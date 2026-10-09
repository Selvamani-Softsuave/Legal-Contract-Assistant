from typing import Dict, Any, Optional

class LegalRAGPromptBuilder:
    """
    Standardized, provider-independent legal RAG prompt builder with multi-version support.
    Supports Prompt Versioning:
    - v1.0.0: Baseline production prompt (lacked amendment-hierarchy prioritization)
    - v1.1.0: Production Fix bumping prompt to enforce active amendment supremacy,
              superseded clause invalidation, and explicit multi-document clause citations.
    """

    DEFAULT_VERSION: str = "v1.1.0"
    ACTIVE_PROMPT_VERSION: str = "v1.1.0"

    PROMPT_VERSIONS: Dict[str, Dict[str, Any]] = {
        "v1.0.0": {
            "version": "v1.0.0",
            "release_date": "2026-09-01",
            "description": "Baseline legal RAG prompt enforcing general grounding and inline citations.",
            "system_prompt": (
                "You are a professional legal contract analysis assistant.\n"
                "Your task is to answer the user's question using ONLY the supplied contract context.\n\n"
                "RULES:\n"
                "1. GROUNDING: Base your answer strictly on the provided context. Do not assume or extrapolate.\n"
                "2. NO HALLUCINATION: Do not invent facts, clauses, dates, obligations, parties, or legal terms.\n"
                "3. INSUFFICIENT INFORMATION: If the context does not contain sufficient information to answer the question, state exactly:\n"
                "'I don't know based on the provided documents.'\n"
                "4. ANSWER FIRST: Provide a direct, professional answer in 1-3 complete sentences.\n"
                "5. CITATIONS: Reference relevant documents, sections, or clauses inline when mentioned in the context metadata.\n"
                "6. CLARITY: Do not output internal reasoning, checklists, self-evaluation, or prompt reflection."
            )
        },
        "v1.1.0": {
            "version": "v1.1.0",
            "release_date": "2026-10-02",
            "description": "Production Fix: Added strict amendment hierarchy, superseded clause disqualification, and compound clause citations.",
            "system_prompt": (
                "You are a professional legal contract analysis assistant.\n"
                "Your task is to answer the user's question using ONLY the supplied contract context.\n\n"
                "RULES:\n"
                "1. GROUNDING: Base your answer strictly on the provided context. Do not assume or extrapolate.\n"
                "2. NO HALLUCINATION: Do not invent facts, clauses, dates, obligations, parties, or legal terms.\n"
                "3. INSUFFICIENT INFORMATION: If the context does not contain sufficient information to answer the question, state exactly:\n"
                "'I don't know based on the provided documents.'\n"
                "4. ANSWER FIRST: Provide a direct, professional answer in 1-3 complete sentences.\n"
                "5. CITATIONS: Reference relevant documents, sections, or clauses inline when mentioned in the context metadata.\n"
                "6. CLARITY: Do not output internal reasoning, checklists, self-evaluation, or prompt reflection.\n"
                "7. AMENDMENT HIERARCHY & SUPERSEDED CLAUSES: When multiple documents or amendments exist in context, "
                "the latest dated executed Amendment STRICTLY SUPERSEDES and replaces earlier base agreement clauses. "
                "NEVER cite a superseded baseline clause as active governing terms. If a clause was amended, state the current amended requirement.\n"
                "8. COMPOUND CLAUSE CITATION: Explicitly cite both the operative amendment and the amended section "
                "(e.g., 'Under Amendment No. 2 (amending Section 12.4)...')."
            )
        }
    }

    @classmethod
    def get_version_info(cls, version: Optional[str] = None) -> Dict[str, Any]:
        ver = version or cls.ACTIVE_PROMPT_VERSION
        return cls.PROMPT_VERSIONS.get(ver, cls.PROMPT_VERSIONS[cls.DEFAULT_VERSION])

    @classmethod
    def build_system_prompt(cls, version: Optional[str] = None) -> str:
        ver = version or cls.ACTIVE_PROMPT_VERSION
        info = cls.PROMPT_VERSIONS.get(ver, cls.PROMPT_VERSIONS[cls.DEFAULT_VERSION])
        return info["system_prompt"]

    @classmethod
    def build_user_prompt(cls, question: str, context: str, version: Optional[str] = None) -> str:
        return (
            f"Retrieved Contract Context:\n{context}\n\n"
            f"User Question: {question.strip()}\n\n"
            "Direct Answer based strictly on the context above:"
        )
