"""
Script to ingest the 6 Shared Corpus documents into the SQL Server database
and Azurite blob storage so they appear directly in the Web Application UI.
"""

import sys
import time
from pathlib import Path
import httpx

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = WORKSPACE_ROOT / "shared-corpus" / "contracts-pdf"
BASE_URL = "http://localhost:8080"

CONTRACT_GROUPS = [
    {
        "name": "Northwind Logistics MSA Suite (MSA-2026-014)",
        "contract_type": "Master Services Agreement",
        "governing_law": "IND",
        "description": "Standard Northwind Logistics Agreement suite including MSA, Amendment No. 1, Amendment No. 2, and Schedules A-D.",
        "files": [
            "MSA-2026-014_Northwind_Master_Services_Agreement.pdf",
            "AMD-2026-014-01_Northwind_Amendment_No_1.pdf",
            "AMD-2026-014-02_Northwind_Amendment_No_2.pdf",
            "SCH-2026-014_Northwind_Schedules.pdf",
        ]
    },
    {
        "name": "Vertex Retail MSA (MSA-2026-022)",
        "contract_type": "Master Services Agreement",
        "governing_law": "SGP",
        "description": "Vertex Retail Master Services Agreement governed by Singapore law and SIAC arbitration.",
        "files": [
            "MSA-2026-022_Vertex_Master_Services_Agreement.pdf"
        ]
    },
    {
        "name": "Halcyon Analytics Mutual NDA (NDA-2026-007)",
        "contract_type": "Non-Disclosure Agreement",
        "governing_law": "GBR",
        "description": "Halcyon Analytics Mutual Non-Disclosure Agreement governed by English law.",
        "files": [
            "NDA-2026-007_Mutual_Non_Disclosure_Agreement.pdf"
        ]
    }
]


def ingest_to_ui():
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    print("=" * 70)
    print("INGESTING SHARED CORPUS CONTRACTS & DOCUMENTS TO WEB UI DATABASE")
    print(f"Backend API: {BASE_URL}")
    print("=" * 70)

    # 1. Check existing contracts
    res = client.get("/api/v1/contracts")
    existing_contracts = {c["name"]: c["id"] for c in res.json()}

    for group in CONTRACT_GROUPS:
        name = group["name"]
        if name in existing_contracts:
            contract_id = existing_contracts[name]
            print(f"\n[EXISTS] Contract: '{name}' -> ID: {contract_id}")
        else:
            create_payload = {
                "name": name,
                "contract_type": group["contract_type"],
                "governing_law": group["governing_law"],
                "description": group["description"],
                "status": "Active"
            }
            c_res = client.post("/api/v1/contracts", json=create_payload)
            if c_res.status_code not in (200, 201):
                print(f"[ERROR] Failed to create contract {name}: {c_res.text}")
                continue
            contract_id = c_res.json()["id"]
            print(f"\n[CREATED] Contract: '{name}' -> ID: {contract_id}")

        # Upload files for this contract
        for fname in group["files"]:
            fpath = PDF_DIR / fname
            if not fpath.exists():
                print(f"  [WARN] File not found: {fpath}")
                continue

            print(f"  Uploading: {fname} ({fpath.stat().st_size:,} bytes)...")
            with open(fpath, "rb") as f:
                upload_res = client.post(
                    "/api/v1/documents/upload",
                    data={"contract_id": contract_id},
                    files={"file": (fname, f, "application/pdf")}
                )

            if upload_res.status_code in (200, 201, 202):
                doc_data = upload_res.json()
                doc_id = doc_data.get("documentId")
                print(f"  -> Uploaded successfully (Doc ID: {doc_id})")
            else:
                print(f"  [ERROR] Upload failed: {upload_res.status_code} - {upload_res.text}")

    print("\n" + "=" * 70)
    print("All Shared Corpus documents uploaded. Refresh your browser at http://localhost:4200/")
    print("=" * 70)


if __name__ == "__main__":
    ingest_to_ui()
