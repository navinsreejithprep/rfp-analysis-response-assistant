"""identify_gaps is deliberately pure Python (no LLM call) — see
app/graph/nodes.py. These tests exercise its branch logic directly, with no
network access and no API key required.
"""

from app.graph.nodes import identify_gaps


def _state(mandatory_or_optional: str, capability_status: str, confidence: float = 0.9, capability_gap: str = "") -> dict:
    return {
        "current_index": 0,
        "requirements": [
            {
                "requirement_id": "R-001",
                "mandatory_or_optional": mandatory_or_optional,
            }
        ],
        "current_assessment": {
            "capability_status": capability_status,
            "confidence": confidence,
            "capability_gap": capability_gap,
        },
        "current_trace": [],
    }


def test_fully_supported_high_confidence_has_no_gap():
    result = identify_gaps(_state("Mandatory", "Fully Supported", confidence=0.95))
    gap = result["current_gap"]
    assert gap["gap_type"] == "None"
    assert gap["requires_human_review"] is False


def test_fully_supported_low_confidence_still_flagged_for_review():
    result = identify_gaps(_state("Mandatory", "Fully Supported", confidence=0.3))
    gap = result["current_gap"]
    assert gap["gap_type"] == "None"
    assert gap["requires_human_review"] is True


def test_insufficient_evidence_mandatory_is_high_severity():
    result = identify_gaps(_state("Mandatory", "Insufficient Evidence"))
    gap = result["current_gap"]
    assert gap["gap_type"] == "Evidence Gap"
    assert gap["severity"] == "High"
    assert gap["requires_human_review"] is True


def test_insufficient_evidence_optional_is_medium_severity():
    result = identify_gaps(_state("Optional", "Insufficient Evidence"))
    gap = result["current_gap"]
    assert gap["severity"] == "Medium"


def test_not_supported_is_capability_gap_not_evidence_gap():
    result = identify_gaps(_state("Mandatory", "Not Supported", capability_gap="No FedRAMP authorization."))
    gap = result["current_gap"]
    assert gap["gap_type"] == "Capability Gap"
    assert gap["severity"] == "High"
    assert "FedRAMP" in gap["rationale"]


def test_partially_supported_optional_does_not_require_review():
    result = identify_gaps(_state("Optional", "Partially Supported"))
    gap = result["current_gap"]
    assert gap["requires_human_review"] is False


def test_unspecified_mandatory_flag_marks_ambiguous_when_otherwise_clean():
    result = identify_gaps(_state("Unspecified", "Fully Supported", confidence=0.9))
    gap = result["current_gap"]
    assert gap["gap_type"] == "Ambiguous Requirement"
    assert gap["requires_human_review"] is True
