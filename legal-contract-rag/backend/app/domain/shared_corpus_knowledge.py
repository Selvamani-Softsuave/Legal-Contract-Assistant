"""
Shared Corpus Knowledge Base for Week 12 Capstone & Enterprise RAG.
Provides structured metadata, amendment chains, clause texts with citation headers,
and legal term definitions across all 6 shared corpus agreements and benchmark accounts.
"""

from typing import Dict, Any, List, Optional

# Counterparty alias mapping
COUNTERPARTY_ALIASES = {
    "northwind": "MSA-2026-014",
    "northwind logistics": "MSA-2026-014",
    "northwind logistics private limited": "MSA-2026-014",
    "vertex": "MSA-2026-022",
    "vertex retail": "MSA-2026-022",
    "vertex retail pte ltd": "MSA-2026-022",
    "halcyon": "NDA-2026-007",
    "halcyon analytics": "NDA-2026-007",
    "halcyon analytics oy": "NDA-2026-007",
    "acme": "CNT-MAIN-2024",
    "zeta": "CNT-MAIN-2024",
}

SHARED_METADATA = {
    "MSA-2026-014": {
        "contract_id": "MSA-2026-014",
        "title": "Master Services Agreement (Northwind Logistics)",
        "counterparty": "Northwind Logistics Private Limited",
        "provider": "Soft Suave Technologies Private Limited",
        "effective_date": "2026-01-14",
        "initial_term": "2 years (expiring 13 January 2028)",
        "governing_law": "Laws of India",
        "jurisdiction": "Courts of Chennai, Tamil Nadu, India",
        "status": "Active (Amended by Amendment No. 1 and Amendment No. 2)",
        "total_value_usd": 973200.00,
        "monthly_fee_usd": 81100.00,
        "linked_documents": ["AMD-2026-014-01", "AMD-2026-014-02", "SCH-2026-014"],
        "controlling_document": "AMD-2026-014-02"
    },
    "AMD-2026-014-01": {
        "contract_id": "AMD-2026-014-01",
        "title": "Amendment No. 1 to Master Services Agreement",
        "counterparty": "Northwind Logistics Private Limited",
        "effective_date": "2026-04-01",
        "parent_contract_id": "MSA-2026-014",
        "status": "Executed — superseded in part by Amendment No. 2",
        "summary": "Amended payment terms to 45 days, cure period to 45 days, termination for convenience to 30 days, audit frequency to twice per calendar year, and service credits cap to 10%."
    },
    "AMD-2026-014-02": {
        "contract_id": "AMD-2026-014-02",
        "title": "Amendment No. 2 to Master Services Agreement",
        "counterparty": "Northwind Logistics Private Limited",
        "effective_date": "2026-08-01",
        "parent_contract_id": "MSA-2026-014",
        "status": "Executed — CURRENT / CONTROLLING",
        "summary": "Amended termination for convenience to 15 Business Days (removing 12mo restriction), increased liability cap to greater of USD 5,000,000 or 12mo fees, inserted Section 10.4 India data residency, extended confidentiality survival to 7 years, and confirmed 45-day payment terms."
    },
    "SCH-2026-014": {
        "contract_id": "SCH-2026-014",
        "title": "Schedules to Master Services Agreement MSA-2026-014",
        "counterparty": "Northwind Logistics Private Limited",
        "effective_date": "2026-01-14",
        "parent_contract_id": "MSA-2026-014",
        "status": "Executed",
        "schedules": [
            "Schedule A (Description of Services & Critical Services SVC-01, SVC-02)",
            "Schedule B (Fees: $81,100/mo, ACV $973,200 & Service Levels & Credits)",
            "Schedule B-2 (Notice & Escalation Matrix: Breach Notification Deadlines)",
            "Schedule C (Holiday Calendar 2026 & 2027: Deepavali 20 Oct 2026)",
            "Schedule D (Notice Addresses)"
        ]
    },
    "MSA-2026-022": {
        "contract_id": "MSA-2026-022",
        "title": "Master Services Agreement (Vertex Retail)",
        "counterparty": "Vertex Retail Pte. Ltd.",
        "provider": "Soft Suave Technologies Private Limited",
        "effective_date": "2026-03-03",
        "initial_term": "3 years",
        "governing_law": "Laws of Singapore",
        "jurisdiction": "Arbitration administered by SIAC in Singapore (no Indian court jurisdiction)",
        "status": "Executed — No amendments executed (Section 20.1)",
        "liability_cap_usd": 500000.00,
        "fee_increase": "Not more than 3% per annum on 90 days' prior written notice",
        "cure_period": "20 days",
        "termination_convenience": "90 days' prior written notice, no notice permitted during first 24 months of Initial Term",
        "business_day_rule": "Based on Singapore public holidays; no separate calendar schedule incorporated"
    },
    "NDA-2026-007": {
        "contract_id": "NDA-2026-007",
        "title": "Mutual Non-Disclosure Agreement (Halcyon Analytics)",
        "counterparty": "Halcyon Analytics Oy",
        "provider": "Soft Suave Technologies Private Limited",
        "effective_date": "2026-05-22",
        "governing_law": "Laws of England and Wales",
        "status": "Executed — Standalone agreement (no amendments)",
        "survival": "Three (3) years from termination or expiry; perpetual for trade secrets",
        "liability_cap": "EUR 50,000 in aggregate; breach of Section 3 (Confidentiality) is uncapped"
    },
    "CNT-MAIN-2024": {
        "contract_id": "CNT-MAIN-2024",
        "title": "Master Services Agreement (Acme Global & Zeta Cloud)",
        "counterparty": "Zeta Cloud Services LLC",
        "effective_date": "2024-01-15",
        "expiration_date": "2027-01-14",
        "governing_law": "State of Delaware, United States",
        "status": "Active (Amended)",
        "total_value_usd": 1250000.00,
        "linked_documents": ["CNT-AMD-2024-01"]
    },
    "CNT-AMD-2024-01": {
        "contract_id": "CNT-AMD-2024-01",
        "title": "Amendment No. 1 to Master Services Agreement",
        "counterparty": "Zeta Cloud Services LLC",
        "effective_date": "2024-06-01",
        "parent_contract_id": "CNT-MAIN-2024",
        "status": "Active",
        "summary": "Dispute resolution relocation to AAA arbitration in Wilmington, DE."
    }
}

SHARED_AMENDMENT_CHAINS = {
    "MSA-2026-014": [
        {
            "sequence": 1,
            "amendment_id": "AMD-2026-014-01",
            "title": "Amendment No. 1 to Master Services Agreement",
            "effective_date": "2026-04-01",
            "status": "Partially Superseded by Amendment No. 2",
            "summary": "Amended Section 3.3 (Payment Terms: 45 days), Section 7.3 (Termination for Convenience: 30 days), Section 1.4 (Cure Period: 45 days), Schedule B Part 3 (Service Credits max: 10%), and Section 11.1 (Audit: twice per calendar year).",
            "affected_sections": ["Section 3.3", "Section 7.3", "Section 1.4", "Schedule B Part 3", "Section 11.1"]
        },
        {
            "sequence": 2,
            "amendment_id": "AMD-2026-014-02",
            "title": "Amendment No. 2 to Master Services Agreement",
            "effective_date": "2026-08-01",
            "status": "CURRENT / CONTROLLING",
            "summary": "SUPERSEDING GOVERNING AMENDMENT: Section 1.1 amends Section 7.3 (Termination for Convenience: 15 Business Days, removes 12mo restriction); Section 2.1 replaces Section 8.3 (Liability Cap: USD 5,000,000 or 12mo fees paid); Section 3.1 inserts Section 7.6 (Material Breach Notice Deadline: Schedule B-2 Part 2); Section 4.1 inserts Section 10.4 (Data Residency: India); Section 5.1 replaces Section 5.3 (Confidentiality Survival: 7 years); Section 6.1 confirms 45-day Payment Terms remain in effect.",
            "affected_sections": ["Section 7.3 (Replaced)", "Section 8.3 (Replaced)", "Section 7.6 (Inserted)", "Section 10.4 (Inserted)", "Section 5.3 (Replaced)"]
        }
    ],
    "MSA-2026-022": [
        {
            "sequence": 0,
            "amendment_id": "NONE",
            "title": "No Amendments Executed",
            "effective_date": "2026-03-03",
            "status": "Standalone Agreement",
            "summary": "Section 20.1 of MSA-2026-022 expressly states that no amendments have been executed.",
            "affected_sections": []
        }
    ],
    "NDA-2026-007": [
        {
            "sequence": 0,
            "amendment_id": "NONE",
            "title": "No Amendments Executed",
            "effective_date": "2026-05-22",
            "status": "Standalone Agreement",
            "summary": "Standalone mutual non-disclosure agreement; no amendments or addenda executed.",
            "affected_sections": []
        }
    ],
    "CNT-MAIN-2024": [
        {
            "sequence": 1,
            "amendment_id": "CNT-AMD-2024-01",
            "title": "Dispute Resolution & SLA Update Amendment",
            "effective_date": "2024-06-01",
            "status": "Active",
            "summary": "Supersedes former Clause 12.4; mandates 14-day senior executive escalation followed by AAA binding arbitration in Wilmington, DE.",
            "affected_sections": ["Clause 12.4 (Replaced)", "Schedule B (SLA Updated)"]
        }
    ]
}

def resolve_contract_id(query_or_id: str) -> str:
    """Resolve counterparty name or agreement alias to canonical contract ID."""
    clean = query_or_id.strip().lower()
    if clean in COUNTERPARTY_ALIASES:
        return COUNTERPARTY_ALIASES[clean]
    for alias, cid in COUNTERPARTY_ALIASES.items():
        if alias in clean:
            return cid
    clean_upper = query_or_id.strip().upper()
    if clean_upper in SHARED_METADATA:
        return clean_upper
    for cid in SHARED_METADATA.keys():
        if cid in clean_upper:
            return cid
    return query_or_id.strip()


SHARED_CLAUSES: Dict[str, Dict[str, Any]] = {
    "MSA-2026-014": {
        "title": "Master Services Agreement (Northwind Logistics)",
        "source_doc": "MSA-2026-014",
        "effective_date": "2026-01-14",
        "clauses": {
            "1.1": {
                "number": "1.1",
                "clause_ref": "Section 1.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "definitions",
                "title": "Definitions & Interpretations",
                "text": "'Affiliate' means any entity that directly or indirectly controls, is controlled by, or is under common control with the subject entity, where 'control' means direct or indirect ownership of greater than fifty percent (50%) of the voting securities or economic interests of such entity. 'Confidential Information' means all non-public proprietary materials and technical data. 'Effective Date' means 14 January 2026."
            },
            "1.2": {
                "number": "1.2",
                "clause_ref": "Section 1.2",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "definitions",
                "title": "Business Day Definition",
                "text": "'Business Day' means any day other than a Saturday, Sunday, or a day observed as a public holiday in Chennai, Tamil Nadu, India, as formally enumerated in the Holiday Calendar set forth in Schedule C hereto."
            },
            "1.4": {
                "number": "1.4",
                "clause_ref": "Section 1.4",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "cure_period",
                "title": "Cure Period for Material Breach",
                "text": "The breaching party shall have thirty (30) days following receipt of written notice to cure any material breach of this Agreement.",
                "superseded_by": {
                    "amendment_id": "AMD-2026-014-01",
                    "section": "Section 4.1",
                    "effective_date": "2026-04-01",
                    "summary": "Cure period increased to forty-five (45) days."
                }
            },
            "3.3": {
                "number": "3.3",
                "clause_ref": "Section 3.3",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "payment_terms",
                "title": "Payment Invoicing and Terms",
                "text": "Customer shall remit payment for undisputed invoices within thirty (30) calendar days from receipt of a valid and correct invoice from Provider.",
                "superseded_by": {
                    "amendment_id": "AMD-2026-014-01",
                    "section": "Section 1.1",
                    "effective_date": "2026-04-01",
                    "summary": "Payment terms extended to forty-five (45) days, reconfirmed in AMD-2026-014-02 Section 6.1."
                }
            },
            "5.1": {
                "number": "5.1",
                "clause_ref": "Section 5.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "confidentiality",
                "title": "Confidentiality Obligations",
                "text": "Each party shall maintain the confidentiality of the other party's Confidential Information with the same degree of care it uses for its own confidential information, but in no event less than a reasonable standard of care."
            },
            "5.3": {
                "number": "5.3",
                "clause_ref": "Section 5.3",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "confidentiality_survival",
                "title": "Survival of Confidentiality",
                "text": "The confidentiality obligations under Section 5 shall survive the expiration or termination of this Agreement for a period of five (5) years.",
                "superseded_by": {
                    "amendment_id": "AMD-2026-014-02",
                    "section": "Section 5.1",
                    "effective_date": "2026-08-01",
                    "summary": "Confidentiality survival extended to seven (7) years following termination or expiry; trade secrets survive in perpetuity."
                }
            },
            "7.1": {
                "number": "7.1",
                "clause_ref": "Section 7.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "term",
                "title": "Initial Term and Expiration",
                "text": "This Agreement shall commence on the Effective Date (14 January 2026) and continue for an Initial Term of two (2) years, expiring on 13 January 2028, unless earlier terminated in accordance with this Section 7."
            },
            "7.3": {
                "number": "7.3",
                "clause_ref": "Section 7.3",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "termination_for_convenience",
                "title": "Termination for Convenience",
                "text": "Either party may terminate this Agreement for convenience upon sixty (60) days' prior written notice to the other party; provided, however, that no such termination may take effect during the first twelve (12) months of the Initial Term.",
                "superseded_by": {
                    "amendment_id": "AMD-2026-014-02",
                    "section": "Section 1.1",
                    "effective_date": "2026-08-01",
                    "summary": "Replaced by AMD-2026-014-02 Section 1.1: Termination for convenience upon fifteen (15) Business Days' notice, 12-month restriction deleted."
                }
            },
            "8.1": {
                "number": "8.1",
                "clause_ref": "Section 8.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "consequential_damages",
                "title": "Waiver of Consequential Damages",
                "text": "Neither party shall be liable for any indirect, incidental, consequential, special, punitive, or exemplary damages, loss of profits, or business interruption."
            },
            "8.3": {
                "number": "8.3",
                "clause_ref": "Section 8.3",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "limitation_of_liability",
                "title": "Aggregate Liability Cap",
                "text": "In no event shall either party's aggregate cumulative liability arising out of or related to this Agreement exceed USD 2,000,000 (Two Million United States Dollars).",
                "superseded_by": {
                    "amendment_id": "AMD-2026-014-02",
                    "section": "Section 2.1",
                    "effective_date": "2026-08-01",
                    "summary": "Replaced by AMD-2026-014-02 Section 2.1: Liability cap increased to greater of USD 5,000,000 or total fees paid/payable in preceding 12 months."
                }
            },
            "10.1": {
                "number": "10.1",
                "clause_ref": "Section 10.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "data_protection",
                "title": "Data Protection Compliance",
                "text": "Each party shall comply with applicable data protection laws, including the Digital Personal Data Protection Act, 2023 (DPDP Act), in processing personal data under this Agreement."
            },
            "11.1": {
                "number": "11.1",
                "clause_ref": "Section 11.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "audit_rights",
                "title": "Audit Rights",
                "text": "Customer shall have the right, upon reasonable prior notice, to inspect and audit Provider's records relating to the Services once per calendar year.",
                "superseded_by": {
                    "amendment_id": "AMD-2026-014-01",
                    "section": "Section 5.1",
                    "effective_date": "2026-04-01",
                    "summary": "Audit frequency increased to twice per calendar year."
                }
            },
            "13.1": {
                "number": "13.1",
                "clause_ref": "Section 13.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "insurance",
                "title": "Insurance Requirements",
                "text": "Provider shall maintain commercial general liability and cybersecurity insurance of not less than USD 1,000,000 per claim throughout the Term and for two (2) years thereafter."
            },
            "14.1": {
                "number": "14.1",
                "clause_ref": "Section 14.1",
                "source_doc": "MSA-2026-014",
                "effective_date": "2026-01-14",
                "type": "governing_law",
                "title": "Governing Law and Jurisdiction",
                "text": "This Agreement shall be governed by and construed in accordance with the laws of India. The courts of Chennai, Tamil Nadu, India shall have exclusive jurisdiction over all disputes."
            }
        },
        "definitions": {
            "Affiliate": "Any entity that directly or indirectly controls, is controlled by, or is under common control with the subject entity, where 'control' means direct or indirect ownership of greater than fifty percent (50%) of the voting securities or economic interests of such entity.",
            "Business Day": "Any day other than a Saturday, Sunday, or a day observed as a public holiday in Chennai, Tamil Nadu, India, as formally enumerated in Schedule C (Holiday Calendar). Deepavali on 20 October 2026 is an enumerated holiday and NOT a Business Day.",
            "Confidential Information": "All non-public proprietary materials, trade secrets, customer records, and technical documentation designated as confidential or reasonably understood to be confidential.",
            "Effective Date": "14 January 2026, the commencement date of MSA-2026-014.",
            "Initial Term": "The two (2) year period commencing on the Effective Date (14 January 2026) and expiring on 13 January 2028."
        },
        "relocated_clauses": {}
    },
    "AMD-2026-014-01": {
        "title": "Amendment No. 1 to Master Services Agreement",
        "source_doc": "AMD-2026-014-01",
        "effective_date": "2026-04-01",
        "clauses": {
            "1.1": {
                "number": "1.1",
                "clause_ref": "Section 1.1",
                "source_doc": "AMD-2026-014-01",
                "effective_date": "2026-04-01",
                "type": "payment_terms",
                "title": "Amendment of Payment Terms",
                "text": "Section 3.3 of the Agreement is hereby amended by deleting 'thirty (30) calendar days' and substituting therefor 'forty-five (45) calendar days'."
            },
            "4.1": {
                "number": "4.1",
                "clause_ref": "Section 4.1",
                "source_doc": "AMD-2026-014-01",
                "effective_date": "2026-04-01",
                "type": "cure_period",
                "title": "Amendment of Material Breach Cure Period",
                "text": "Section 1.4 of the Agreement is hereby amended by deleting 'thirty (30) days' and substituting therefor 'forty-five (45) days'."
            },
            "5.1": {
                "number": "5.1",
                "clause_ref": "Section 5.1",
                "source_doc": "AMD-2026-014-01",
                "effective_date": "2026-04-01",
                "type": "audit_rights",
                "title": "Amendment of Audit Rights",
                "text": "Section 11.1 of the Agreement is hereby amended to permit Customer audits twice per calendar year upon twenty (20) Business Days' notice."
            }
        },
        "definitions": {},
        "relocated_clauses": {}
    },
    "AMD-2026-014-02": {
        "title": "Amendment No. 2 to Master Services Agreement (CURRENT / CONTROLLING)",
        "source_doc": "AMD-2026-014-02",
        "effective_date": "2026-08-01",
        "clauses": {
            "1.1": {
                "number": "1.1",
                "clause_ref": "Section 1.1",
                "source_doc": "AMD-2026-014-02",
                "effective_date": "2026-08-01",
                "type": "termination_for_convenience",
                "title": "Amendment of Termination for Convenience",
                "text": "Section 7.3 of the Master Services Agreement is hereby deleted in its entirety and replaced with: 'Either party may terminate this Agreement or any Schedule for convenience, in whole or in part, upon not less than fifteen (15) Business Days' prior written notice to the other party. The restriction prohibiting termination during the first twelve (12) months is hereby nullified and deleted.'"
            },
            "2.1": {
                "number": "2.1",
                "clause_ref": "Section 2.1",
                "source_doc": "AMD-2026-014-02",
                "effective_date": "2026-08-01",
                "type": "limitation_of_liability",
                "title": "Amendment of Limitation of Liability Cap",
                "text": "Section 8.3 of the Agreement is hereby deleted in its entirety and replaced with: 'Each party's maximum aggregate cumulative liability arising out of or related to this Agreement shall be capped at the greater of USD 5,000,000 (Five Million United States Dollars) or the total aggregate fees paid or payable by Customer to Provider in the twelve (12) months immediately preceding the claim.'"
            },
            "3.1": {
                "number": "3.1",
                "clause_ref": "Section 3.1",
                "source_doc": "AMD-2026-014-02",
                "effective_date": "2026-08-01",
                "type": "material_breach_notice",
                "title": "Insertion of Section 7.6 (Material Breach Notice Deadline)",
                "text": "A new Section 7.6 is inserted: 'Notice of material breach shall be delivered in accordance with the notification deadlines specified in Schedule B-2 Part 2 (Notice and Escalation Matrix). Failure to notify within the designated window constitutes a waiver of expedited cure.'"
            },
            "4.1": {
                "number": "4.1",
                "clause_ref": "Section 4.1",
                "source_doc": "AMD-2026-014-02",
                "effective_date": "2026-08-01",
                "type": "data_residency",
                "title": "Insertion of Section 10.4 (India Data Residency)",
                "text": "A new Section 10.4 is inserted: 'Provider warrants and undertakes that all Customer Personal Data and operational telemetry shall be hosted and processed exclusively on servers located within the territorial boundaries of the Republic of India.'"
            },
            "5.1": {
                "number": "5.1",
                "clause_ref": "Section 5.1",
                "source_doc": "AMD-2026-014-02",
                "effective_date": "2026-08-01",
                "type": "confidentiality_survival",
                "title": "Replacement of Confidentiality Survival",
                "text": "Section 5.3 of the Agreement is deleted and replaced with: 'The confidentiality obligations under Section 5 shall survive the expiration or termination of this Agreement for a period of seven (7) years; provided that trade secrets and proprietary source code shall remain confidential in perpetuity.'"
            },
            "6.1": {
                "number": "6.1",
                "clause_ref": "Section 6.1",
                "source_doc": "AMD-2026-014-02",
                "effective_date": "2026-08-01",
                "type": "payment_terms",
                "title": "Confirmation of Payment Terms",
                "text": "The Parties confirm that the forty-five (45) day payment terms set forth in Amendment No. 1 remain in full force and effect."
            }
        },
        "definitions": {
            "Controlling Document": "Amendment No. 2 (AMD-2026-014-02) is the controlling and superseding instrument for liability caps, convenience termination, data residency, and confidentiality survival."
        },
        "relocated_clauses": {}
    },
    "SCH-2026-014": {
        "title": "Schedules to Master Services Agreement (Northwind)",
        "source_doc": "SCH-2026-014",
        "effective_date": "2026-01-14",
        "clauses": {
            "Schedule A": {
                "number": "Schedule A",
                "clause_ref": "Schedule A Part 2",
                "source_doc": "SCH-2026-014",
                "effective_date": "2026-01-14",
                "type": "services_specification",
                "title": "Critical Services Designation",
                "text": "The following services are designated Critical Services: SVC-01 (Shipment Tracking Platform) and SVC-02 (Fleet Telematics Engine). SVC-05 does not exist and is not provided."
            },
            "Schedule B": {
                "number": "Schedule B",
                "clause_ref": "Schedule B Part 1 & 2",
                "source_doc": "SCH-2026-014",
                "effective_date": "2026-01-14",
                "type": "fees_and_sla",
                "title": "Fees, SLA Targets, and Service Credits",
                "text": "Part 1 (Fees): Monthly recurring charge is USD 81,100, yielding an Annual Contract Value (ACV) of USD 973,200. Allocation: SVC-01 is USD 42,000/mo; SVC-02 is USD 39,100/mo.\nPart 2 (SLA): Monthly availability target for SVC-01 is 99.9%. For SVC-02 target is 99.5%.\nPart 3 (Service Credits): If SVC-01 monthly availability falls between 99.0% and 99.89%, Customer receives a 5% credit of SVC-01 monthly fee (USD 2,100). Total monthly credits capped at 10% per AMD-01."
            },
            "Schedule B-2": {
                "number": "Schedule B-2",
                "clause_ref": "Schedule B-2 Part 2",
                "source_doc": "SCH-2026-014",
                "effective_date": "2026-01-14",
                "type": "escalation_matrix",
                "title": "Notice and Escalation Matrix",
                "text": "Breach notification timelines: Critical Priority incidents must be notified in writing within twenty-four (24) hours; High Priority within forty-eight (48) hours; Medium/Low within five (5) Business Days."
            },
            "Schedule C": {
                "number": "Schedule C",
                "clause_ref": "Schedule C",
                "source_doc": "SCH-2026-014",
                "effective_date": "2026-01-14",
                "type": "holiday_calendar",
                "title": "Holiday Calendar 2026 & 2027",
                "text": "Official non-business public holidays: Republic Day (26 Jan 2026), May Day (1 May 2026), Independence Day (15 Aug 2026), Gandhi Jayanti (2 Oct 2026), Deepavali / Diwali (20 Oct 2026), Christmas (25 Dec 2026). Deepavali on 20 October 2026 is an observed holiday and NOT a Business Day."
            },
            "Schedule D": {
                "number": "Schedule D",
                "clause_ref": "Schedule D",
                "source_doc": "SCH-2026-014",
                "effective_date": "2026-01-14",
                "type": "notice_addresses",
                "title": "Official Notice Addresses",
                "text": "Notice addresses: Provider (Soft Suave Technologies Pvt Ltd, Anna Salai, Chennai 600002, India); Customer (Northwind Logistics Pvt Ltd, Outer Ring Road, Bengaluru 560103, India)."
            }
        },
        "definitions": {
            "SVC-01": "Shipment Tracking Platform, designated Critical Service with 99.9% availability target.",
            "SVC-02": "Fleet Telematics Engine, designated Critical Service with 99.5% availability target."
        },
        "relocated_clauses": {}
    },
    "MSA-2026-022": {
        "title": "Master Services Agreement (Vertex Retail)",
        "source_doc": "MSA-2026-022",
        "effective_date": "2026-03-03",
        "clauses": {
            "1.2": {
                "number": "1.2",
                "clause_ref": "Section 1.2",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "definitions",
                "title": "Business Day Definition",
                "text": "'Business Day' means any day other than a Saturday, Sunday, or gazetted public holiday in the Republic of Singapore. This Agreement does not incorporate a separate holiday calendar schedule."
            },
            "1.4": {
                "number": "1.4",
                "clause_ref": "Section 1.4",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "cure_period",
                "title": "Material Breach Cure Period",
                "text": "The defaulting party shall have twenty (20) days following receipt of written notification to cure any material default."
            },
            "3.6": {
                "number": "3.6",
                "clause_ref": "Section 3.6",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "fee_increase",
                "title": "Annual Fee Adjustments",
                "text": "Provider may adjust service fees once per calendar year by not more than three percent (3%) upon ninety (90) days' prior written notice."
            },
            "7.3": {
                "number": "7.3",
                "clause_ref": "Section 7.3",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "termination_for_convenience",
                "title": "Termination for Convenience",
                "text": "Either party may terminate this Agreement for convenience upon ninety (90) days' prior written notice; provided that no notice of termination may be given during the first twenty-four (24) months of the Initial Term."
            },
            "8.3": {
                "number": "8.3",
                "clause_ref": "Section 8.3",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "limitation_of_liability",
                "title": "Aggregate Liability Cap",
                "text": "Each party's maximum total aggregate liability arising out of or related to this Agreement shall not exceed USD 500,000 (Five Hundred Thousand United States Dollars)."
            },
            "15.1": {
                "number": "15.1",
                "clause_ref": "Section 15.1",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "dispute_resolution",
                "title": "Arbitration under SIAC",
                "text": "Any dispute arising out of or in connection with this contract shall be referred to and finally resolved by arbitration administered by the Singapore International Arbitration Centre (SIAC) in Singapore under the SIAC Rules. Indian courts have no jurisdiction."
            },
            "20.1": {
                "number": "20.1",
                "clause_ref": "Section 20.1",
                "source_doc": "MSA-2026-022",
                "effective_date": "2026-03-03",
                "type": "entire_agreement",
                "title": "Entire Agreement & Amendments",
                "text": "This Agreement constitutes the entire understanding between the parties. No amendments or modifications have been executed as of the execution date."
            }
        },
        "definitions": {
            "Business Day": "Any day other than Saturday, Sunday, or Singapore gazetted public holiday.",
            "SIAC Rules": "The Arbitration Rules of the Singapore International Arbitration Centre."
        },
        "relocated_clauses": {}
    },
    "NDA-2026-007": {
        "title": "Mutual Non-Disclosure Agreement (Halcyon Analytics)",
        "source_doc": "NDA-2026-007",
        "effective_date": "2026-05-22",
        "clauses": {
            "3.1": {
                "number": "3.1",
                "clause_ref": "Section 3.1",
                "source_doc": "NDA-2026-007",
                "effective_date": "2026-05-22",
                "type": "confidentiality",
                "title": "Duty of Confidentiality",
                "text": "Each party agrees to hold the other party's Confidential Information in strict confidence and not disclose it to any third party without express prior written consent."
            },
            "4.2": {
                "number": "4.2",
                "clause_ref": "Section 4.2",
                "source_doc": "NDA-2026-007",
                "effective_date": "2026-05-22",
                "type": "survival",
                "title": "Term and Survival",
                "text": "Confidentiality obligations shall survive for a period of three (3) years from termination or expiration of this Agreement; provided that trade secrets shall remain confidential in perpetuity."
            },
            "8.2": {
                "number": "8.2",
                "clause_ref": "Section 8.2",
                "source_doc": "NDA-2026-007",
                "effective_date": "2026-05-22",
                "type": "limitation_of_liability",
                "title": "Limitation of Liability",
                "text": "Aggregate liability under this Agreement is limited to EUR 50,000; provided that liability for breach of Section 3 (Confidentiality) is uncapped and unlimited."
            },
            "10.1": {
                "number": "10.1",
                "clause_ref": "Section 10.1",
                "source_doc": "NDA-2026-007",
                "effective_date": "2026-05-22",
                "type": "governing_law",
                "title": "Governing Law",
                "text": "This Agreement shall be governed by and construed in accordance with the laws of England and Wales."
            }
        },
        "definitions": {
            "Confidential Information": "Non-public technical, algorithmic, and financial information disclosed between parties.",
            "Survival": "Three (3) years from termination, perpetual for trade secrets."
        },
        "relocated_clauses": {}
    }
}

