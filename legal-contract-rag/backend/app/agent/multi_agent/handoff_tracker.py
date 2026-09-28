"""
Handoff Tracker & Context Re-send Multiplier Engine for Week 10 (Track F - Legal Contracts).
Tracks per-hop prompt and completion tokens, writes to resource/handoffs.log,
computes the Context Re-send Multiplier (multi tokens / single tokens),
and identifies the dominant token sink handoff.
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

HANDOFF_LOG_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        "resource",
        "handoffs.log"
    )
)


class HandoffRecord:
    def __init__(
        self,
        case_id: str,
        hop_number: int,
        handoff_name: str,
        from_entity: str,
        to_entity: str,
        prompt_tokens: int,
        completion_tokens: int,
        context_resend_snippet: str = "",
        is_resend: bool = False
    ):
        self.case_id = case_id
        self.hop_number = hop_number
        self.handoff_name = handoff_name
        self.from_entity = from_entity
        self.to_entity = to_entity
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.context_resend_snippet = context_resend_snippet
        self.is_resend = is_resend
        self.timestamp = datetime.utcnow().isoformat()

    def to_log_line(self) -> str:
        return (
            f"[{self.timestamp}] [{self.case_id}] Hop {self.hop_number}: {self.handoff_name} | "
            f"From: {self.from_entity} -> To: {self.to_entity} | "
            f"Prompt: {self.prompt_tokens} toks | Completion: {self.completion_tokens} toks | "
            f"Total: {self.total_tokens} toks"
            + (f" | [RESEND: {self.context_resend_snippet[:80]}...]" if self.is_resend else "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "hop_number": self.hop_number,
            "handoff_name": self.handoff_name,
            "from_entity": self.from_entity,
            "to_entity": self.to_entity,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "is_resend": self.is_resend,
            "context_resend_snippet": self.context_resend_snippet,
            "timestamp": self.timestamp
        }


class HandoffTracker:
    def __init__(self, log_path: str = HANDOFF_LOG_PATH):
        self.log_path = log_path
        self.records: List[HandoffRecord] = []

    def record_handoff(
        self,
        case_id: str,
        hop_number: int,
        handoff_name: str,
        from_entity: str,
        to_entity: str,
        prompt_tokens: int,
        completion_tokens: int,
        context_resend_snippet: str = "",
        is_resend: bool = False
    ) -> HandoffRecord:
        record = HandoffRecord(
            case_id=case_id,
            hop_number=hop_number,
            handoff_name=handoff_name,
            from_entity=from_entity,
            to_entity=to_entity,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            context_resend_snippet=context_resend_snippet,
            is_resend=is_resend
        )
        self.records.append(record)
        self._append_to_file(record)
        return record

    def clear(self):
        self.records = []
        if os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(f"# Week 10 Multi-Agent Handoff Log — Initialized {datetime.utcnow().isoformat()}\n\n")

    def _append_to_file(self, record: HandoffRecord):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(record.to_log_line() + "\n")

    def compute_summary(self, single_agent_total_tokens: int) -> Dict[str, Any]:
        """
        Computes the Context Re-send Multiplier and attributes the dominant token share.
        """
        total_multi_tokens = sum(r.total_tokens for r in self.records)
        if single_agent_total_tokens <= 0:
            multiplier = 1.0
        else:
            multiplier = round(total_multi_tokens / single_agent_total_tokens, 1)

        # Aggregate tokens by handoff_name across the run
        breakdown_by_handoff: Dict[str, int] = {}
        for r in self.records:
            breakdown_by_handoff[r.handoff_name] = breakdown_by_handoff.get(r.handoff_name, 0) + r.total_tokens

        # Find dominant handoff
        dominant_handoff = "None"
        dominant_tokens = 0
        dominant_percentage = 0.0

        if total_multi_tokens > 0:
            for h_name, toks in breakdown_by_handoff.items():
                if toks > dominant_tokens:
                    dominant_tokens = toks
                    dominant_handoff = h_name
            dominant_percentage = round((dominant_tokens / total_multi_tokens) * 100.0, 1)

        # Multiplier line formatted exactly per rubric
        multiplier_line = (
            f"Multi/Single Token Multiplier: {multiplier}x "
            f"(Dominant Hand-off: {dominant_handoff}, {dominant_percentage}% of all tokens)"
        )

        return {
            "total_multi_tokens": total_multi_tokens,
            "single_agent_total_tokens": single_agent_total_tokens,
            "multiplier": multiplier,
            "dominant_handoff": dominant_handoff,
            "dominant_tokens": dominant_tokens,
            "dominant_percentage": dominant_percentage,
            "multiplier_line": multiplier_line,
            "breakdown_by_handoff": breakdown_by_handoff,
            "total_hops": len(self.records)
        }


# Global singleton tracker instance
global_handoff_tracker = HandoffTracker()
