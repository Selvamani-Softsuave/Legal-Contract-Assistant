from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class LLMRequest(BaseModel):
    user_prompt: str
    system_prompt: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    model: Optional[str] = None
    stop_sequences: Optional[List[str]] = None
    timeout: Optional[float] = None
    response_format: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[LLMUsage] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None
