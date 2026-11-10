"""
Automated Pytest Suite for Week 6 Practical — Track F (Legal Contracts).
"""

import json
import pytest
from pathlib import Path

from backend.app.evals.deterministic_assertions import (
    DeterministicAssertions,
    run_all_assertions,
)
from backend.app.evals.clause_judge import (
    ClauseJudge,
    get_disagreement_analyses,
)
from backend.app.evals.ragas_eval import RagasEvaluator


BASE_DIR = Path(__file__).parent.parent


def resolve_file(filename: str) -> Path:
    for p in [BASE_DIR / "resource" / filename, BASE_DIR / filename]:
        if p.exists():
            return p
    return BASE_DIR / "resource" / filename


def test_eval_dataset_integrity():
    """Verify eval set contains 25+ cases tagged with Week 5 taxonomy modes and 2+ regression cases."""
    dataset_file = resolve_file("eval_dataset_25.json")
    assert dataset_file.exists(), "eval_dataset_25.json must exist"

    with open(dataset_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    assert len(dataset) >= 25, f"Expected 25+ cases, got {len(dataset)}"

    valid_taxonomy_modes = {
        "NUMERICAL_DETAIL_SUMMARY_OMISSION",
        "IDENTIFIERS_AND_HEADINGS",
        "NUMERICAL_AND_TIME_TERMS",
        "LIABILITY_AND_GOVERNING_LAW",
        "MULTI_DOC_SCOPING",
        "EDGE_CASES_AND_OUT_OF_SCOPE",
        "SUPERSEDED_AMENDMENT_PRECISION",
    }

    regression_cases = []
    for item in dataset:
        assert "taxonomy_mode" in item, f"Case {item.get('id')} missing taxonomy_mode"
        assert item["taxonomy_mode"] in valid_taxonomy_modes, f"Unknown mode {item['taxonomy_mode']}"
        assert "question" in item and "generated_answer" in item
        if item.get("is_regression", False):
            regression_cases.append(item)

    assert len(regression_cases) >= 2, f"Expected at least 2 regression cases, got {len(regression_cases)}"


def test_blind_hand_labels_protocol():
    """Verify 25 hand labels exist in labels_25.json on the single binary criterion."""
    labels_file = resolve_file("labels_25.json")
    assert labels_file.exists(), "labels_25.json must exist"

    with open(labels_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["protocol"] == "BLIND_HAND_LABELING_PROTOCOL"
    assert "timestamp_created" in data
    assert data["total_cases_labeled"] >= 25

    labels = data["labels"]
    assert len(labels) >= 25

    for cid, info in labels.items():
        assert info["human_label"] in (0, 1)
        assert info["verdict_name"] in ("PASS", "FAIL")
        assert len(info["rationale"]) > 5


def test_assertion_clause_reference_exists():
    """Test deterministic check for cited clause references."""
    contract = "Section 7.2 Termination for Breach: 30 days notice required."
    
    # Valid cite
    res_valid = DeterministicAssertions.assert_clause_reference_exists(
        "As stated in Section 7.2, 30 days notice is required.", contract
    )
    assert res_valid.passed is True

    # Hallucinated cite
    res_invalid = DeterministicAssertions.assert_clause_reference_exists(
        "Under Section 9.9, payment is due immediately.", contract
    )
    assert res_invalid.passed is False
    assert "9.9" in res_invalid.details


def test_assertion_effective_date_parseable():
    """Test deterministic check for date parsing."""
    res_valid = DeterministicAssertions.assert_effective_date_parseable(
        "The agreement was signed on January 15, 2026."
    )
    assert res_valid.passed is True
    assert "2026-01-15" in res_valid.details

    res_no_date = DeterministicAssertions.assert_effective_date_parseable(
        "This agreement covers logistics services."
    )
    assert res_no_date.passed is True


def test_assertion_defined_terms_valid():
    """Test deterministic check for capitalized defined terms."""
    contract = "This Agreement is entered by Acme ('Client') and FastShip ('Vendor')."
    
    res_valid = DeterministicAssertions.assert_defined_terms_valid(
        "The 'Client' and 'Vendor' agree to terms.", contract
    )
    assert res_valid.passed is True

    res_invalid = DeterministicAssertions.assert_defined_terms_valid(
        "The 'SuperFictionalParty' will provide audit services.", contract
    )
    assert res_invalid.passed is False
    assert "SuperFictionalParty" in res_invalid.details


def test_assertion_notice_periods_numeric():
    """Test deterministic check for numeric notice periods."""
    # Valid numeric notice
    res_valid = DeterministicAssertions.assert_notice_periods_numeric(
        "Notice of termination requires ninety (90) days prior written notice."
    )
    assert res_valid.passed is True

    # Vague non-numeric notice (failure)
    res_invalid = DeterministicAssertions.assert_notice_periods_numeric(
        "Notice of termination requires reasonable notice before ending."
    )
    assert res_invalid.passed is False
    assert "reasonable notice" in res_invalid.details


@pytest.mark.asyncio
async def test_judge_agreement_delta_improvement():
    """Verify that Judge v2 few-shot calibration improves human agreement over Judge v1."""
    with open(resolve_file("eval_dataset_25.json"), "r", encoding="utf-8") as f:
        dataset = json.load(f)
    with open(resolve_file("labels_25.json"), "r", encoding="utf-8") as f:
        labels_data = json.load(f)

    hand_labels = {cid: info["human_label"] for cid, info in labels_data["labels"].items()}

    judge = ClauseJudge(base_dir=BASE_DIR)
    _, report_v1 = await judge.evaluate_dataset(dataset, hand_labels, version="v1")
    _, report_v2 = await judge.evaluate_dataset(dataset, hand_labels, version="v2")

    assert report_v1.agreement_percentage >= 70.0, f"Judge v1 baseline agreement was {report_v1.agreement_percentage}%"
    assert report_v2.agreement_percentage >= 90.0, f"Judge v2 calibrated agreement was {report_v2.agreement_percentage}%"
    assert report_v2.agreement_percentage > report_v1.agreement_percentage, "Judge v2 must improve over Judge v1"


def test_disagreement_analysis_evidence():
    """Verify that 2 real disagreements are documented and analyzed."""
    with open(resolve_file("eval_dataset_25.json"), "r", encoding="utf-8") as f:
        dataset = json.load(f)
    with open(resolve_file("labels_25.json"), "r", encoding="utf-8") as f:
        labels_data = json.load(f)

    hand_labels = {cid: info["human_label"] for cid, info in labels_data["labels"].items()}
    disagreements = get_disagreement_analyses(dataset, hand_labels)

    assert len(disagreements) >= 2
    for d in disagreements:
        assert d.case_id in ("TC-W6-002", "TC-W6-017")
        assert "Human Reviewer was right" in d.who_was_right
        assert len(d.analysis) > 20


def test_bonus_ragas_superseded_amendment():
    """Verify RAGAS evaluation identifies high faithfulness on superseded amendment."""
    with open(resolve_file("eval_dataset_25.json"), "r", encoding="utf-8") as f:
        dataset = json.load(f)

    report = RagasEvaluator.run_ragas_evaluation(dataset)
    assert report.average_faithfulness > 0.85
    assert report.trap_case_faithfulness >= 0.90
    assert report.trap_case_precision <= 0.50
