import logging
from typing import Optional, Dict, Any
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LangfuseService:
    """
    Enterprise Langfuse integration for LLM observability and tracing.
    Gracefully degrades with no-op operations if credentials are unset or the
    langfuse library is not installed, preventing runtime application failures.
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        enabled: Optional[bool] = None,
        mode: Optional[str] = None,
        client: Optional[Any] = None
    ):
        self.mode = (mode or getattr(settings, "LANGFUSE_MODE", "LOCAL")).upper()
        self.host = host or settings.LANGFUSE_HOST
        
        # Resolve host based on mode if host not explicitly customized
        if self.mode == "CLOUD" and "localhost" in self.host:
            self.host = "https://cloud.langfuse.com"
        elif self.mode == "LOCAL" and "cloud.langfuse.com" in self.host:
            self.host = "http://localhost:3000"

        self.public_key = public_key or settings.LANGFUSE_PUBLIC_KEY
        self.secret_key = secret_key or settings.LANGFUSE_SECRET_KEY
        
        explicit_enabled = enabled if enabled is not None else settings.LANGFUSE_ENABLED
        self.enabled = explicit_enabled and (self.mode != "DISABLED") and bool(self.public_key and self.secret_key)
        self._client = client
        if self._client is None:
            self._init_client()

    def _init_client(self):
        if not self.enabled:
            logger.debug("Langfuse tracing is disabled or credentials not provided. Operating in no-op mode.")
            return

        try:
            from langfuse import Langfuse
            self._client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host
            )
            logger.info(f"Langfuse client initialized successfully for host: {self.host}")
        except ImportError:
            logger.warning("Package 'langfuse' is not installed. Operating in graceful no-op mode.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}. Degrading to no-op mode.")
            self.enabled = False

    @property
    def is_active(self) -> bool:
        return bool(self.enabled and self._client is not None)

    def trace_generation(
        self,
        name: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        output_text: str,
        provider: str = "generic",
        user_id: Optional[str] = "default_user",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None
    ) -> Optional[str]:
        """
        Creates a trace and generation log in Langfuse tracking prompts, output, and execution context.
        Returns the trace ID if successful, or None if in no-op mode.
        """
        if not self.is_active:
            return None

        try:
            trace = self._client.trace(
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
                tags=tags or ["legal-contract-rag", provider]
            )

            trace.generation(
                name=f"{name}-llm-generation",
                model=model,
                input={
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                },
                output=output_text,
                metadata={
                    "provider": provider,
                    **(metadata or {})
                }
            )

            if hasattr(self._client, "flush"):
                self._client.flush()

            return getattr(trace, "id", None)
        except Exception as e:
            logger.warning(f"Failed to record Langfuse generation trace: {e}")
            return None


# Global singleton instance
langfuse_service = LangfuseService()
