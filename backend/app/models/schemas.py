"""Core data model for the RFP Analysis & Response Assistant.

These Pydantic models are the contract every LangGraph node reads from and
writes to. Structured LLM calls use `with_structured_output(<Model>)` against
the models below instead of parsing free-form text, so every hand-off between
nodes is validated data rather than a hopeful re-parse of a string.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RequirementCategory(str, Enum):
    FUNCTIONAL = "Functional"
    TECHNICAL = "Technical"
    SECURITY = "Security"
    COMPLIANCE = "Compliance"
    IMPLEMENTATION = "Implementation"
    OPERATIONS = "Operations"
    COMMERCIAL = "Commercial"
    EXPERIENCE_CREDENTIALS = "Experience/Credentials"
    OTHER = "Other"


class MandatoryOrOptional(str, Enum):
    MANDATORY = "Mandatory"
    OPTIONAL = "Optional"
    UNSPECIFIED = "Unspecified"


class CapabilityStatus(str, Enum):
    FULLY_SUPPORTED = "Fully Supported"
    PARTIALLY_SUPPORTED = "Partially Supported"
    NOT_SUPPORTED = "Not Supported"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class GapType(str, Enum):
    NONE = "None"
    EVIDENCE_GAP = "Evidence Gap"          # documents don't prove it, capability may still exist
    CAPABILITY_GAP = "Capability Gap"       # documents actively indicate the company cannot do this
    AMBIGUOUS_REQUIREMENT = "Ambiguous Requirement"


# ---------------------------------------------------------------------------
# 1. Requirement extraction
# ---------------------------------------------------------------------------

class Requirement(BaseModel):
    requirement_id: str = Field(description="Stable short id, e.g. R-001")
    original_requirement: str = Field(description="Verbatim or near-verbatim text of the requirement from the RFP")
    requirement_category: RequirementCategory
    mandatory_or_optional: MandatoryOrOptional
    deadline_or_timeline: Optional[str] = Field(default=None, description="Any deadline/timeline text tied to this requirement, if present")
    requested_capability: str = Field(description="Plain-language summary of the capability being asked for")
    evaluation_criteria: Optional[str] = Field(default=None, description="How the RFP says this will be scored/evaluated, if stated")
    evidence_needed: str = Field(description="What kind of evidence would prove the company can meet this requirement")


class RequirementList(BaseModel):
    requirements: list[Requirement]


class RequirementClassification(BaseModel):
    requirement_id: str
    requirement_category: RequirementCategory
    mandatory_or_optional: MandatoryOrOptional


class RequirementClassificationList(BaseModel):
    classifications: list[RequirementClassification]


# ---------------------------------------------------------------------------
# 2. Evidence retrieval
# ---------------------------------------------------------------------------

class EvidenceChunk(BaseModel):
    source_document: str
    content: str
    similarity_score: float


# ---------------------------------------------------------------------------
# 3. Capability assessment
# ---------------------------------------------------------------------------

class CapabilityAssessment(BaseModel):
    requirement_id: str
    capability_status: CapabilityStatus
    supporting_evidence: str = Field(description="Summary of what the retrieved evidence actually says, in the model's own words")
    source_documents: list[str]
    capability_gap: str = Field(description="Empty string if there is no gap")
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# 4. Gap identification (deterministic — no LLM call, see graph/nodes.py)
# ---------------------------------------------------------------------------

class GapAnalysisResult(BaseModel):
    requirement_id: str
    gap_type: GapType
    severity: str  # "High" | "Medium" | "Low" | "None"
    requires_human_review: bool
    rationale: str


# ---------------------------------------------------------------------------
# 5. Draft response generation
# ---------------------------------------------------------------------------

class DraftResponse(BaseModel):
    requirement_id: str
    response_text: str
    citations: list[str]
    requires_human_confirmation: bool
    confirmation_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# 6. Validation
# ---------------------------------------------------------------------------

class ValidationVerdict(BaseModel):
    """What the LLM judges. `citation_present` and `revision_required` are
    deliberately NOT part of this schema — they're computed deterministically
    in graph/nodes.py from data the code already has, rather than trusted to
    the model's judgment."""

    requirement_addressed: bool
    evidence_supported: bool
    unsupported_claims: list[str]
    missing_elements: list[str]
    validation_score: float = Field(ge=0.0, le=1.0)
    revision_reason: Optional[str] = None


class ValidationResult(BaseModel):
    requirement_id: str
    requirement_addressed: bool
    evidence_supported: bool
    unsupported_claims: list[str]
    missing_elements: list[str]
    citation_present: bool
    validation_score: float = Field(ge=0.0, le=1.0)
    revision_required: bool
    revision_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# 7. Per-requirement rollup + trace (used for the observability drill-down)
# ---------------------------------------------------------------------------

class TraceEvent(BaseModel):
    node: str
    summary: str


class RequirementResult(BaseModel):
    requirement: Requirement
    evidence: list[EvidenceChunk]
    assessment: CapabilityAssessment
    gap: GapAnalysisResult
    response: DraftResponse
    validation: ValidationResult
    revision_count: int
    trace: list[TraceEvent]


# ---------------------------------------------------------------------------
# 8. Final analysis package
# ---------------------------------------------------------------------------

class ExecutiveSummary(BaseModel):
    total_requirements: int
    fully_supported: int
    partially_supported: int
    not_supported: int
    insufficient_evidence: int
    overall_coverage_pct: float
    narrative: str


class HumanReviewItem(BaseModel):
    requirement_id: str
    reason: str
    category: str  # "Unsupported Claim" | "Missing Evidence" | "Ambiguous Requirement" | "Confirmation Needed"


class FinalAnalysis(BaseModel):
    job_id: str
    executive_summary: ExecutiveSummary
    requirement_results: list[RequirementResult]
    consolidated_response: str
    human_review_items: list[HumanReviewItem]
