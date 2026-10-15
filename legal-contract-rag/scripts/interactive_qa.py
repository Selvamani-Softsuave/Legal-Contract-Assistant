"""
Interactive Legal Contract Q&A Tool.
Run this script to enter any prompt/question in the terminal and get instant RAG answers with citations.

Usage:
    .\\.venv\\Scripts\\python.exe scripts/interactive_qa.py
"""

import sys
import asyncio
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "shared-corpus" / "loaders"))

from scripts.evaluate_shared_corpus import SharedCorpusRAGPipeline

def main():
    contracts_dir = WORKSPACE_ROOT / "shared-corpus" / "contracts"
    print("=" * 70)
    print("  ENTERPRISE LEGAL CONTRACT RAG — INTERACTIVE CHAT")
    print("=" * 70)
    print("Loading indexed contracts from Shared Corpus...")
    pipeline = SharedCorpusRAGPipeline(contracts_dir)
    print(f"Ready! Indexed {len(pipeline.chunks)} chunks across 6 legal documents.")
    print("Type your question below (or 'exit' / 'quit' to stop).\n")

    sample_questions = [
        "What notice period is required to terminate the Northwind agreement for convenience?",
        "What is the liability cap in Section 8.3 of the Vertex Master Services Agreement?",
        "What does 'Business Day' mean under the Northwind agreement?",
        "What is the governing law of the Apex Industries agreement?"
    ]
    print("Sample questions you can try:")
    for idx, sq in enumerate(sample_questions, 1):
        print(f"  {idx}. {sq}")
    print("-" * 70)

    while True:
        try:
            query = input("\nEnter Question > ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Exiting interactive Q&A. Goodbye!")
                break

            print("\nSearching contracts and generating answer...")
            t0 = asyncio.get_event_loop().time()
            res = asyncio.run(pipeline.answer(query))
            elapsed = (asyncio.get_event_loop().time() - t0)

            print("\n" + "=" * 50 + " ANSWER " + "=" * 50)
            print(res["answer"])
            print("=" * 108)

            print(f"\n[Cited Documents & Sources ({len(res['retrieved_chunks'])} retrieved chunks)]")
            for c in res["retrieved_chunks"][:3]:
                print(f"  - Document: {c['source_doc']} | Counterparty: {c['counterparty']} | Clause: {c['clause_ref']}")
            print("-" * 70)

        except KeyboardInterrupt:
            print("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
