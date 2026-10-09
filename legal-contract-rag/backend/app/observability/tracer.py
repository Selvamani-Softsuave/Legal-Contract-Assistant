import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from backend.app.schemas.telemetry import SpanDTO, CostBreakdownDTO, RequestTraceDTO

# Standard Pricing per 1 Million tokens (USD)
MODEL_PRICING = {
    # Text embeddings: $0.02 / 1M tokens
    "embedding": {"input_per_1m": 0.020, "output_per_1m": 0.000},
    # Fast / Tier-2 Frontier (e.g. gpt-4o-mini / gemini-1.5-flash): $0.15 input / $0.60 output
    "gpt-4o-mini": {"input_per_1m": 0.150, "output_per_1m": 0.600, "cached_input_per_1m": 0.075},
    "gemini-1.5-flash": {"input_per_1m": 0.150, "output_per_1m": 0.600, "cached_input_per_1m": 0.075},
    "default_llm": {"input_per_1m": 0.150, "output_per_1m": 0.600, "cached_input_per_1m": 0.075},
    # Deterministic / Validation tools: fixed compute estimate
    "tools_compute": {"cost_per_invocation": 0.000007}
}


class ProductionTracer:
    """
    Production-grade request tracer tracking per-span latency, tokens,
    and stage-based cost attribution (retrieval vs. generation vs. tools).
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: str = "default_user",
        prompt_version: str = "v1.0.0",
        contract_id: Optional[str] = None
    ):
        self.trace_id = f"TRACE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.prompt_version = prompt_version
        self.contract_id = contract_id
        self.spans: List[SpanDTO] = []
        self.start_time = time.time()
        self.start_time_iso = datetime.now(timezone.utc).isoformat()
        self.retrieved_context_ids: List[str] = []
        self.cited_clauses: List[str] = []
        self.amendment_status: str = "CURRENT"
        self.has_citation_conflict: bool = False
        self.canary_routed: bool = False

    @contextmanager
    def span(self, span_name: str, stage: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager to measure span execution time, tokens, and cost."""
        span_id = f"span-{uuid.uuid4().hex[:6]}"
        t0 = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()
        span_data = {
            "span_id": span_id,
            "span_name": span_name,
            "stage": stage,
            "start_time_iso": start_iso,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "status": "SUCCESS",
            "metadata": metadata or {}
        }

        try:
            yield span_data
        except Exception as exc:
            span_data["status"] = "FAILED"
            span_data["metadata"]["error"] = str(exc)
            raise exc
        finally:
            t1 = time.time()
            latency_ms = max(0.01, round((t1 - t0) * 1000, 2))
            span_data["end_time_iso"] = datetime.now(timezone.utc).isoformat()
            span_data["latency_ms"] = latency_ms

            # Compute Span Cost
            inp_tok = span_data.get("input_tokens", 0)
            out_tok = span_data.get("output_tokens", 0)
            cache_tok = span_data.get("cached_tokens", 0)
            tot_tok = inp_tok + out_tok

            cost = 0.0
            if stage == "retrieval":
                pricing = MODEL_PRICING["embedding"]
                cost = (inp_tok / 1_000_000.0) * pricing["input_per_1m"]
            elif stage == "generation":
                pricing = MODEL_PRICING["default_llm"]
                cost = (
                    (inp_tok / 1_000_000.0) * pricing["input_per_1m"] +
                    (out_tok / 1_000_000.0) * pricing["output_per_1m"] +
                    (cache_tok / 1_000_000.0) * pricing.get("cached_input_per_1m", 0.0)
                )
            elif stage == "tools":
                cost = MODEL_PRICING["tools_compute"]["cost_per_invocation"]

            span_dto = SpanDTO(
                span_id=span_id,
                span_name=span_name,
                stage=stage,
                start_time_iso=start_iso,
                end_time_iso=span_data["end_time_iso"],
                latency_ms=latency_ms,
                input_tokens=inp_tok,
                output_tokens=out_tok,
                cached_tokens=cache_tok,
                total_tokens=tot_tok,
                cost_usd=round(cost, 8),
                status=span_data["status"],
                metadata=span_data["metadata"]
            )
            self.spans.append(span_dto)

    def record_context_ids(self, context_ids: List[str]):
        self.retrieved_context_ids = context_ids

    def record_clause_citations(self, cited_clauses: List[str], amendment_status: str = "CURRENT", conflict: bool = False):
        self.cited_clauses = cited_clauses
        self.amendment_status = amendment_status
        self.has_citation_conflict = conflict

    def finalize_trace(
        self,
        input_query: str,
        output_answer: str,
        status: str = "SUCCESS",
        error_type: Optional[str] = None
    ) -> RequestTraceDTO:
        """Finalize and assemble the complete RequestTraceDTO with stage cost breakdown."""
        total_latency_ms = max(0.01, round((time.time() - self.start_time) * 1000, 2))

        retrieval_cost = sum(s.cost_usd for s in self.spans if s.stage == "retrieval")
        generation_cost = sum(s.cost_usd for s in self.spans if s.stage == "generation")
        tools_cost = sum(s.cost_usd for s in self.spans if s.stage == "tools")
        total_cost = retrieval_cost + generation_cost + tools_cost

        total_prompt_tokens = sum(s.input_tokens for s in self.spans)
        total_completion_tokens = sum(s.output_tokens for s in self.spans)
        total_tokens = total_prompt_tokens + total_completion_tokens

        retrieval_pct = round((retrieval_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        generation_pct = round((generation_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        tools_pct = round((tools_cost / total_cost * 100) if total_cost > 0 else 0, 2)

        cost_breakdown = CostBreakdownDTO(
            retrieval_cost_usd=round(retrieval_cost, 8),
            generation_cost_usd=round(generation_cost, 8),
            tools_cost_usd=round(tools_cost, 8),
            total_cost_usd=round(total_cost, 8),
            retrieval_pct=retrieval_pct,
            generation_pct=generation_pct,
            tools_pct=tools_pct
        )

        dt = datetime.fromisoformat(self.start_time_iso)
        day_name = dt.strftime("%A")

        return RequestTraceDTO(
            trace_id=self.trace_id,
            request_id=self.request_id,
            timestamp_iso=self.start_time_iso,
            day_of_week=day_name,
            user_id=self.user_id,
            contract_id=self.contract_id,
            prompt_version=self.prompt_version,
            input_query=input_query,
            output_answer=output_answer,
            retrieved_context_ids=self.retrieved_context_ids,
            cited_clauses=self.cited_clauses,
            amendment_status=self.amendment_status,
            has_citation_conflict=self.has_citation_conflict,
            spans=self.spans,
            total_latency_ms=total_latency_ms,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            cost_by_stage=cost_breakdown,
            status=status,
            error_type=error_type,
            canary_routed=self.canary_routed
        )
