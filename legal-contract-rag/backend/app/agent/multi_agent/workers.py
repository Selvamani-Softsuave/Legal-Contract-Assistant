"""
Specialist Workers for Week 10 Multi-Agent Orchestrator Squad (Track F - Legal Contracts).
Per Week 10 rubric constraints:
1. Clause Retrieval Worker: Narrow prompt, strictly clause tools (zero definition tools).
2. Defined-Terms Worker: Narrow prompt, strictly definition/metadata tools.
   Supports simulated HTTP 500 worker failure injection.
"""

import time
import logging
from typing import Dict, Any, Optional
from backend.app.agent.enums import ContractVersionEnum
from backend.app.agent.tools import get_clause, get_definitions, get_effective_date_and_metadata

logger = logging.getLogger("multi_agent_workers")


class ClauseRetrievalWorker:
    """
    Specialist Worker 1: Clause Retrieval.
    Has a tightly constrained role and narrow toolset (get_clause only).
    Does NOT possess definition resolution tools.
    """

    WORKER_NAME = "ClauseRetrievalWorker"
    SYSTEM_ROLE = (
        "You are a narrow Legal Clause Specialist. Your only job is to retrieve exact, "
        "binding clause text from contracts and cite the specific Article/Section. "
        "You have no authority or tools to interpret defined terms."
    )

    def __init__(self):
        self.total_invocations = 0

    async def execute(
        self,
        contract_id: str = "CNT-MAIN",
        clause_type: str = "TERMINATION",
        version: str = "FINAL_EXECUTED"
    ) -> Dict[str, Any]:
        """
        Executes clause retrieval and calculates token usage for prompt & completion.
        """
        t0 = time.perf_counter()
        self.total_invocations += 1

        # Synthesize worker prompt
        worker_prompt = (
            f"{self.SYSTEM_ROLE}\n\nTask: Retrieve clause '{clause_type}' "
            f"from contract '{contract_id}' [Version: {version}]."
        )
        prompt_tokens = int(len(worker_prompt.split()) * 1.3) + 120

        # Resolve version enum
        if isinstance(version, ContractVersionEnum):
            v_enum = version
        elif version in ContractVersionEnum.__members__:
            v_enum = ContractVersionEnum[version]
        else:
            v_enum = ContractVersionEnum.FINAL_EXECUTED

        # Execute deterministic tool
        clause_text = get_clause(
            clause_type=clause_type,
            contract_id=contract_id,
            contract_version=v_enum
        )

        success = "not found" not in clause_text.lower()
        article_cited = f"Article for {clause_type}"
        if "ARTICLE 10" in clause_text:
            article_cited = "Article 10 (Termination)"
        elif "ARTICLE 11" in clause_text:
            article_cited = "Article 11 (Notices)"
        elif "ARTICLE 14" in clause_text:
            article_cited = "Article 14 (Governing Law)"
        elif "ARTICLE 8" in clause_text:
            article_cited = "Article 8 (Limitation of Liability)"

        completion_tokens = int(len(clause_text.split()) * 1.3) + 40
        elapsed_s = time.perf_counter() - t0

        return {
            "worker": self.WORKER_NAME,
            "status": "SUCCESS" if success else "FAILED",
            "clause_type": clause_type,
            "clause_text": clause_text,
            "article_cited": article_cited,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_seconds": elapsed_s,
            "error": None if success else clause_text
        }


class DefinedTermsWorker:
    """
    Specialist Worker 2: Defined Terms & Schedules.
    Has a tightly constrained role and narrow toolset (get_definitions, get_effective_date_and_metadata).
    Does NOT possess general clause retrieval tools.
    Supports injecting an HTTP 500 failure for rubric compliance.
    """

    WORKER_NAME = "DefinedTermsWorker"
    SYSTEM_ROLE = (
        "You are a narrow Defined Terms & Schedule Specialist. Your only job is to resolve "
        "capitalized defined terms, cure periods, and schedule dependencies under contracts. "
        "You do not retrieve entire operational clauses."
    )

    def __init__(self, inject_failure_500: bool = False):
        self.inject_failure_500 = inject_failure_500
        self.total_invocations = 0

    async def execute(
        self,
        contract_id: str = "CNT-MAIN",
        term: str = "CURE PERIOD",
        version: str = "FINAL_EXECUTED"
    ) -> Dict[str, Any]:
        """
        Executes defined-term lookup or simulates an HTTP 500 worker failure.
        """
        t0 = time.perf_counter()
        self.total_invocations += 1

        # Synthesize worker prompt
        worker_prompt = (
            f"{self.SYSTEM_ROLE}\n\nTask: Resolve defined term '{term}' in contract '{contract_id}' [Version: {version}]."
        )
        prompt_tokens = int(len(worker_prompt.split()) * 1.3) + 110

        # Check for simulated HTTP 500 failure injection
        if self.inject_failure_500:
            elapsed_s = time.perf_counter() - t0
            return {
                "worker": self.WORKER_NAME,
                "status": "HTTP_500_INTERNAL_SERVER_ERROR",
                "term": term,
                "definition": None,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": 15,
                "total_tokens": prompt_tokens + 15,
                "latency_seconds": elapsed_s,
                "error": "HTTP 500: Remote Worker Unavailable — Connection refused by DefinedTermsWorker microservice."
            }

        # Resolve version enum
        if isinstance(version, ContractVersionEnum):
            v_enum = version
        elif version in ContractVersionEnum.__members__:
            v_enum = ContractVersionEnum[version]
        else:
            v_enum = ContractVersionEnum.FINAL_EXECUTED

        # Normal execution
        def_text = get_definitions(
            term=term,
            contract_version=v_enum,
            contract_id=contract_id
        )

        success = "unstated" not in def_text.lower()
        completion_tokens = int(len(def_text.split()) * 1.3) + 35
        elapsed_s = time.perf_counter() - t0

        return {
            "worker": self.WORKER_NAME,
            "status": "SUCCESS" if success else "FAILED",
            "term": term,
            "definition": def_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_seconds": elapsed_s,
            "error": None if success else def_text
        }
