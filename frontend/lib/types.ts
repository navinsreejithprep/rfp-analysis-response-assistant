// Mirrors backend/app/models/schemas.py. Kept as plain types (not generated)
// since the two sides change together in this project; see README for the
// tradeoff (a real production system would generate this from the OpenAPI
// schema instead).

export type RequirementCategory =
  | "Functional"
  | "Technical"
  | "Security"
  | "Compliance"
  | "Implementation"
  | "Operations"
  | "Commercial"
  | "Experience/Credentials"
  | "Other";

export type MandatoryOrOptional = "Mandatory" | "Optional" | "Unspecified";

export type CapabilityStatus =
  | "Fully Supported"
  | "Partially Supported"
  | "Not Supported"
  | "Insufficient Evidence";

export type GapType =
  | "None"
  | "Evidence Gap"
  | "Capability Gap"
  | "Ambiguous Requirement";

export interface Requirement {
  requirement_id: string;
  original_requirement: string;
  requirement_category: RequirementCategory;
  mandatory_or_optional: MandatoryOrOptional;
  deadline_or_timeline: string | null;
  requested_capability: string;
  evaluation_criteria: string | null;
  evidence_needed: string;
}

export interface EvidenceChunk {
  source_document: string;
  content: string;
  similarity_score: number;
}

export interface CapabilityAssessment {
  requirement_id: string;
  capability_status: CapabilityStatus;
  supporting_evidence: string;
  source_documents: string[];
  capability_gap: string;
  recommended_action: string;
  confidence: number;
}

export interface GapAnalysisResult {
  requirement_id: string;
  gap_type: GapType;
  severity: "High" | "Medium" | "Low" | "None";
  requires_human_review: boolean;
  rationale: string;
}

export interface DraftResponse {
  requirement_id: string;
  response_text: string;
  citations: string[];
  requires_human_confirmation: boolean;
  confirmation_reason: string | null;
}

export interface ValidationResult {
  requirement_id: string;
  requirement_addressed: boolean;
  evidence_supported: boolean;
  unsupported_claims: string[];
  missing_elements: string[];
  citation_present: boolean;
  validation_score: number;
  revision_required: boolean;
  revision_reason: string | null;
}

export interface TraceEvent {
  node: string;
  summary: string;
}

export interface RequirementResult {
  requirement: Requirement;
  evidence: EvidenceChunk[];
  assessment: CapabilityAssessment;
  gap: GapAnalysisResult;
  response: DraftResponse;
  validation: ValidationResult;
  revision_count: number;
  trace: TraceEvent[];
  in_progress?: boolean;
}

export interface ExecutiveSummary {
  total_requirements: number;
  fully_supported: number;
  partially_supported: number;
  not_supported: number;
  insufficient_evidence: number;
  overall_coverage_pct: number;
  narrative: string;
}

export interface HumanReviewItem {
  requirement_id: string;
  reason: string;
  category: "Unsupported Claim" | "Missing Evidence" | "Ambiguous Requirement" | "Confirmation Needed";
}

export interface FinalAnalysis {
  job_id: string;
  executive_summary: ExecutiveSummary;
  requirement_results: RequirementResult[];
  consolidated_response: string;
  human_review_items: HumanReviewItem[];
}

export type JobStatus = "pending" | "running" | "completed" | "error";

export interface JobProgressItem {
  requirement_id: string;
  original_requirement: string;
  category: RequirementCategory;
  node_status: "pending" | "in_progress" | "completed";
  current_node?: string;
  capability_status: CapabilityStatus | null;
}

export interface JobProgress {
  job_id: string;
  status: JobStatus;
  error: string | null;
  current_node: string | null;
  total_requirements: number;
  completed_requirements: number;
  requirements: JobProgressItem[];
}

export interface EvalResults {
  generated_at: string;
  model: string;
  embedding_model: string;
  requirement_extraction: {
    expected_count: number;
    extracted_count: number;
    extraction_ratio: number;
    field_completeness_rate: number;
  };
  retrieval: {
    cases_evaluated: number;
    hit_rate: number | null;
    details: unknown[];
  };
  capability_classification: {
    cases_evaluated: number;
    accuracy: number | null;
    details: unknown[];
  };
  evidence_grounding: {
    cases_evaluated: number;
    grounding_rate: number | null;
    details: unknown[];
  };
  ambiguous_requirement_handling: Record<string, unknown>;
  response_validation: {
    cases_evaluated: number;
    recall_on_flawed_drafts: number | null;
    details: unknown[];
  };
}
