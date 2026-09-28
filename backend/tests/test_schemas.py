import pytest
from pydantic import ValidationError

from app.models.schemas import (
    CapabilityAssessment,
    CapabilityStatus,
    MandatoryOrOptional,
    Requirement,
    RequirementCategory,
)


def test_requirement_accepts_valid_data():
    req = Requirement(
        requirement_id="R-001",
        original_requirement="The vendor shall provide 24/7 support.",
        requirement_category=RequirementCategory.OPERATIONS,
        mandatory_or_optional=MandatoryOrOptional.MANDATORY,
        requested_capability="24/7 support",
        evidence_needed="Support hours documentation",
    )
    assert req.requirement_category == RequirementCategory.OPERATIONS
    assert req.deadline_or_timeline is None


def test_requirement_rejects_invalid_category():
    with pytest.raises(ValidationError):
        Requirement(
            requirement_id="R-001",
            original_requirement="text",
            requirement_category="Not A Real Category",
            mandatory_or_optional=MandatoryOrOptional.MANDATORY,
            requested_capability="x",
            evidence_needed="x",
        )


def test_capability_assessment_confidence_bounds():
    with pytest.raises(ValidationError):
        CapabilityAssessment(
            requirement_id="R-001",
            capability_status=CapabilityStatus.FULLY_SUPPORTED,
            supporting_evidence="x",
            source_documents=[],
            capability_gap="",
            recommended_action="x",
            confidence=1.5,  # out of bounds
        )
