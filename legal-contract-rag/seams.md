# Integration Seams Record (Tuesday Unedited Seam List)
**Project**: Soft Suave Enterprise Legal Contract Review Assistant  
**Variant**: Track F — Legal Contract Assistant (Week 12 Capstone)  
**Date**: Tuesday, 13 October 2026 (Logged & Maintained Through Integration Defense)  

---

## 1. Executive Summary

This integration seams record tracks every architectural, protocol, data, and behavioral boundary encountered while integrating eleven weeks of independent components into a unified, stranger-executable system behind `run_capstone.py`.

In accordance with Capstone Variant F requirements, this document preserves the unedited Tuesday seam inventory, tagged with explicit statuses:
- `[FIXED]`: Seam resolved and verified by automated regression test suites.
- `[ACCEPTED]`: Seam acknowledged as an intentional design trade-off, bounded by guardrails or fail-safes.
- `[RAN-OUT-OF-TIME]`: Seam deferred to the post-capstone production backlog with explicit containment.

---

## 2. Component Integration Seams Inventory

### Seam 1: Ingestion & Document Loader -> Multi-Document Indexing
- **Location**: `backend/app/services/document_service.py` <-> `shared-corpus/loaders/document_loader.py`
- **Issue**: Standard text extractors split documents arbitrarily without capturing contract hierarchy or mandatory legal metadata. Scanned PDF amendments introduced OCR noise (4.2% character error rate) and broken markdown tables.
- **Tuesday Analysis**: Multi-contract queries confused base MSAs with subsequent amendments when chunks lacked counterparty names, effective dates, and controlling document tags.
- **Status**: `[FIXED]`
- **Resolution**: Implemented `SharedCorpusChunker` enforcing all 5 mandatory metadata fields (`source_doc`, `counterparty`, `effective_date`, `doc_type`, `clause_ref`) and structured table header preservation. Validated in `tests/test_chunking.py` and `scripts/evaluate_shared_corpus.py`.

---

### Seam 2: Hybrid Retriever (BM25 + Semantic) -> Amendment Precedence Engine
- **Location**: `backend/app/services/rag_service.py` <-> `backend/app/domain/shared_corpus_knowledge.py`
- **Issue**: Keyword search (BM25) and cosine vector similarity ranked older, high-keyword-density base agreement clauses higher than concise amending instruments. For example, Northwind Section 8.3 ($2M cap) outranked Amendment No. 2 Section 2.1 ($5M cap).
- **Tuesday Analysis**: Semantic search alone is temporal-blind; embeddings encode semantic similarity, not legal supersession hierarchy.
- **Status**: `[FIXED]`
- **Resolution**: Integrated reciprocal rank fusion (RRF) with temporal amendment weighting:
  1. Base agreements carry amendment relocation pointers.
  2. Amendment instruments (`AMD-2026-014-02`) carry `controlling_document=True` metadata boosts.
  3. `get_clause` automatically injects `[AMENDMENT ALERT: SUPERSEDED PROVISION]` warning with pointers to current controlling terms. Validated in `tests/test_week12_capstone.py::test_amendment_supersession_resolution`.

---

### Seam 3: Decoupled Agent Host -> Model Context Protocol (MCP) Server
- **Location**: `backend/app/agent/mcp_agent.py` <-> `backend/app/mcp/servers/{clause_server,repo_server}.py`
- **Issue**: Handshake between JSON-RPC 2.0 client and server failed when tool arguments used inconsistent naming (e.g. `contract_id` vs `doc_id`, `section_number` vs `clause_number`).
- **Tuesday Analysis**: MCP specification mandates JSON-RPC 2.0 protocol schemas (`protocolVersion: 2024-11-05`). Hardcoded tool definitions in the agent broke zero-code extensibility.
- **Status**: `[FIXED]`
- **Resolution**: Standardized tool schemas across `get_clause`, `get_definitions`, `get_contract_metadata`, and `get_amendment_chain`. `MCPAgentHost` and `run_capstone.py` discover tools dynamically at startup via `MCPClientManager.list_tools()`. Validated in `tests/test_week9_mcp.py` and `tests/test_week12_capstone.py::test_runtime_mcp_tool_discovery`.

---

### Seam 4: Primary LLM Provider -> Secondary / Mock Fallback Routing
- **Location**: `backend/app/llm/factory.py` <-> `backend/app/llm/providers/`
- **Issue**: Network timeouts or rate limits (TPM throttle on Gemini/OpenRouter) caused unhandled exceptions, breaking long evaluation runs or interactive CLI sessions.
- **Tuesday Analysis**: System must gracefully degrade without crashing or outputting raw HTTP stack traces to legal users.
- **Status**: `[FIXED]`
- **Resolution**: Implemented exponential backoff retry loop (3 attempts) with transparent fallback to local provider and deterministic domain knowledge synthesis. Validated in `tests/test_llm_providers.py` and `tests/test_week11_production.py`.

---

### Seam 5: Agent Synthesis Output -> Legal Advice Refusal Guardrail
- **Location**: `run_capstone.py::LegalAdviceGuardrail` <-> User Interface
- **Issue**: Standard LLM prompts tended to be conversational and helpful, frequently declaring negotiated liability terms or termination windows "standard practice" or "acceptable for IT contracts".
- **Tuesday Analysis**: In legal tech, declaring a clause "standard" constitutes unauthorized practice of law and misleads non-legal corporate users into signing unfavorable commercial terms.
- **Status**: `[FIXED]`
- **Resolution**: Built deterministic regex interceptor in `LegalAdviceGuardrail`. If user asks whether a clause is "standard", "acceptable", or "safe to sign", output is sanitized and prepended with mandatory counsel referral notice:
  `"LEGAL ADVICE DISCLAIMER & COUNSEL REFERRAL: The Legal Contract Assistant is an AI information retrieval system, not a licensed legal practitioner..."` Validated in `tests/test_week12_capstone.py::test_legal_advice_refusal_guardrail_triggers`.

---

### Seam 6: Citation Generation -> Citation Integrity Validator
- **Location**: `backend/app/agent/mcp_agent.py` <-> `run_capstone.py::CitationValidator`
- **Issue**: Agent outputs frequently hallucinated clause numbers or omitted source document identifiers when summarizing across multiple agreements.
- **Tuesday Analysis**: Legal users cannot trust outputs without exact verification vectors: `clause_ref`, `source_doc`, and `effective_date`.
- **Status**: `[FIXED]`
- **Resolution**: Enforced strict tool output headers formatting:
  `[CITATION: clause_ref='<ref>', source_doc='<doc>', effective_date='<date>']`
  `CitationValidator.validate_citations_present()` inspects every generated answer and logs compliance status in execution trace. Validated in `tests/test_week12_capstone.py::test_mandatory_citation_formatting`.

---

### Seam 7: Local ChromaDB Vector Store -> Windows File Locking & Pytest Multi-Processing
- **Location**: `.pytest_cache/` & `chroma_data/` on Windows 11 NTFS
- **Issue**: Running pytest under Windows failed with `WinError 5: Access is denied` due to SQLite `.lock` files and read-only cache attributes.
- **Tuesday Analysis**: External graders running on Windows will experience broken test runs if cache directory or path separators are not localized.
- **Status**: `[FIXED]`
- **Resolution**: Isolated pytest cache to `-o cache_dir=.pytest_cache_local`, passed explicit forward-slash paths, and configured `sys.stdout.reconfigure(encoding="utf-8")` to eliminate cp1252 console crashes.

---

### Seam 8: Execution Tracing -> Cost & Latency Attribution
- **Location**: `backend/app/mcp/wire_tracer.py` <-> `cost_by_stage.md`
- **Issue**: Distributed MCP calls between agent host and servers ran without unified correlation IDs, making it impossible to attribute per-query costs and stage-by-stage latencies.
- **Tuesday Analysis**: Production defense requires proving unit economics ($0.000299/query) and identifying exactly which stage breaks at 10x concurrency.
- **Status**: `[FIXED]`
- **Resolution**: Added unified `trace_id` injection across agent thoughts, JSON-RPC requests, and metrics reporting. Validated in `run_capstone.py` and `tests/test_week11_production.py`.

---

### Seam 9: Cross-Jurisdictional Statutory Conflicts (Choice of Law)
- **Location**: `backend/app/domain/shared_corpus_knowledge.py` (India vs Singapore vs UK)
- **Issue**: When analyzing arbitration or dispute resolution across Vertex (SIAC Singapore) and Northwind (Chennai India), the model occasionally blended Singapore International Arbitration Act concepts with Indian Arbitration & Conciliation Act provisions.
- **Tuesday Analysis**: Deep statutory interplay across multi-jurisdictional private international law is out of scope for a contract retrieval system; contracts must be answered strictly on their express terms.
- **Status**: `[ACCEPTED]`
- **Trade-off & Guardrail**: The system operates strictly as a document-grounded assistant, refusing to hypothesize external statutory interpretations and citing express contractual clauses (`MSA-2026-022 Section 15.1` vs `MSA-2026-014 Section 14.1`).

---

### Seam 10: Multi-Tier Nested Addenda Chains (>3 Indirection Levels)
- **Location**: `backend/app/mcp/servers/repo_server.py::get_amendment_chain`
- **Issue**: When an agreement has an amendment that amends a schedule that references a side-letter with a cross-waiver, linear BFS search requires multi-hop graph resolution.
- **Tuesday Analysis**: All shared corpus agreements (Northwind, Vertex, Halcyon) have at most 2 active amendments and 5 schedules. Building a full graph database engine would exceed project timeline.
- **Status**: `[RAN-OUT-OF-TIME]`
- **Containment & Mitigation**: Currently bounded by 2-level amendment depth traversal (`base -> amendment -> controlling amendment`), covering 100% of the shared corpus. Multi-hop recursive graph traversal is logged in the Phase 2 production roadmap (`PRD-W12-004`).

---

## 3. Seam Status Summary Table

| Seam ID | Subsystem Seam | Type | Status | Verification Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Ingestion -> Multi-Document Indexing | Data | `[FIXED]` | `tests/test_chunking.py` |
| **S-02** | Retriever -> Amendment Precedence | Logic | `[FIXED]` | `tests/test_week12_capstone.py` |
| **S-03** | Agent Host -> MCP Protocol | Protocol | `[FIXED]` | `tests/test_week9_mcp.py` |
| **S-04** | LLM Provider -> Fallback Matrix | Network | `[FIXED]` | `tests/test_llm_providers.py` |
| **S-05** | Agent Output -> Legal Refusal Guardrail | Safety | `[FIXED]` | `run_capstone.py` |
| **S-06** | Citation -> Citation Integrity Validator | Grounding | `[FIXED]` | `run_capstone.py` |
| **S-07** | Windows OS -> ChromaDB / Pytest Cache | Platform | `[FIXED]` | `pytest -o cache_dir=.pytest_cache_local` |
| **S-08** | Traceability -> Cost / Latency Metrics | Observability | `[FIXED]` | `cost_by_stage.md` |
| **S-09** | Cross-Jurisdiction Statutory Conflict | Legal Domain | `[ACCEPTED]` | Express clause boundary disclaimer |
| **S-10** | Multi-Tier Nested Addenda (>3 hops) | Scale/Graph | `[RAN-OUT-OF-TIME]` | 2-level traversal bounded; backlog PRD-W12-004 |

---
**Maintained by**: Soft Suave AI League Engineering Team  
**Defense Review**: Week 12 Capstone Variant F
