"""
A2A (Agent-to-Agent) Protocol & AgentCard Module for Week 10 Practical (Bonus Challenge).
Defines:
1. The formal AgentCard advertised by the Legal Orchestrator (skills, I/O modes, auth).
2. The A2A Task Lifecycle state machine (submitted, working, input-required, failed, completed).
3. Lifecycle mapping of the failed worker case and the 2-line A2A vs REST value proposition.
4. Generates resource/agent_card.json.
"""

import os
import json
from typing import Dict, Any

AGENT_CARD_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        "resource",
        "agent_card.json"
    )
)


class A2AAgentCardManager:
    """
    Manages A2A AgentCard discovery and task lifecycle evaluation.
    """

    AGENT_CARD: Dict[str, Any] = {
        "name": "LegalContractOrchestrator",
        "version": "1.0.0",
        "description": "Enterprise Legal Orchestrator coordinating clause extraction and defined-terms resolution across contract repositories.",
        "provider": {
            "organization": "Soft Suave AI Engineering League",
            "contact": "legal-ai-squad@softsuave.com"
        },
        "capabilities": {
            "skills": [
                {
                    "name": "extract_contract_clauses",
                    "description": "Dispatches clause retrieval to ClauseRetrievalWorker to locate binding operational clauses (Termination, Notice, Liability, Governing Law).",
                    "input_parameters": {
                        "contract_id": "string",
                        "clause_type": "string",
                        "version": "string (optional: ORIGINAL, AMENDMENT_V1)"
                    }
                },
                {
                    "name": "resolve_defined_terms",
                    "description": "Delegates term definitions, schedules, and cross-contract dependencies to DefinedTermsWorker.",
                    "input_parameters": {
                        "contract_id": "string",
                        "term": "string",
                        "version": "string"
                    }
                },
                {
                    "name": "synthesize_legal_qa",
                    "description": "Synthesizes extracted clauses and verified definitions into grounded, citation-backed legal counsel answers.",
                    "input_parameters": {
                        "question": "string",
                        "clauses": "object",
                        "definitions": "object"
                    }
                }
            ],
            "input_modes": ["application/json", "text/plain"],
            "output_modes": ["application/json", "text/markdown"],
            "protocols_supported": ["A2A-v1", "JSON-RPC-2.0-MCP", "REST-v1"]
        },
        "authentication": {
            "type": "BearerToken",
            "issuer": "Enterprise-Auth0-RBAC",
            "required_scopes": ["legal:contract:read", "legal:orchestrate:execute"]
        },
        "endpoints": {
            "task_submit": "/api/v1/a2a/tasks",
            "task_status": "/api/v1/a2a/tasks/{task_id}",
            "task_input": "/api/v1/a2a/tasks/{task_id}/input",
            "agent_card": "/api/v1/a2a/agent-card"
        }
    }

    TASK_LIFECYCLE_MAPPING: Dict[str, Any] = {
        "failed_case_id": "RACE-005",
        "question": "What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?",
        "plain_rest_failure_behavior": (
            "Under synchronous REST, a 500 error from the Defined-Terms worker immediately terminates the HTTP connection, "
            "forcing the client to either drop the request or return an unverified hallucination."
        ),
        "a2a_lifecycle_mapping": {
            "state_transition": "submitted -> working -> input-required",
            "target_state": "input-required",
            "reason": (
                "The task pauses at 'input-required' to prompt human legal counsel: "
                "'Defined-Terms worker failed on Schedule B-2. Which amendment date or cure period governs this termination notice?'"
            )
        },
        "a2a_vs_rest_two_line_verdict": (
            "A2A provides an asynchronous, stateful task lifecycle with native human-in-the-loop pause states (input-required), "
            "whereas plain REST is a synchronous, stateless pipe that collapses into unrecoverable 500 dead-ends when sub-agents fail."
        )
    }

    @classmethod
    def get_agent_card_data(cls) -> Dict[str, Any]:
        cls.save_agent_card_file()
        return {
            "agent_card": cls.AGENT_CARD,
            "lifecycle_mapping": cls.TASK_LIFECYCLE_MAPPING
        }

    @classmethod
    def save_agent_card_file(cls):
        os.makedirs(os.path.dirname(AGENT_CARD_PATH), exist_ok=True)
        payload = {
            "agent_card": cls.AGENT_CARD,
            "lifecycle_mapping": cls.TASK_LIFECYCLE_MAPPING
        }
        with open(AGENT_CARD_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
