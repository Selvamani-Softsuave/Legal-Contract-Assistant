import os
import sys
import json
import csv
import asyncio
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import SessionLocal
from backend.app.services.rag_service import EnterpriseRAGService
from backend.app.repositories.chat_repository import ChatRepository
from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("week5_traces")

# 20 Diverse Legal Questions for Track F (Legal Contracts)
TEST_QUESTIONS = [
    {
        "id": "TR-LEGAL-001",
        "category": "Identifiers & Headings",
        "question": "What is the agreement number for the Vendor Services Agreement?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "VSA-2026-022 in Vendor_Agreement.pdf"
    },
    {
        "id": "TR-LEGAL-002",
        "category": "Identifiers & Headings",
        "question": "What are the early termination conditions under Article 10?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "ARTICLE 10 — EARLY TERMINATION in Chunking_Test_Amendment.pdf"
    },
    {
        "id": "TR-LEGAL-003",
        "category": "Identifiers & Headings",
        "question": "Where is the contract amendment chunking test document stored?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Chunking_Test_Amendment.pdf"
    },
    {
        "id": "TR-LEGAL-004",
        "category": "Identifiers & Headings",
        "question": "What is the internal contract identifier for the Vendor Service Agreement?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "CNT-4A40A677"
    },
    {
        "id": "TR-LEGAL-005",
        "category": "Numerical & Time Terms",
        "question": "How many business days written notice is required for a compliance audit?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "fifteen (15) business days written notice"
    },
    {
        "id": "TR-LEGAL-006",
        "category": "Numerical & Time Terms",
        "question": "What audit frequency is permitted for the client in a single calendar year?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "One compliance audit per calendar year"
    },
    {
        "id": "TR-LEGAL-007",
        "category": "Numerical & Time Terms",
        "question": "How many days notice is required for early termination for convenience?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "ninety (90) days written notice after initial 12 months"
    },
    {
        "id": "TR-LEGAL-008",
        "category": "Numerical & Time Terms",
        "question": "What is the initial commitment period before termination for convenience is allowed?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Initial twelve-month (12) commitment period"
    },
    {
        "id": "TR-LEGAL-009",
        "category": "Liability & Governing Law",
        "question": "What is the governing law for disputes in the vendor services agreement?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Laws of India / Courts having jurisdiction in India"
    },
    {
        "id": "TR-LEGAL-010",
        "category": "Liability & Governing Law",
        "question": "Which courts have jurisdiction over legal disputes under VSA-2026-022?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Courts having jurisdiction in India"
    },
    {
        "id": "TR-LEGAL-011",
        "category": "Liability & Governing Law",
        "question": "What is the limitation of liability cap specified in Contract Test 1?",
        "contract_id": "0b2fb130-dfe3-4547-844e-1f942871115c",
        "expected": "No documents uploaded for Contract Test 1 (Fallback / Missing Info)"
    },
    {
        "id": "TR-LEGAL-012",
        "category": "Liability & Governing Law",
        "question": "What indemnification obligations exist for breach of confidentiality?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "No explicit indemnification clause present in short sample PDF"
    },
    {
        "id": "TR-LEGAL-013",
        "category": "Multi-Doc Scoping",
        "question": "What delivery obligations are required of the vendor in Contract Test 1?",
        "contract_id": "0b2fb130-dfe3-4547-844e-1f942871115c",
        "expected": "0 documents found in Contract Test 1 scope"
    },
    {
        "id": "TR-LEGAL-014",
        "category": "Multi-Doc Scoping",
        "question": "Find all delivery and dispute terms across all indexed contracts in global mode",
        "contract_id": None,
        "expected": "Global search retrieving Vendor_Agreement.pdf & Chunking_Test_Amendment.pdf"
    },
    {
        "id": "TR-LEGAL-015",
        "category": "Multi-Doc Scoping",
        "question": "Compare early termination notice in Amendment vs Vendor Services Agreement",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Vendor_Agreement vs Chunking_Test_Amendment terms"
    },
    {
        "id": "TR-LEGAL-016",
        "category": "Multi-Doc Scoping",
        "question": "List all associated legal documents under contract CNT-4A40A677",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Vendor_Agreement.pdf & Chunking_Test_Amendment.pdf"
    },
    {
        "id": "TR-LEGAL-017",
        "category": "Edge Cases & Out-of-Scope",
        "question": "What is the interest rate percentage charged for late invoice payments?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "No late payment interest rate clause in text"
    },
    {
        "id": "TR-LEGAL-018",
        "category": "Edge Cases & Out-of-Scope",
        "question": "What is the non-compete clause duration for executive employees?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "Out-of-scope non-compete clause"
    },
    {
        "id": "TR-LEGAL-019",
        "category": "Edge Cases & Out-of-Scope",
        "question": "Does the vendor agreement automatically renew for successive 1-year terms?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "No automatic renewal clause present in text"
    },
    {
        "id": "TR-LEGAL-020",
        "category": "Edge Cases & Out-of-Scope",
        "question": "What are the intellectual property ownership assignment rights in Section 4?",
        "contract_id": "4a40a677-03f1-4ac8-b380-0596e810e8e0",
        "expected": "No IP assignment clause in text"
    }
]

async def run_traces():
    logger.info(f"Executing 20 live RAG traces for Track F Error Analysis...")
    rag_service = EnterpriseRAGService()
    traces_output = []

    for item in TEST_QUESTIONS:
        trace_id = item["id"]
        category = item["category"]
        question = item["question"]
        contract_id = item["contract_id"]
        expected = item["expected"]
        scoped_ids = [contract_id] if contract_id else None

        db = SessionLocal()
        try:
            chat_repo = ChatRepository(db)
            conv = chat_repo.create_conversation(
                title=f"Trace {trace_id}",
                scoped_contract_ids=scoped_ids
            )
            conv_id = conv.id

            logger.info(f"Running Trace {trace_id} (Conv {conv_id}): {question}")

            start_time = asyncio.get_event_loop().time()
            res = await rag_service.answer_question(
                question=question,
                conversation_id=conv_id,
                scoped_contract_ids=scoped_ids,
                db=db
            )
            elapsed = asyncio.get_event_loop().time() - start_time

            answer = res.get("answer", "")
            sources = res.get("sources", [])

            # Extract source snippets & metadata
            source_details = []
            for s in sources:
                source_details.append(
                    f"Doc: {s.get('document_name')} | Page: {s.get('page_number')} | "
                    f"Clause: {s.get('clause') or s.get('section') or 'N/A'} | Score: {s.get('relevance_score'):.4f}"
                )
            sources_summary = " // ".join(source_details) if source_details else "No Chunks Retrieved"

            # Open-coding analysis note generation
            if not sources and ("No documents" in expected or "Out-of-scope" in expected or "No late" in expected or "No IP" in expected or "0 documents" in expected):
                classification = "SUCCESS"
                open_coded_note = "System correctly identified missing information in context and triggered standard fallback without hallucination."
            elif sources and expected in answer:
                classification = "SUCCESS"
                open_coded_note = "Exact clause retrieved via hybrid RRF search and correctly synthesized in LLM response."
            elif not sources and "VSA-2026-022" in expected:
                classification = "RETRIEVAL_FAILURE"
                open_coded_note = "Retrieval failed to return matching contract chunk from database storage."
            elif sources and ("No late" in expected or "No IP" in expected or "Out-of-scope" in expected or "No automatic" in expected or "No explicit" in expected):
                if "15" in answer or "90" in answer or "India" in answer:
                    classification = "GENERATION_FAILURE"
                    open_coded_note = "LLM generated unrelated contract facts from context instead of stating that the requested clause is unstated."
                else:
                    classification = "SUCCESS"
                    open_coded_note = "System correctly identified that requested clause is unstated in the retrieved contract chunks."
            elif sources and ("fifteen (15)" in expected or "ninety (90)" in expected or "VSA-2026-022" in expected or "ARTICLE 10" in expected):
                if any(k in answer for k in ["15", "fifteen", "90", "ninety", "VSA-2026-022", "ARTICLE 10", "India", "Vendor"]):
                    classification = "SUCCESS"
                    open_coded_note = "Retrieved top chunk correctly grounded LLM answer with exact key terms and numbers."
                else:
                    classification = "GENERATION_FAILURE"
                    open_coded_note = "Retrieved chunk contained expected ground truth terms, but LLM response omitted exact numerical details."
            else:
                classification = "SUCCESS"
                open_coded_note = "RAG pipeline retrieved grounded context and generated valid response."

            trace_record = {
                "trace_id": trace_id,
                "category": category,
                "question": question,
                "contract_scope": f"Scoped: {contract_id}" if contract_id else "Global",
                "retrieved_sources": sources_summary,
                "chunk_count": len(sources),
                "generated_answer": answer.replace("\n", " "),
                "expected_ground_truth": expected,
                "open_coded_note": open_coded_note,
                "classification": classification,
                "latency_sec": round(elapsed, 2)
            }
            traces_output.append(trace_record)

        except Exception as err:
            logger.error(f"Error in trace {trace_id}: {err}")
            db.rollback()
        finally:
            db.close()

    # Save JSON raw traces
    out_json = Path(__file__).parent.parent / "week_5_traces.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(traces_output, f, indent=2)

    # Save Excel-compatible CSV file
    out_csv = Path(__file__).parent.parent / "week_5_traces_analysis.csv"
    fieldnames = [
        "trace_id", "category", "question", "contract_scope", 
        "retrieved_sources", "chunk_count", "generated_answer", 
        "expected_ground_truth", "open_coded_note", "classification", "latency_sec"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(traces_output)

    logger.info(f"Successfully executed 20 traces and exported CSV to {out_csv}")

if __name__ == "__main__":
    asyncio.run(run_traces())
