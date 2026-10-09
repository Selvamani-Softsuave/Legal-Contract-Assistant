from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SpanDTO(BaseModel):
    span_id: str
    span_name: str  # e.g., "embedding", "hybrid_retrieval", "prompt_assembly", "llm_generation", "citation_validation"
    stage: str      # "retrieval", "generation", "tools"
    start_time_iso: str
    end_time_iso: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: str = "SUCCESS"  # "SUCCESS", "FAILED"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostBreakdownDTO(BaseModel):
    retrieval_cost_usd: float
    generation_cost_usd: float
    tools_cost_usd: float
    total_cost_usd: float
    retrieval_pct: float
    generation_pct: float
    tools_pct: float


class RequestTraceDTO(BaseModel):
    trace_id: str
    request_id: str
    timestamp_iso: str
    day_of_week: str  # "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
    user_id: str
    contract_id: Optional[str] = None
    prompt_version: str  # "v1.0.0", "v1.1.0"
    input_query: str
    output_answer: str
    retrieved_context_ids: List[str] = Field(default_factory=list)
    cited_clauses: List[str] = Field(default_factory=list)  # e.g. ["Section 12.4", "Amendment No. 2"]
    amendment_status: str = "CURRENT"  # "CURRENT", "SUPERSEDED", "UNKNOWN"
    has_citation_conflict: bool = False
    spans: List[SpanDTO] = Field(default_factory=list)
    total_latency_ms: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    cost_by_stage: CostBreakdownDTO
    status: str = "SUCCESS"  # "SUCCESS", "FAILURE", "ERROR"
    error_type: Optional[str] = None
    canary_routed: bool = False


class LogFilterDTO(BaseModel):
    start_time_iso: Optional[str] = None
    end_time_iso: Optional[str] = None
    day_of_week: Optional[str] = None
    user_id: Optional[str] = None
    prompt_version: Optional[str] = None
    query_keyword: Optional[str] = None
    answer_keyword: Optional[str] = None
    cost_min_usd: Optional[float] = None
    cited_clause: Optional[str] = None
    amendment_status: Optional[str] = None
    has_citation_conflict: Optional[bool] = None


class SupportDrillResultDTO(BaseModel):
    drill_name: str
    complaint_text: str
    slice_used: str
    time_to_find_seconds: float
    time_to_find_formatted: str  # "mm:ss"
    total_traces_scanned: int
    traces_matching_slice: int
    found_trace_id: str
    root_cause: str
    missing_log_field_identified: Optional[str] = None
    bonus_time_to_find_seconds: Optional[float] = None
    bonus_time_to_find_formatted: Optional[str] = None
    bonus_field_used: Optional[str] = None


class CanaryConfigDTO(BaseModel):
    active_prompt_version: str = "v1.0.0"
    canary_prompt_version: str = "v1.1.0"
    canary_traffic_percentage: float = 5.0  # 5% canary traffic
    max_citation_error_threshold_pct: float = 0.0
    max_p95_latency_ms: float = 2500.0
    auto_rollback_enabled: bool = True
    status: str = "CANARY_ACTIVE"  # "CANARY_ACTIVE", "PROMOTED", "ROLLED_BACK"
