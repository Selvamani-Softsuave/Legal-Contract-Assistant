import re
from typing import Optional


class ResponseValidator:
    """
    Validates and normalizes LLM outputs safely without aggressive regex that could
    accidentally truncate valid legal clauses or text.
    """

    DEFAULT_FALLBACK: str = "I don't know based on the provided documents."

    @classmethod
    def validate_and_normalize(cls, raw_content: Optional[str]) -> str:
        if not raw_content or not raw_content.strip():
            return cls.DEFAULT_FALLBACK

        cleaned = raw_content.strip()

        # Handle think/thought blocks
        cleaned = re.sub(r"<(think|thought)>.*?</\1>", "", cleaned, flags=re.DOTALL | re.IGNORECASE).strip()

        # Handle models wrapping response with markdown code fences
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                cleaned = "\n".join(lines[1:-1]).strip()

        # If answer explicitly has "Answer:" prefix after thinking text
        if "\nAnswer:" in cleaned or cleaned.startswith("Answer:"):
            parts = cleaned.split("Answer:")
            candidate = parts[-1].strip()
            if candidate:
                cleaned = candidate

        # Handle reasoning models outputting bulleted thought traces / draft options
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        bullet_lines = [l for l in lines if l.startswith("*") or l.startswith("-")]
        if len(bullet_lines) >= 2 or any("option" in l.lower() or "draft" in l.lower() for l in bullet_lines):
            # 1. Search for *Option ...:* or *Draft ...:*
            drafts = re.findall(r'(?:Option|Draft)\s*\d+[^:*]*:\*?\s*([^\n]+)', cleaned, flags=re.IGNORECASE)
            if drafts:
                complete_drafts = [d.strip(' "\'') for d in drafts if d.strip().endswith(('.', '!', '?', '"', "'")) and len(d.strip()) > 35]
                if complete_drafts:
                    cleaned = complete_drafts[-1]
                elif len(drafts[0].strip(' "\'')) > 30:
                    cleaned = drafts[0].strip(' "\'')

            # 2. Check for trailing non-bullet paragraph at the very end
            if cleaned == raw_content.strip() or any(cleaned.startswith(b) for b in ["*", "-"]):
                trailing = []
                for l in reversed(lines):
                    if not (l.startswith("*") or l.startswith("-")):
                        trailing.insert(0, l)
                    else:
                        break
                if trailing:
                    cand = " ".join(trailing).strip(' "\'')
                    if len(cand) > 30 and not any(cand.lower().startswith(w) for w in ["user", "tone", "question", "scenario", "constraint"]):
                        cleaned = cand

            # 3. Check for quoted sentences in the text (e.g. "Hello! I am...")
            if cleaned == raw_content.strip() or any(cleaned.startswith(b) for b in ["*", "-"]):
                non_meta_lines = [
                    l for l in cleaned.splitlines()
                    if not any(w in l.lower() for w in ["user input", "user question", "user says", "input:", "scenario:", "role:", "constraints:", "question:"])
                ]
                non_meta_text = "\n".join(non_meta_lines)
                quotes = re.findall(r'"([^"\n]{25,})"', non_meta_text)
                meta_words = ["warm", "concise", "role", "constraint", "tailor", "guideline", "sentence", "draft", "option"]
                valid_quotes = [q for q in quotes if not any(w in q.lower() for w in meta_words)]
                if valid_quotes:
                    cleaned = valid_quotes[-1].strip(' "\'')

        cleaned = cleaned.strip(' "\'')

        # Handle duplicate repeating output (common in reasoning models like Gemma)
        half = len(cleaned) // 2
        if half > 20 and cleaned[:half] == cleaned[half:]:
            cleaned = cleaned[:half].strip()
        elif '"' in cleaned:
            parts = [p.strip() for p in cleaned.split('"') if p.strip()]
            if parts and len(parts[0]) > 25:
                cleaned = parts[0]

        # Clean trailing self-evaluation bullets if present (e.g. * Grounded? Yes.)
        cleaned = re.sub(r"(\n\s*\*[^\n]+\?\s*(Yes|No)\.?)+\s*$", "", cleaned, flags=re.IGNORECASE).strip()

        # Check for model refusals / insufficient context signals
        refusal_patterns = [
            "i do not have enough information",
            "not mentioned in the context",
            "not provided in the context",
            "provided context does not contain",
            "cannot find any information",
            "no information is provided",
            "the provided documents do not mention",
        ]
        lower_cleaned = cleaned.lower()
        if any(p in lower_cleaned for p in refusal_patterns) and len(cleaned) < 150:
            return cls.DEFAULT_FALLBACK

        return cleaned if cleaned else cls.DEFAULT_FALLBACK
