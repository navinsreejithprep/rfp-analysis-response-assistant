"""Hand-labeled evaluation dataset.

Expected labels were assigned by reading the synthetic knowledge base in
backend/data/knowledge_base/ directly (see the file each case points to via
expected_source_documents) — they are ground truth for THIS demo corpus, not
a claim about any real vendor. run_eval.py compares live pipeline output
against these labels; it does not invent scores.

Categories covered, per the project brief: clearly supported, partially
supported, unsupported, ambiguous, and a case with genuinely insufficient
evidence.
"""

from __future__ import annotations

from typing import Optional, TypedDict


class EvalCase(TypedDict, total=False):
    requirement_id: str
    original_requirement: str
    requirement_category: str
    mandatory_or_optional: str
    requested_capability: str
    evidence_needed: str
    expected_capability_status: Optional[str]
    expected_source_documents: list[str]
    case_type: str  # "supported" | "partial" | "unsupported" | "insufficient_evidence" | "ambiguous"


REQUIREMENT_CASES: list[EvalCase] = [
    {
        "requirement_id": "R-EVAL-01",
        "original_requirement": "The vendor shall demonstrate experience implementing AI-enabled workflow automation for document or invoice processing in a retail environment.",
        "requirement_category": "Experience/Credentials",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "AI-enabled document/invoice processing automation in retail",
        "evidence_needed": "A relevant case study with measurable outcomes",
        "expected_capability_status": "Fully Supported",
        "expected_source_documents": ["case_studies.md", "past_project_experience.md"],
        "case_type": "supported",
    },
    {
        "requirement_id": "R-EVAL-02",
        "original_requirement": "The vendor shall provide a conversational customer support assistant capable of citing source documentation for every response.",
        "requirement_category": "Functional",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "Citation-grounded conversational support assistant",
        "evidence_needed": "A case study describing a grounded, cited support assistant",
        "expected_capability_status": "Fully Supported",
        "expected_source_documents": ["case_studies.md", "ai_data_capabilities.md"],
        "case_type": "supported",
    },
    {
        "requirement_id": "R-EVAL-03",
        "original_requirement": "The vendor should describe experience with mainframe modernization, including COBOL system migration.",
        "requirement_category": "Technical",
        "mandatory_or_optional": "Optional",
        "requested_capability": "Mainframe / COBOL modernization",
        "evidence_needed": "A description of mainframe migration capability or experience",
        "expected_capability_status": "Not Supported",
        "expected_source_documents": ["technology_capabilities.md"],
        "case_type": "unsupported",
    },
    {
        "requirement_id": "R-EVAL-04",
        "original_requirement": "The vendor must provide a current, independently audited SOC 2 Type II report or ISO 27001 certificate for their own corporate environment.",
        "requirement_category": "Compliance",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "Vendor's own independently audited SOC 2 / ISO 27001 certificate",
        "evidence_needed": "A published audit certificate or attestation",
        "expected_capability_status": "Insufficient Evidence",
        "expected_source_documents": ["cybersecurity_capabilities.md", "certifications.md"],
        "case_type": "insufficient_evidence",
    },
    {
        "requirement_id": "R-EVAL-05",
        "original_requirement": "The vendor must hold FedRAMP Moderate authorization or equivalent.",
        "requirement_category": "Compliance",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "FedRAMP Moderate authorization",
        "evidence_needed": "Evidence of FedRAMP authorization",
        "expected_capability_status": "Not Supported",
        "expected_source_documents": ["cybersecurity_capabilities.md"],
        "case_type": "unsupported",
    },
    {
        "requirement_id": "R-EVAL-06",
        "original_requirement": "The vendor must describe prior experience migrating an on-premises application estate of at least 100 servers to a public cloud provider.",
        "requirement_category": "Implementation",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "Large-scale (100+ server) cloud migration experience",
        "evidence_needed": "A migration case study with server count",
        "expected_capability_status": "Partially Supported",
        "expected_source_documents": ["cloud_capabilities.md", "case_studies.md"],
        "case_type": "partial",
    },
    {
        "requirement_id": "R-EVAL-07",
        "original_requirement": "The vendor must provide 24/7/365 follow-the-sun production support with defined Severity 1 response-time SLAs.",
        "requirement_category": "Operations",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "24/7/365 follow-the-sun support",
        "evidence_needed": "A description of support hours/SLA model",
        "expected_capability_status": "Not Supported",
        "expected_source_documents": ["delivery_methodology.md"],
        "case_type": "unsupported",
    },
    {
        "requirement_id": "R-EVAL-08",
        "original_requirement": "The vendor must submit audited financial statements for the past three fiscal years as proof of financial stability.",
        "requirement_category": "Commercial",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "Audited financial statements",
        "evidence_needed": "Financial statements or bonding capacity evidence",
        "expected_capability_status": "Insufficient Evidence",
        "expected_source_documents": ["company_overview.md"],
        "case_type": "insufficient_evidence",
    },
    {
        "requirement_id": "R-EVAL-09",
        "original_requirement": "The vendor should describe their standard engagement governance model for programs exceeding $250,000 in scope.",
        "requirement_category": "Commercial",
        "mandatory_or_optional": "Optional",
        "requested_capability": "Engagement governance model",
        "evidence_needed": "A description of steering committee / governance cadence",
        "expected_capability_status": "Fully Supported",
        "expected_source_documents": ["delivery_methodology.md"],
        "case_type": "supported",
    },
    {
        "requirement_id": "R-EVAL-10",
        "original_requirement": "The vendor should describe relevant staff certifications held across their cloud, security, and AI/data practice areas.",
        "requirement_category": "Experience/Credentials",
        "mandatory_or_optional": "Optional",
        "requested_capability": "Staff certifications",
        "evidence_needed": "A list of relevant staff certifications",
        "expected_capability_status": "Fully Supported",
        "expected_source_documents": ["certifications.md", "team_credentials.md"],
        "case_type": "supported",
    },
    {
        "requirement_id": "R-EVAL-11",
        "original_requirement": "The vendor must describe prior experience delivering client-facing services in languages other than English.",
        "requirement_category": "Experience/Credentials",
        "mandatory_or_optional": "Mandatory",
        "requested_capability": "Non-English client-facing delivery experience",
        "evidence_needed": "Evidence of multilingual delivery",
        "expected_capability_status": "Not Supported",
        "expected_source_documents": ["team_credentials.md"],
        "case_type": "unsupported",
    },
    {
        "requirement_id": "R-EVAL-12",
        "original_requirement": "The vendor should ensure appropriate quality standards are maintained throughout the engagement.",
        "requirement_category": "Other",
        "mandatory_or_optional": "Unspecified",
        "requested_capability": "Unspecified quality standard",
        "evidence_needed": "Unclear — requirement does not specify a measurable standard",
        "expected_capability_status": None,
        "expected_source_documents": [],
        "case_type": "ambiguous",
    },
]


class ValidationCase(TypedDict):
    requirement_id: str
    original_requirement: str
    evidence: list[dict]
    bad_response_text: str
    bad_citations: list[str]
    expect_revision_required: bool
    reason: str


# Deliberately flawed drafts used to test whether validate_response actually
# catches problems rather than rubber-stamping. Evidence blocks are taken
# verbatim from the real knowledge base documents so the "unsupported claim"
# is genuinely unsupported by the text a reviewer would see.
VALIDATION_CASES: list[ValidationCase] = [
    {
        "requirement_id": "R-EVAL-07",
        "original_requirement": "The vendor must provide 24/7/365 follow-the-sun production support with defined Severity 1 response-time SLAs.",
        "evidence": [
            {
                "source_document": "delivery_methodology.md",
                "content": (
                    "NorthPeak offers post-go-live managed support with response-time SLAs (e.g., 4-hour "
                    "response for Severity 1 issues during business hours). NorthPeak does not currently "
                    "offer a 24/7/365 follow-the-sun support model; after-hours coverage would need to be "
                    "scoped as a custom addition."
                ),
                "similarity_score": 0.42,
            }
        ],
        "bad_response_text": (
            "NorthPeak provides full 24/7/365 follow-the-sun global production support with a dedicated "
            "network operations center, meeting all Severity 1 response-time requirements (see "
            "delivery_methodology.md)."
        ),
        "bad_citations": ["delivery_methodology.md"],
        "expect_revision_required": True,
        "reason": "Response directly contradicts the evidence, which states 24/7/365 support is NOT currently offered.",
    },
    {
        "requirement_id": "R-EVAL-04",
        "original_requirement": "The vendor must provide a current, independently audited SOC 2 Type II report or ISO 27001 certificate for their own corporate environment.",
        "evidence": [
            {
                "source_document": "certifications.md",
                "content": (
                    "Corporate-level attestations NorthPeak does NOT hold (explicitly, for this demo): no "
                    "FedRAMP authorization; no published, independently audited SOC 2 Type II or ISO 27001 "
                    "certificate for NorthPeak's own corporate environment; no CMMI appraisal on record."
                ),
                "similarity_score": 0.55,
            }
        ],
        "bad_response_text": (
            "NorthPeak holds a current, independently audited SOC 2 Type II certification for its corporate "
            "environment, satisfying this requirement in full."
        ),
        "bad_citations": [],
        "expect_revision_required": True,
        "reason": "No citation is present, and the claim directly contradicts the evidence.",
    },
]
