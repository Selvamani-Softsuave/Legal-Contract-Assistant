from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Optional, Dict, Any

from backend.app.schemas.telemetry import (
    RequestTraceDTO,
    LogFilterDTO,
    SupportDrillResultDTO,
    CanaryConfigDTO
)
from backend.app.observability.store import global_log_store

router = APIRouter()

# In-memory canary configuration state
_canary_config = CanaryConfigDTO(
    active_prompt_version="v1.0.0",
    canary_prompt_version="v1.1.0",
    canary_traffic_percentage=5.0,
    max_citation_error_threshold_pct=0.0,
    max_p95_latency_ms=2500.0,
    auto_rollback_enabled=True,
    status="CANARY_ACTIVE"
)


@router.get("/logs", response_model=List[RequestTraceDTO])
def get_production_logs(
    day_of_week: Optional[str] = Query(None, description="Filter by day of week (e.g. Thursday)"),
    prompt_version: Optional[str] = Query(None, description="Filter by prompt version (v1.0.0, v1.1.0)"),
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    query_keyword: Optional[str] = Query(None, description="Search keyword in user query"),
    answer_keyword: Optional[str] = Query(None, description="Search keyword in generated answer"),
    cost_min_usd: Optional[float] = Query(None, description="Filter for cost outliers above threshold"),
    cited_clause: Optional[str] = Query(None, description="Filter by cited clause reference"),
    amendment_status: Optional[str] = Query(None, description="Filter by amendment status (CURRENT, SUPERSEDED)"),
    has_citation_conflict: Optional[bool] = Query(None, description="Filter by citation conflict flag")
):
    """Query and multi-dimensionally slice production request traces."""
    filters = LogFilterDTO(
        day_of_week=day_of_week,
        prompt_version=prompt_version,
        user_id=user_id,
        query_keyword=query_keyword,
        answer_keyword=answer_keyword,
        cost_min_usd=cost_min_usd,
        cited_clause=cited_clause,
        amendment_status=amendment_status,
        has_citation_conflict=has_citation_conflict
    )
    return global_log_store.slice_logs(filters)


@router.get("/traces/{trace_id}", response_model=RequestTraceDTO)
def get_trace_by_id(trace_id: str):
    """Retrieve full unredacted span telemetry, token usage, and cost for a single trace."""
    trace = global_log_store.get_trace_by_id(trace_id)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trace '{trace_id}' not found.")
    return trace


@router.post("/drill", response_model=SupportDrillResultDTO)
def run_support_drill(
    complaint: str = Query(
        "a lawyer said it cited the wrong clause on termination, maybe Thursday",
        description="Vague production complaint string"
    )
):
    """Execute the Track F support drill and return the discovered trace, time-to-find, and root cause."""
    return global_log_store.execute_support_drill(complaint)


@router.get("/canary-config", response_model=CanaryConfigDTO)
def get_canary_config():
    """Get active canary traffic and rollback parameters."""
    return _canary_config


@router.post("/canary-config", response_model=CanaryConfigDTO)
def update_canary_config(config: CanaryConfigDTO):
    """Update canary traffic allocation or trigger instant rollback."""
    global _canary_config
    _canary_config = config
    return _canary_config


@router.get("/cost-summary", response_model=Dict[str, Any])
def get_cost_summary():
    """Get aggregate cost-by-stage and 10x scalability projection metrics."""
    traces = global_log_store.get_all_traces()
    if not traces:
        return {"message": "No traces available"}

    total_cost = sum(t.cost_by_stage.total_cost_usd for t in traces)
    avg_cost = total_cost / len(traces)
    retrieval_cost = sum(t.cost_by_stage.retrieval_cost_usd for t in traces)
    gen_cost = sum(t.cost_by_stage.generation_cost_usd for t in traces)
    tools_cost = sum(t.cost_by_stage.tools_cost_usd for t in traces)

    return {
        "total_traces_analyzed": len(traces),
        "total_cost_usd": round(total_cost, 6),
        "avg_cost_per_query_usd": round(avg_cost, 8),
        "stage_breakdown": {
            "retrieval_cost_usd": round(retrieval_cost, 6),
            "retrieval_pct": round((retrieval_cost / total_cost) * 100, 2) if total_cost > 0 else 0,
            "generation_cost_usd": round(gen_cost, 6),
            "generation_pct": round((gen_cost / total_cost) * 100, 2) if total_cost > 0 else 0,
            "tools_cost_usd": round(tools_cost, 6),
            "tools_pct": round((tools_cost / total_cost) * 100, 2) if total_cost > 0 else 0,
        },
        "tenx_scale_projections": {
            "baseline_rpm": 30,
            "tenx_rpm": 300,
            "baseline_tpm": 45000,
            "tenx_tpm": 450000,
            "first_bottleneck": "LLM Provider TPM Rate Limit (Tier 2 quota capped at 250,000 TPM)",
            "time_to_rate_limit_seconds": 42.6,
            "cost_at_tenx_hourly_usd": round(avg_cost * 300 * 60, 4)
        }
    }
