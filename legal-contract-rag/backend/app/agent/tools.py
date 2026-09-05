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

MOCK_CONTRACT_STORE: Dict[str, Dict[ContractVersionEnum, Dict[str, Any]]] = {
    "CNT-MAIN": {
        ContractVersionEnum.ORIGINAL: {
            "metadata": {
                "title": "Vendor Services Agreement",
                "contract_id": "CNT-MAIN",
                "version": ContractVersionEnum.ORIGINAL.value,
                "execution_date": "2024-01-15",
                "effective_date": "2024-02-01",
                "parties": ["Acme Corp (Client)", "Global Logistics Ltd (Vendor)"],
                "initial_term_months": 12,
            },
            "clauses": {
                "TERMINATION": "ARTICLE 10 — TERMINATION\n10.1 Termination for Convenience: Either party may terminate this Agreement without cause after the initial twelve (12) month commitment period by providing ninety (90) days prior written notice to the other party.\n10.2 Termination for Cause: Either party may terminate immediately upon written notice if the other party commits a Material Breach and fails to cure such breach within the Cure Period following notice.\n10.3 Termination for Insolvency: Either party may terminate immediately upon written notice if the other party becomes insolvent or enters bankruptcy.",
                "NOTICE": "ARTICLE 11 — NOTICES\n11.1 Formal Notice: All notices under this Agreement must be in writing and delivered by certified mail or registered courier to the registered addresses specified in the Preamble.",
                "GOVERNING_LAW": "ARTICLE 14 — GOVERNING LAW\n14.1 This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware.",
                "LIMITATION_OF_LIABILITY": "ARTICLE 8 — LIMITATION OF LIABILITY\n8.1 Neither party's aggregate liability under this Agreement shall exceed the total fees paid in the preceding twelve (12) months.",
            },
            "definitions": {
                "CURE PERIOD": "Thirty (30) calendar days from receipt of written notice of breach.",
                "MATERIAL BREACH": "A substantial failure of a party to perform any primary service obligation under Section 4.",
                "NOTICE PERIOD": "The ninety (90) day written notice window mandated under Section 10.1.",
                "APPLICABLE SCHEDULE": "Schedule A (Standard Service Level Agreements).",
            },
        },
        ContractVersionEnum.AMENDMENT_V1: {
            "metadata": {
                "title": "Vendor Services Agreement — Amendment No. 1",
                "contract_id": "CNT-MAIN",
                "version": ContractVersionEnum.AMENDMENT_V1.value,
                "execution_date": "2024-06-15",
                "effective_date": "2024-07-01",
                "parties": ["Acme Corp (Client)", "Global Logistics Ltd (Vendor)"],
                "initial_term_months": 6,
            },
            "clauses": {
                "TERMINATION": "ARTICLE 10 — TERMINATION (AMENDED)\n10.1 Termination for Convenience: Either party may terminate for convenience upon sixty (60) days prior written notice after an initial six (6) month commitment period.\n10.2 Termination for Cause: Remains governed by Section 10.2 of the Original Agreement with extended Cure Period.",
                "NOTICE": "ARTICLE 11 — NOTICES (AMENDED)\n11.1 Formal Notice: Electronic mail with delivery confirmation is accepted as valid notice.",
            },
            "definitions": {
                "CURE PERIOD": "Forty-five (45) calendar days from receipt of written notice of breach.",
                "MATERIAL BREACH": "A breach resulting in verified direct financial damages exceeding $50,000.",
                "NOTICE PERIOD": "Sixty (60) days prior written notice for convenience.",
            },
        },
        ContractVersionEnum.AMENDMENT_V2: {
            "metadata": {
                "title": "Vendor Services Agreement — Amendment No. 2 (Executed Final)",
                "contract_id": "CNT-MAIN",
                "version": ContractVersionEnum.AMENDMENT_V2.value,
                "execution_date": "2024-11-20",
                "effective_date": "2024-12-01",
                "parties": ["Acme Corp (Client)", "Global Logistics Ltd (Vendor)"],
                "initial_term_months": 12,
            },
            "clauses": {
                "TERMINATION": "ARTICLE 10 — TERMINATION (FINAL AMENDED)\n10.1 Termination for Convenience: Either party may terminate this Agreement without cause after the initial twelve (12) month commitment period by providing ninety (90) days prior written notice.\n10.2 Termination for Cause: Either party may terminate if a Material Breach occurs. Notice requirements for cause turn on defined Schedule B-2.\n10.3 Accelerated Termination: In the event of a Change of Control, either party may terminate on thirty (30) days notice.",
                "NOTICE": "ARTICLE 11 — NOTICES (FINAL)\n11.1 Notices must be delivered via registered courier or secure client portal.",
            },
            "definitions": {
                "CURE PERIOD": "Thirty (30) calendar days from receipt of written notice of breach.",
                "SCHEDULE B-2": "Schedule detailing breach resolution: The termination notice deadline is fifteen (15) Business Days following the expiration of the 30-day Cure Period.",
                "BUSINESS DAY": "Any day other than Saturday, Sunday, or official bank holidays in New York.",
                "MATERIAL BREACH": "Any failure to deliver Milestone Deliverables within thirty (30) days of the scheduled delivery date as defined in Schedule B-2.",
                "NOTICE PERIOD": "Ninety (90) days for convenience; fifteen (15) Business Days post-cure for cause.",
                "CHANGE OF CONTROL": "Any merger, acquisition, or sale of greater than 50% of voting shares.",
                "CIRCULAR TERM ALPHA": "Defined in accordance with Circular Term Beta.",
                "CIRCULAR TERM BETA": "Defined in accordance with Circular Term Gamma.",
                "CIRCULAR TERM GAMMA": "Defined in accordance with Circular Term Alpha.",
            },
        },
        ContractVersionEnum.FINAL_EXECUTED: {
            # Alias to AMENDMENT_V2
            "metadata": {
                "title": "Vendor Services Agreement — Final Executed Version",
                "contract_id": "CNT-MAIN",
                "version": ContractVersionEnum.FINAL_EXECUTED.value,
                "execution_date": "2024-11-20",
                "effective_date": "2024-12-01",
                "parties": ["Acme Corp (Client)", "Global Logistics Ltd (Vendor)"],
                "initial_term_months": 12,
            },
            "clauses": {
                "TERMINATION": "ARTICLE 10 — TERMINATION (FINAL AMENDED)\n10.1 Termination for Convenience: Either party may terminate this Agreement without cause after the initial twelve (12) month commitment period by providing ninety (90) days prior written notice.\n10.2 Termination for Cause: Either party may terminate if a Material Breach occurs. Notice requirements for cause turn on defined Schedule B-2.\n10.3 Accelerated Termination: In the event of a Change of Control, either party may terminate on thirty (30) days notice.",
                "NOTICE": "ARTICLE 11 — NOTICES (FINAL)\n11.1 Notices must be delivered via registered courier or secure client portal.",
                "GOVERNING_LAW": "ARTICLE 14 — GOVERNING LAW\n14.1 Delaware State Law.",
            },
            "definitions": {
                "CURE PERIOD": "Thirty (30) calendar days from receipt of written notice of breach.",
                "SCHEDULE B-2": "Schedule detailing breach resolution: The termination notice deadline is fifteen (15) Business Days following the expiration of the 30-day Cure Period.",
                "BUSINESS DAY": "Any day other than Saturday, Sunday, or official bank holidays in New York.",
                "MATERIAL BREACH": "Any failure to deliver Milestone Deliverables within thirty (30) days of the scheduled delivery date as defined in Schedule B-2.",
                "NOTICE PERIOD": "Ninety (90) days for convenience; fifteen (15) Business Days post-cure for cause.",
                "CHANGE OF CONTROL": "Any merger, acquisition, or sale of greater than 50% of voting shares.",
                "CIRCULAR TERM ALPHA": "Defined in accordance with Circular Term Beta.",
                "CIRCULAR TERM BETA": "Defined in accordance with Circular Term Gamma.",
                "CIRCULAR TERM GAMMA": "Defined in accordance with Circular Term Alpha.",
            },
        },
    }
}


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
