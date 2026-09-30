"""
Agent Tools Registry for Week 7 Practical (Track F - Legal Contracts).
Implements 3 sharp, single-purpose, non-overlapping tools with typed Enums:
1. get_clause
2. get_effective_date_and_metadata
3. get_definitions (Third Tool with ContractVersionEnum)
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from backend.app.agent.enums import ContractVersionEnum, ClauseTypeEnum

logger = logging.getLogger("agent_tools")


# ─── Mock Legal Contract Repository for Deterministic Benchmarking ─────────────
from backend.app.evals.fixtures.mock_contract_store import MOCK_CONTRACT_STORE


# ─── Tool 1: get_clause ────────────────────────────────────────────────────────

def get_clause(
    clause_type: str,
    contract_id: str = "CNT-MAIN",
    contract_version: ContractVersionEnum = ContractVersionEnum.FINAL_EXECUTED,
) -> str:
    """
    [TOOL 1: GET_CLAUSE]
    Single Job: Retrieves the raw text of a specific contract section (e.g. Termination, Notice, Governing Law) from the specified contract version.
    Does NOT resolve defined legal terms or parse execution dates.
    """
    logger.info(f"Tool Exec: get_clause(clause_type='{clause_type}', contract_id='{contract_id}', version='{contract_version}')")
    c_store = MOCK_CONTRACT_STORE.get(contract_id, MOCK_CONTRACT_STORE["CNT-MAIN"])
    
    # Resolve version
    v_enum = contract_version if isinstance(contract_version, ContractVersionEnum) else ContractVersionEnum(contract_version)
    v_data = c_store.get(v_enum, c_store.get(ContractVersionEnum.FINAL_EXECUTED))
    
    # Normalize clause type
    c_type_upper = clause_type.upper().strip().replace(" ", "_")
    clauses = v_data.get("clauses", {})
    
    for k, text in clauses.items():
        if k in c_type_upper or c_type_upper in k:
            return text
            
    # Fallback search across keys
    for k, text in clauses.items():
        if clause_type.lower() in text.lower():
            return text
            
    return f"Clause '{clause_type}' not found in contract {contract_id} (version: {v_enum.value})."


# ─── Tool 2: get_effective_date_and_metadata ───────────────────────────────────

def get_effective_date_and_metadata(
    contract_id: str = "CNT-MAIN",
    contract_version: ContractVersionEnum = ContractVersionEnum.FINAL_EXECUTED,
) -> Dict[str, Any]:
    """
    [TOOL 2: GET_EFFECTIVE_DATE_AND_METADATA]
    Single Job: Extracts the execution date, effective date, and party names from the contract preamble or signature block.
    Does NOT retrieve substantive clauses or resolve defined terms.
    """
    logger.info(f"Tool Exec: get_effective_date_and_metadata(contract_id='{contract_id}', version='{contract_version}')")
    c_store = MOCK_CONTRACT_STORE.get(contract_id, MOCK_CONTRACT_STORE["CNT-MAIN"])
    v_enum = contract_version if isinstance(contract_version, ContractVersionEnum) else ContractVersionEnum(contract_version)
    v_data = c_store.get(v_enum, c_store.get(ContractVersionEnum.FINAL_EXECUTED))
    
    return v_data.get("metadata", {
        "error": f"Metadata not found for contract {contract_id} (version: {v_enum.value})"
    })


# ─── Tool 3: get_definitions (The Rubric-Required 3rd Tool) ───────────────────

def get_definitions(
    term: str,
    contract_version: ContractVersionEnum = ContractVersionEnum.FINAL_EXECUTED,
    contract_id: str = "CNT-MAIN",
) -> str:
    """
    [TOOL 3: GET_DEFINITIONS]
    Single Job: Looks up the precise definition of a capitalized legal term (e.g. 'Cause', 'Material Breach', 'Notice Period', 'Business Day', 'Schedule B-2') in the contract's definition section or schedules.
    Does NOT retrieve general contract clauses or metadata.
    """
    logger.info(f"Tool Exec: get_definitions(term='{term}', version='{contract_version}', contract_id='{contract_id}')")
    c_store = MOCK_CONTRACT_STORE.get(contract_id, MOCK_CONTRACT_STORE["CNT-MAIN"])
    v_enum = contract_version if isinstance(contract_version, ContractVersionEnum) else ContractVersionEnum(contract_version)
    v_data = c_store.get(v_enum, c_store.get(ContractVersionEnum.FINAL_EXECUTED))
    
    defs = v_data.get("definitions", {})
    term_upper = term.upper().strip()
    
    if term_upper in defs:
        return f"Defined Term '{term}' ({v_enum.value}): {defs[term_upper]}"
        
    for k, v in defs.items():
        if term_upper in k or k in term_upper:
            return f"Defined Term '{k}' ({v_enum.value}): {v}"
            
    return f"Defined term '{term}' is unstated in {contract_id} definitions ({v_enum.value})."


# ─── Tool Metadata & Schema Registry ──────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_clause",
        "description": "Retrieves the raw text of a specific contract section (e.g. Termination, Notice, Governing Law) from the specified contract version. Does NOT define terms or retrieve execution dates.",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_type": {
                    "type": "string",
                    "description": "The type of clause to retrieve (e.g. 'TERMINATION', 'NOTICE', 'GOVERNING_LAW')."
                },
                "contract_id": {
                    "type": "string",
                    "description": "The unique contract identifier (default 'CNT-MAIN')."
                },
                "contract_version": {
                    "type": "string",
                    "enum": [v.value for v in ContractVersionEnum],
                    "description": "The target contract version."
                }
            },
            "required": ["clause_type"]
        }
    },
    {
        "name": "get_effective_date_and_metadata",
        "description": "Extracts the execution date, effective date, and party names from the contract preamble or signature block. Does NOT extract substantive clauses or legal term definitions.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The unique contract identifier (default 'CNT-MAIN')."
                },
                "contract_version": {
                    "type": "string",
                    "enum": [v.value for v in ContractVersionEnum],
                    "description": "The target contract version."
                }
            }
        }
    },
    {
        "name": "get_definitions",
        "description": "Looks up the precise definition of a capitalized legal term (e.g. 'Cause', 'Material Breach', 'Notice Period', 'Business Day', 'Schedule B-2') in the contract's definition section or schedules. Does NOT retrieve general contract clauses or metadata.",
        "parameters": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "The capitalized defined term to look up (e.g. 'Material Breach', 'Cure Period', 'Notice Period')."
                },
                "contract_version": {
                    "type": "string",
                    "enum": [v.value for v in ContractVersionEnum],
                    "description": "The contract version containing the relevant definitions."
                },
                "contract_id": {
                    "type": "string",
                    "description": "The unique contract identifier (default 'CNT-MAIN')."
                }
            },
            "required": ["term"]
        }
    }
]


AVAILABLE_TOOLS = {
    "get_clause": get_clause,
    "get_effective_date_and_metadata": get_effective_date_and_metadata,
    "get_definitions": get_definitions,
}
