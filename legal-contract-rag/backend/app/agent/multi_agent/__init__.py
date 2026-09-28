"""
Multi-Agent Orchestrator Squad & Benchmark Module for Week 10 (Track F - Legal Contracts).
Provides an isolated evaluation testbed to race an Orchestrator + 2 Specialist Workers
against the primary Single Agent architecture.
"""

from .workers import ClauseRetrievalWorker, DefinedTermsWorker
from .orchestrator import LegalOrchestrator
from .handoff_tracker import HandoffTracker, global_handoff_tracker
from .failure_injector import WorkerFailureInjector
from .agent_card import A2AAgentCardManager
from .race_runner import Week10RaceRunner

__all__ = [
    "ClauseRetrievalWorker",
    "DefinedTermsWorker",
    "LegalOrchestrator",
    "HandoffTracker",
    "global_handoff_tracker",
    "WorkerFailureInjector",
    "A2AAgentCardManager",
    "Week10RaceRunner",
]
