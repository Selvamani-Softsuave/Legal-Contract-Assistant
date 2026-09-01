"""
Deterministic Assertions for Legal Contract Clause Answers.

Moving deterministic checks (clause references, dates, defined terms, numeric notice periods)
out of LLM prompts and into zero-cost, deterministic code assertions.
"""

import re
from typing import Dict, List, Optional, Any
from dateutil import parser as date_parser
from pydantic import BaseModel, Field


class AssertionResult(BaseModel):
    name: str
    passed: bool
    details: str
    target_value: Optional[str] = None


class DeterministicAssertions:
    """
    Zero-token deterministic validator for legal contract RAG outputs.
    Replaces LLM-as-a-judge calls for 4 strictly assertable criteria.
    """

    # Regex patterns for contract clause citations (e.g., Section 7.2, Article 10, Clause 3.1)
    CLAUSE_CITATION_PATTERN = re.compile(
        r'\b(?:Section|Article|Clause|Schedule|Paragraph|Exhibit)\s+([0-9]+(?:\.[0-9]+)*)',
        re.IGNORECASE
    )

    # Regex for notice periods and durations (e.g. 90 days, 15 business days, 12 months)
    NOTICE_PERIOD_PATTERN = re.compile(
        r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|thirty|sixty|ninety)\s*(?:\([0-9]+\))?\s*(?:business\s+)?(?:calendar\s+)?(days?|months?|years?|weeks?)\b',
        re.IGNORECASE
    )

    # Common capitalized defined terms used in commercial contracts
    KNOWN_DEFINED_TERMS = {
        "Agreement", "Client", "Vendor", "Customer", "Confidential Information",
        "Effective Date", "Services", "Deliverables", "Intellectual Property",
        "Term", "Dispute", "Force Majeure", "Party", "Parties", "Work Product",
        "Fees", "Taxes", "Applicable Law", "Indemnification", "Master Agreement",
        "Amendment", "Statement of Work", "SOW"
    }

    @classmethod
    def assert_clause_reference_exists(
        cls, answer: str, contract_text: str
    ) -> AssertionResult:
        """
        Criterion 1: Every cited clause reference (such as Section 7.2 or Article 10)
        actually exists in the contract context.
        """
        citations = cls.CLAUSE_CITATION_PATTERN.findall(answer)
        if not citations:
            return AssertionResult(
                name="clause_reference_exists",
                passed=True,
                details="No specific clause numbers cited in answer (N/A).",
                target_value="None"
            )

        missing_citations = []
        for cite in citations:
            # Check if cite number appears anywhere in contract text alongside Section/Article/Clause
            pattern = re.compile(
                rf'\b(?:Section|Article|Clause)\s+{re.escape(cite)}\b',
                re.IGNORECASE
            )
            if not pattern.search(contract_text) and cite not in contract_text:
                missing_citations.append(cite)

        if missing_citations:
            return AssertionResult(
                name="clause_reference_exists",
                passed=False,
                details=f"Cited clause(s) {missing_citations} do not exist in the contract text.",
                target_value=", ".join(missing_citations)
            )

        return AssertionResult(
            name="clause_reference_exists",
            passed=True,
            details=f"All cited clause references ({', '.join(citations)}) exist in contract context.",
            target_value=", ".join(citations)
        )

    @classmethod
    def assert_effective_date_parseable(
        cls, answer: str, contract_text: Optional[str] = None
    ) -> AssertionResult:
        """
        Criterion 2: Any effective date or execution date mentioned is present and parseable.
        """
        # Look for date patterns (e.g., January 15, 2026, 2026-01-15, 15th January 2026)
        date_pattern = re.compile(
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b',
            re.IGNORECASE
        )
        
        matches = date_pattern.findall(answer)
        if not matches:
            # If no date in answer, check if query requested a date
            if "effective date" in answer.lower() or "date" in answer.lower():
                return AssertionResult(
                    name="effective_date_parseable",
                    passed=True,
                    details="Date mentioned without specific calendar string (N/A).",
                    target_value="None"
                )
            return AssertionResult(
                name="effective_date_parseable",
                passed=True,
                details="No specific date string cited (N/A).",
                target_value="None"
            )

        parsed_dates = []
        for date_str in matches:
            try:
                dt = date_parser.parse(date_str)
                parsed_dates.append(f"{date_str} -> {dt.strftime('%Y-%m-%d')}")
            except Exception as e:
                return AssertionResult(
                    name="effective_date_parseable",
                    passed=False,
                    details=f"Failed to parse date '{date_str}': {e}",
                    target_value=date_str
                )

        return AssertionResult(
            name="effective_date_parseable",
            passed=True,
            details=f"Valid parseable dates: {', '.join(parsed_dates)}",
            target_value=", ".join(matches)
        )

    @classmethod
    def assert_defined_terms_valid(
        cls, answer: str, contract_text: str
    ) -> AssertionResult:
        """
        Criterion 3: Any capitalized defined term used appears in the contract definitions or body.
        """
        # Look for capitalized quotes or title-cased words used as defined terms
        quoted_terms = re.findall(r"['\"]([A-Z][A-Za-z0-9\s]+)['\"]", answer)
        
        # Check quoted terms
        invalid_terms = []
        for term in quoted_terms:
            term_clean = term.strip()
            if len(term_clean) > 2 and term_clean not in contract_text and term_clean not in cls.KNOWN_DEFINED_TERMS:
                invalid_terms.append(term_clean)

        if invalid_terms:
            return AssertionResult(
                name="defined_terms_valid",
                passed=False,
                details=f"Defined term(s) {invalid_terms} do not appear in contract definitions.",
                target_value=", ".join(invalid_terms)
            )

        return AssertionResult(
            name="defined_terms_valid",
            passed=True,
            details="All defined terms used in answer appear in contract definitions/preamble.",
            target_value=", ".join(quoted_terms) if quoted_terms else "None"
        )

    @classmethod
    def assert_notice_periods_numeric(cls, answer: str) -> AssertionResult:
        """
        Criterion 4: Notice-period and duration figures are numeric (e.g. 90 days, 15 business days)
        and not vague approximations ('reasonable time', 'a few weeks').
        """
        # If answer mentions notice/commitment/cure, assert it includes digits or spelled numbers
        notice_indicators = ["notice", "cure period", "commitment period", "written notice", "payable within"]
        contains_notice_query = any(ind in answer.lower() for ind in notice_indicators)
        
        if not contains_notice_query:
            return AssertionResult(
                name="notice_period_numeric",
                passed=True,
                details="No notice periods or durations mentioned in answer (N/A).",
                target_value="None"
            )

        # Check if vague approximation was used instead of exact numeric value
        vague_phrases = ["reasonable time", "reasonable notice", "a few days", "some time", "standard period"]
        for phrase in vague_phrases:
            if phrase in answer.lower():
                return AssertionResult(
                    name="notice_period_numeric",
                    passed=False,
                    details=f"Answer contains vague non-numeric phrase '{phrase}' for notice period.",
                    target_value=phrase
                )

        matches = cls.NOTICE_PERIOD_PATTERN.findall(answer)
        has_digits = bool(re.search(r'\d+', answer))

        if matches or has_digits:
            return AssertionResult(
                name="notice_period_numeric",
                passed=True,
                details=f"Notice period contains explicit numeric figures: {', '.join([' '.join(m) for m in matches]) if matches else 'digits found'}.",
                target_value=str(matches)
            )

        # If it discusses notice but lacks numbers/digits
        return AssertionResult(
            name="notice_period_numeric",
            passed=False,
            details="Notice period mentioned but lacks explicit numeric digit or quantity.",
            target_value="Missing numeric figure"
        )


def run_all_assertions(
    answer: str,
    contract_text: str = ""
) -> Dict[str, AssertionResult]:
    """
    Runs all 4 deterministic assertions on a generated answer.
    """
    return {
        "clause_reference_exists": DeterministicAssertions.assert_clause_reference_exists(answer, contract_text),
        "effective_date_parseable": DeterministicAssertions.assert_effective_date_parseable(answer, contract_text),
        "defined_terms_valid": DeterministicAssertions.assert_defined_terms_valid(answer, contract_text),
        "notice_period_numeric": DeterministicAssertions.assert_notice_periods_numeric(answer),
    }
