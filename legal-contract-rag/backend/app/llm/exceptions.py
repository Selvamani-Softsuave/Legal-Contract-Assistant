from typing import Optional, Dict, Any


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""
    def __init__(self, message: str, provider: str = "unknown", raw_error: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.raw_error = raw_error


class LLMAuthenticationError(LLMProviderError):
    """Raised when API key or authentication fails."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when provider rate limit / quota is exceeded."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when request to LLM times out."""
    pass


class LLMUnavailableError(LLMProviderError):
    """Raised when provider service is unreachable or returns 5xx."""
    pass


class LLMInvalidResponseError(LLMProviderError):
    """Raised when response structure is corrupted or unparseable."""
    pass
