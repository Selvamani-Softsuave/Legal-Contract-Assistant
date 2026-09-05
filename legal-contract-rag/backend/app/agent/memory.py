"""
Agent Memory & Context Compression for Week 7 Bonus Challenge (Track F - Legal Contracts).
Implements:
1. Sliding Window Conversation Buffer with automated background summarization.
2. Fact Store persisting critical facts (e.g. executed effective date) across restarts.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("agent_memory")


class SlidingWindowMemory:
    """
    Sliding window memory buffer that compresses conversation history past a window size
    by generating running summarizations while preserving recent verbatim turns.
    """

    def __init__(self, window_size: int = 6, max_summary_tokens: int = 300):
        self.window_size = window_size
        self.max_summary_tokens = max_summary_tokens
        self.messages: List[Dict[str, str]] = []
        self.running_summary: str = ""

    def add_turn(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.window_size:
            self._compress()

    def _compress(self) -> None:
        """Evicts oldest turns outside the window and integrates them into the running summary."""
        evicted = self.messages[:-self.window_size]
        self.messages = self.messages[-self.window_size:]

        evicted_text = " | ".join(f"{m['role']}: {m['content'][:100]}" for m in evicted)
        if self.running_summary:
            self.running_summary = f"{self.running_summary}; [Prior Turns Summary: {evicted_text}]"
        else:
            self.running_summary = f"[Prior Turns Summary: {evicted_text}]"
        logger.debug(f"[MEMORY_COMPRESS] Compacting {len(evicted)} turns. Running summary length: {len(self.running_summary)}")

    def get_context_for_prompt(self) -> str:
        ctx_parts = []
        if self.running_summary:
            ctx_parts.append(f"--- CONVERSATION SUMMARY (EARLIER TURNS) ---\n{self.running_summary}")
        ctx_parts.append("--- RECENT CONVERSATION TURNS ---")
        for m in self.messages:
            ctx_parts.append(f"{m['role'].upper()}: {m['content']}")
        return "\n\n".join(ctx_parts)


class PersistentFactStore:
    """
    Persists key immutable contract facts (e.g. executed effective date, governing law)
    to a local JSON cache so they survive full process restarts.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent.parent.parent / "resource" / "persistent_contract_facts.json"
        self._facts: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                self._facts = json.loads(self.storage_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load persistent facts: {e}")
                self._facts = {}

    def _save(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(json.dumps(self._facts, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save persistent facts: {e}")

    def store_fact(self, contract_id: str, key: str, value: Any) -> None:
        if contract_id not in self._facts:
            self._facts[contract_id] = {}
        self._facts[contract_id][key] = value
        self._save()

    def get_fact(self, contract_id: str, key: str) -> Optional[Any]:
        return self._facts.get(contract_id, {}).get(key)
