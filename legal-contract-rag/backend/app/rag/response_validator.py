import re
from typing import Optional


class ResponseValidator:
    """
    Validates and normalizes LLM outputs safely without aggressive regex that could
    accidentally truncate valid legal clauses or text.
    """

    DEFAULT_FALLBACK: str = "I don't know based on the provided documents."

    @classmethod
    def validate_and_normalize(cls, raw_content: Optional[str]) -> str:
        if not raw_content or not raw_content.strip():
            return cls.DEFAULT_FALLBACK

        cleaned = raw_content.strip()

        # Handle models wrapping response with markdown code fences
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                cleaned = "\n".join(lines[1:-1]).strip()

        # If answer explicitly has "Answer:" prefix after thinking text
        if "\nAnswer:" in cleaned or cleaned.startswith("Answer:"):
            parts = cleaned.split("Answer:")
            candidate = parts[-1].strip()
            if candidate:
                cleaned = candidate

        # Clean trailing self-evaluation bullets if present (e.g. * Grounded? Yes.)
        cleaned = re.sub(r"(\n\s*\*[^\n]+\?\s*(Yes|No)\.?)+\s*$", "", cleaned, flags=re.IGNORECASE).strip()

        # Check for model refusals / insufficient context signals
        refusal_patterns = [
            "i do not have enough information",
            "not mentioned in the context",
            "not provided in the context",
            "provided context does not contain",
            "cannot find any information",
            "no information is provided",
            "the provided documents do not mention",
        ]
        lower_cleaned = cleaned.lower()
        if any(p in lower_cleaned for p in refusal_patterns) and len(cleaned) < 150:
            return cls.DEFAULT_FALLBACK

        return cleaned if cleaned else cls.DEFAULT_FALLBACK
