"""
Evaluation & Benchmark Mock Contract Fixtures.
Isolated fixture data used for deterministic benchmarks, regression evals, and trajectory testing.
"""

from typing import Dict, Any
from backend.app.agent.enums import ContractVersionEnum

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
