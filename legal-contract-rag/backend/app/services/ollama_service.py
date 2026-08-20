import httpx
import logging
import os

logger = logging.getLogger(__name__)

# Known provider base URLs — just shortcuts; users can always override with LLM_BASE_URL
KNOWN_LLM_URLS = {
    "OPENROUTER": "https://openrouter.ai/api/v1",
    "OPENAI":     "https://api.openai.com/v1",
    "GEMINI":     "https://generativelanguage.googleapis.com/v1beta/openai",
    "GROQ":       "https://api.groq.com/openai/v1",
    "DEEPSEEK":   "https://api.deepseek.com/v1",
    "OLLAMA":     os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
}

KNOWN_LLM_MODELS = {
    "OPENROUTER": "meta-llama/llama-3.1-8b-instruct:free",
    "OPENAI":     "gpt-4o-mini",
    "GEMINI":     "gemini-1.5-flash",
    "GROQ":       "llama-3.1-8b-instant",
    "DEEPSEEK":   "deepseek-chat",
    "OLLAMA":     "llama3.2",
}


def _resolve_llm_config() -> tuple[str, str, str | None, bool]:
    """
    Returns (base_url, model, api_key, is_ollama_native)
    Priority: explicit env vars > known-provider shortcut > local Ollama default
    """
    provider = os.getenv("AI_PROVIDER", "OLLAMA").upper()
    base_url  = os.getenv("LLM_BASE_URL") or KNOWN_LLM_URLS.get(provider, KNOWN_LLM_URLS["OLLAMA"])
    model     = os.getenv("LLM_MODEL")    or KNOWN_LLM_MODELS.get(provider, "llama3.2")
    api_key   = os.getenv("LLM_API_KEY")  or os.getenv("AI_API_KEY")

    # Native Ollama uses a different API format — detect by provider name or URL pattern
    is_ollama_native = provider == "OLLAMA" and "/v1" not in base_url

    return base_url.rstrip("/"), model, api_key, is_ollama_native


class OllamaService:
    _cached_gemini_model = None  # (version, model_name)

    def __init__(self):
        self.timeout = float(os.getenv("LLM_TIMEOUT", os.getenv("OLLAMA_TIMEOUT", "120.0")))

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        base_url, model, api_key, is_ollama_native = _resolve_llm_config()
        logger.info(f"LLM request → {base_url} | model={model}")

        if is_ollama_native:
            url = f"{base_url}/api/generate"
            payload = {"model": model, "prompt": f"{system_prompt}\n\n{user_prompt}", "stream": False}
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    return resp.json().get("response", "")
            except Exception as e:
                logger.error(f"Ollama native error: {e}")
                raise Exception(f"Ollama generation failed: {e}")

        provider = os.getenv("AI_PROVIDER", "OLLAMA").upper()
        if provider == "GEMINI":
            def _build_payload(m_name: str) -> dict:
                if "gemma" in m_name.lower():
                    return {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                            }
                        ],
                        "generationConfig": {"temperature": 0.1}
                    }
                return {
                    "system_instruction": {
                        "parts": [{"text": system_prompt}]
                    },
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": user_prompt}]
                        }
                    ],
                    "generationConfig": {"temperature": 0.1}
                }

            def _get_text(resp_data: dict) -> str:
                candidates_list = resp_data.get("candidates", [])
                if candidates_list:
                    parts = candidates_list[0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts if "text" in p).strip()
                return ""

            # 1. Fast Path: Use cached working model
            if OllamaService._cached_gemini_model:
                version, m = OllamaService._cached_gemini_model
                url = f"https://generativelanguage.googleapis.com/{version}/models/{m}:generateContent?key={api_key}"
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.post(url, json=_build_payload(m))
                        if resp.status_code == 200:
                            extracted = _get_text(resp.json())
                            if extracted:
                                return extracted
                except Exception:
                    OllamaService._cached_gemini_model = None

            # 2. Targeted Candidate List (starts with configured model)
            clean_model = model.replace("models/", "") if model else "gemma-4-26b-a4b-it"
            candidates = [clean_model]
            for fb in ["gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash"]:
                if fb not in candidates:
                    candidates.append(fb)

            last_err = None
            for m in candidates:
                for version in ["v1beta", "v1"]:
                    url = f"https://generativelanguage.googleapis.com/{version}/models/{m}:generateContent?key={api_key}"
                    try:
                        async with httpx.AsyncClient(timeout=self.timeout) as client:
                            resp = await client.post(url, json=_build_payload(m))
                            if resp.status_code == 200:
                                extracted = _get_text(resp.json())
                                if extracted:
                                    OllamaService._cached_gemini_model = (version, m)
                                    logger.info(f"Connected to model: {m} (cached)")
                                    return extracted
                            else:
                                last_err = f"Google ({version}/{m}) error {resp.status_code}: {resp.text}"
                    except Exception as e:
                        last_err = str(e)

            # 3. Dynamic Discovery: Query ListModels filtering out audio/TTS/embeddings
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    list_resp = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
                    if list_resp.status_code == 200:
                        models_data = list_resp.json().get("models", [])
                        valid_models = [
                            m["name"].replace("models/", "")
                            for m in models_data
                            if "generateContent" in m.get("supportedGenerationMethods", [])
                            and not any(x in m["name"].lower() for x in ["tts", "audio", "embed", "imagen"])
                        ]
                        logger.info(f"Available text models: {valid_models}")
                        for m in valid_models:
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
                            resp = await client.post(url, json=_build_payload(m))
                            if resp.status_code == 200:
                                extracted = _get_text(resp.json())
                                if extracted:
                                    OllamaService._cached_gemini_model = ("v1beta", m)
                                    logger.info(f"Discovered working model: {m} (cached)")
                                    return extracted
            except Exception as list_e:
                logger.error(f"Failed to query ListModels: {list_e}")

            logger.error(f"Generation failed across candidates: {last_err}")
            raise Exception(f"Generation failed: {last_err}")

        # Universal OpenAI-compatible path
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API error ({base_url}): {e}")
            raise Exception(f"LLM generation failed: {e}")

    async def health_check(self) -> dict:
        base_url, model, _, is_ollama_native = _resolve_llm_config()
        if is_ollama_native:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{base_url}/api/tags")
                    status = "healthy" if resp.status_code == 200 else "unhealthy"
                    return {"status": status, "service": "ollama", "model": model}
            except Exception:
                return {"status": "unhealthy", "service": "ollama", "model": model}
        return {"status": "configured", "service": base_url, "model": model}

