"""
Week 6 Evals & Error Analysis Package for Track F (Legal Contracts).
"""
try:
    from backend.app.evals.deterministic_assertions import (
        DeterministicAssertions,
        AssertionResult,
        run_all_assertions,
    )
    from backend.app.evals.clause_judge import (
        ClauseJudge,
        JudgeResult,
        AgreementReport,
    )
    __all__ = [
        "DeterministicAssertions",
        "AssertionResult",
        "run_all_assertions",
        "ClauseJudge",
        "JudgeResult",
        "AgreementReport",
    ]
except ImportError:
    __all__ = []
