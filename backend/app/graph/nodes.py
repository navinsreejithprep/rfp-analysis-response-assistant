"""LangGraph node implementations.

Each node is a plain function: `(GraphState) -> dict` partial update. Nodes
that call an LLM are clearly marked; nodes that don't (identify_gaps, most of
final_output's aggregation, the citation/revision gating inside
validate_response) are deliberately deterministic Python — see the README's
"what's deterministic vs. LLM" section, which mirrors this file directly.
"""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config
from app.graph import prompts
from app.graph.llm import get_chat_model, structured
from app.graph.state import GraphState
from app.models.schemas import (
    CapabilityAssessment,
    CapabilityStatus,
    DraftResponse,
    ExecutiveSummary,
    FinalAnalysis,
    GapAnalysisResult,
    GapType,
    HumanReviewItem,
    MandatoryOrOptional,
    RequirementClassificationList,
    RequirementList,
    RequirementResult,
    ValidationResult,
    ValidationVerdict,
)
from app.rag import vectorstore


def _trace(state: GraphState, node: str, summary: str) -> list[dict]:
    existing = list(state.get("current_trace") or [])
    existing.append({"node": node, "summary": summary})
    return existing


# ---------------------------------------------------------------------------
# ingest_rfp — deterministic
# ---------------------------------------------------------------------------

def ingest_rfp(state: GraphState) -> dict:
    text = (state.get("rfp_text") or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text:
        return {"status": "error", "error": "RFP text is empty after parsing.", "current_node": "ingest_rfp"}
    return {
        "rfp_text": text,
        "knowledge_base_documents": vectorstore.list_indexed_documents(),
        "status": "running",
        "current_node": "ingest_rfp",
    }


# ---------------------------------------------------------------------------
# extract_requirements — LLM (structured output), chunked by section
# ---------------------------------------------------------------------------

# A single extract_requirements call asks the model to return a full
# Requirement object (6-7 fields each) per requirement it finds. On a large
# RFP with dozens of requirements, that output can exceed the model's max
# output tokens and come back truncated (invalid JSON) — this happened in
# practice at ~23k input tokens. Splitting the RFP into sections first keeps
# each call's output comfortably within the model's limit regardless of
# overall RFP size.
_MD_HEADER_RE = re.compile(r"^#{2,6}\s+.+$", re.MULTILINE)
_PLAIN_HEADER_RE = re.compile(
    r"^(?:SECTION\s+)?(\d{1,2})\.\s+[A-Z][A-Za-z0-9 /&,'-]{2,80}$", re.MULTILINE
)
MAX_SECTION_CHARS = 6000

_section_safety_splitter = RecursiveCharacterTextSplitter(
    chunk_size=MAX_SECTION_CHARS,
    chunk_overlap=300,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def split_into_sections(text: str) -> list[str]:
    """Split RFP text on its own section headings so each extraction call
    only has to cover one section's worth of requirements.

    Tries Markdown ATX headers first (``## 2. Functional Requirements``),
    then falls back to plain numbered top-level headings (``2. Technical
    Requirements`` / ``SECTION 2. ...``) for RFPs without Markdown structure.
    If neither pattern finds at least 2 headings, the RFP has no detectable
    section structure — it's kept as one chunk, but run through a
    fixed-size safety-net splitter (used for any oversized section too) so
    a single extraction call still can't be asked to cover an unbounded
    amount of text.
    """
    headers = list(_MD_HEADER_RE.finditer(text))
    if len(headers) < 2:
        headers = list(_PLAIN_HEADER_RE.finditer(text))

    if len(headers) < 2:
        sections = [text]
    else:
        sections = []
        for i, h in enumerate(headers):
            start = h.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            sections.append(text[start:end].strip())
        if headers[0].start() > 0:
            preamble = text[: headers[0].start()].strip()
            if preamble:
                sections[0] = f"{preamble}\n\n{sections[0]}"

    final_sections: list[str] = []
    for section in sections:
        if not section.strip():
            continue
        if len(section) > MAX_SECTION_CHARS:
            final_sections.extend(_section_safety_splitter.split_text(section))
        else:
            final_sections.append(section)
    return final_sections


def extract_requirements(state: GraphState) -> dict:
    llm = structured(RequirementList)
    sections = split_into_sections(state["rfp_text"])

    message_batches = [
        [
            SystemMessage(content=prompts.EXTRACT_REQUIREMENTS_SYSTEM),
            HumanMessage(
                content=(
                    "RFP SECTION (one part of a larger RFP — extract only requirements "
                    f"found in THIS excerpt):\n\n{section_text}"
                )
            ),
        ]
        for section_text in sections
    ]
    # Sections have no dependency on each other, so run all extraction calls
    # concurrently instead of one at a time — sequential calls made
    # extraction the slowest part of the pipeline once large RFPs forced
    # section-by-section calls (see split_into_sections above). `.batch()`
    # preserves input order in its results.
    section_results: list[RequirementList] = llm.batch(message_batches, config={"max_concurrency": 8})

    requirements: list[dict] = []
    for result in section_results:
        requirements.extend(r.model_dump(mode="json") for r in result.requirements)

    # Each section's LLM call restarts numbering at R-001, so renumber
    # sequentially across the combined, ordered list.
    for i, req in enumerate(requirements, start=1):
        req["requirement_id"] = f"R-{i:03d}"

    return {
        "requirements": requirements,
        "current_index": 0,
        "revision_count": 0,
        "results": [],
        "current_node": "extract_requirements",
    }


# ---------------------------------------------------------------------------
# classify_requirements — LLM (structured output), sees the full list at once
# ---------------------------------------------------------------------------

def classify_requirements(state: GraphState) -> dict:
    requirements = state["requirements"]
    if not requirements:
        return {"current_node": "classify_requirements"}

    listing = "\n".join(
        f"- id={r['requirement_id']} | current_guess={r['requirement_category']} | "
        f"text={r['original_requirement']!r} | capability={r['requested_capability']!r}"
        for r in requirements
    )
    llm = structured(RequirementClassificationList)
    result: RequirementClassificationList = llm.invoke(
        [
            SystemMessage(content=prompts.CLASSIFY_REQUIREMENTS_SYSTEM),
            HumanMessage(content=listing),
        ]
    )
    by_id = {c.requirement_id: c for c in result.classifications}
    updated = []
    for r in requirements:
        c = by_id.get(r["requirement_id"])
        if c:
            r = {**r, "requirement_category": c.requirement_category.value, "mandatory_or_optional": c.mandatory_or_optional.value}
        updated.append(r)
    return {"requirements": updated, "current_node": "classify_requirements"}


# ---------------------------------------------------------------------------
# retrieve_evidence — deterministic control flow, embeddings call under the hood
# ---------------------------------------------------------------------------

def retrieve_evidence(state: GraphState) -> dict:
    idx = state["current_index"]
    req = state["requirements"][idx]
    query = f"{req['original_requirement']} {req['requested_capability']} {req['evidence_needed']}"
    evidence = vectorstore.retrieve(query, k=config.RETRIEVAL_TOP_K)
    trace = _trace(
        state,
        "retrieve_evidence",
        f"Retrieved {len(evidence)} chunk(s) from: {', '.join(sorted({e['source_document'] for e in evidence})) or 'none'}",
    )
    return {"current_evidence": evidence, "current_trace": trace, "current_node": "retrieve_evidence"}


# ---------------------------------------------------------------------------
# assess_capability — LLM (structured output)
# ---------------------------------------------------------------------------

def _format_evidence(evidence: list[dict]) -> str:
    if not evidence:
        return "(no evidence retrieved)"
    blocks = []
    for e in evidence:
        blocks.append(f"[source_document={e['source_document']} | similarity={e['similarity_score']}]\n{e['content']}")
    return "\n\n---\n\n".join(blocks)


def assess_capability(state: GraphState) -> dict:
    idx = state["current_index"]
    req = state["requirements"][idx]
    evidence = state["current_evidence"]

    llm = structured(CapabilityAssessment)
    result: CapabilityAssessment = llm.invoke(
        [
            SystemMessage(content=prompts.ASSESS_CAPABILITY_SYSTEM),
            HumanMessage(
                content=(
                    f"REQUIREMENT (id={req['requirement_id']}): {req['original_requirement']}\n"
                    f"Requested capability: {req['requested_capability']}\n"
                    f"Evidence needed: {req['evidence_needed']}\n\n"
                    f"RETRIEVED EVIDENCE:\n{_format_evidence(evidence)}"
                )
            ),
        ]
    )
    result.requirement_id = req["requirement_id"]
    trace = _trace(state, "assess_capability", f"capability_status={result.capability_status.value}, confidence={result.confidence}")
    return {"current_assessment": result.model_dump(mode="json"), "current_trace": trace, "current_node": "assess_capability"}


# ---------------------------------------------------------------------------
# identify_gaps — deterministic (no LLM call)
# ---------------------------------------------------------------------------

def identify_gaps(state: GraphState) -> dict:
    idx = state["current_index"]
    req = state["requirements"][idx]
    assessment = state["current_assessment"]
    status = CapabilityStatus(assessment["capability_status"])
    is_mandatory = req["mandatory_or_optional"] == MandatoryOrOptional.MANDATORY.value

    if status == CapabilityStatus.FULLY_SUPPORTED:
        gap_type, severity, requires_review = GapType.NONE, "None", assessment["confidence"] < 0.5
        rationale = "Evidence fully supports this requirement." if not requires_review else \
            "Evidence appears to fully support this requirement, but model confidence was low — worth a human sanity check."
    elif status == CapabilityStatus.INSUFFICIENT_EVIDENCE:
        gap_type = GapType.EVIDENCE_GAP
        severity = "High" if is_mandatory else "Medium"
        requires_review = True
        rationale = "The knowledge base does not contain enough evidence to confirm or deny this capability — this is a documentation gap, not a proven inability."
    elif status == CapabilityStatus.NOT_SUPPORTED:
        gap_type = GapType.CAPABILITY_GAP
        severity = "High" if is_mandatory else "Medium"
        requires_review = True
        rationale = assessment["capability_gap"] or "Evidence indicates this capability is not currently in place."
    else:  # PARTIALLY_SUPPORTED
        gap_type = GapType.CAPABILITY_GAP
        severity = "Medium" if is_mandatory else "Low"
        requires_review = is_mandatory
        rationale = assessment["capability_gap"] or "Evidence shows related but incomplete capability."

    if req["mandatory_or_optional"] == MandatoryOrOptional.UNSPECIFIED.value and gap_type == GapType.NONE:
        gap_type = GapType.AMBIGUOUS_REQUIREMENT
        requires_review = True
        rationale += " Additionally, the RFP does not clearly state whether this requirement is mandatory."

    result = GapAnalysisResult(
        requirement_id=req["requirement_id"],
        gap_type=gap_type,
        severity=severity,
        requires_human_review=requires_review,
        rationale=rationale,
    )
    trace = _trace(state, "identify_gaps", f"gap_type={gap_type.value}, severity={severity}")
    return {"current_gap": result.model_dump(mode="json"), "current_trace": trace, "current_node": "identify_gaps"}


# ---------------------------------------------------------------------------
# draft_response — LLM (structured output)
# ---------------------------------------------------------------------------

def draft_response(state: GraphState) -> dict:
    idx = state["current_index"]
    req = state["requirements"][idx]
    assessment = state["current_assessment"]
    evidence = state["current_evidence"]
    prior_validation = state.get("current_validation")

    revision_note = ""
    if prior_validation:
        issues = []
        if not prior_validation["requirement_addressed"]:
            issues.append("the previous draft did not actually address the requirement")
        if not prior_validation["evidence_supported"]:
            issues.append("the previous draft made claims the evidence did not support")
        if prior_validation["unsupported_claims"]:
            issues.append(f"unsupported claims: {'; '.join(prior_validation['unsupported_claims'])}")
        if prior_validation["missing_elements"]:
            issues.append(f"missing elements: {'; '.join(prior_validation['missing_elements'])}")
        if not prior_validation["citation_present"]:
            issues.append("no source document was cited by name")
        revision_note = "\n\nTHIS IS A REVISION. Fix these specific problems from the last attempt: " + "; ".join(issues)

    llm = structured(DraftResponse)
    result: DraftResponse = llm.invoke(
        [
            SystemMessage(content=prompts.DRAFT_RESPONSE_SYSTEM),
            HumanMessage(
                content=(
                    f"REQUIREMENT (id={req['requirement_id']}): {req['original_requirement']}\n\n"
                    f"CAPABILITY ASSESSMENT:\ncapability_status={assessment['capability_status']}\n"
                    f"supporting_evidence={assessment['supporting_evidence']}\n"
                    f"source_documents={assessment['source_documents']}\n"
                    f"capability_gap={assessment['capability_gap']}\n\n"
                    f"EVIDENCE:\n{_format_evidence(evidence)}"
                    f"{revision_note}"
                )
            ),
        ]
    )
    result.requirement_id = req["requirement_id"]
    trace = _trace(state, "draft_response", f"revision={'yes' if prior_validation else 'no'}, requires_human_confirmation={result.requires_human_confirmation}")
    return {"current_response": result.model_dump(mode="json"), "current_trace": trace, "current_node": "draft_response"}


# ---------------------------------------------------------------------------
# validate_response — LLM judgment + deterministic gating
# ---------------------------------------------------------------------------

def validate_response(state: GraphState) -> dict:
    idx = state["current_index"]
    requirements = state["requirements"]
    req = requirements[idx]
    response = state["current_response"]
    evidence = state["current_evidence"]

    llm = structured(ValidationVerdict)
    verdict: ValidationVerdict = llm.invoke(
        [
            SystemMessage(content=prompts.VALIDATE_RESPONSE_SYSTEM),
            HumanMessage(
                content=(
                    f"REQUIREMENT: {req['original_requirement']}\n\n"
                    f"EVIDENCE PROVIDED TO THE DRAFTER:\n{_format_evidence(evidence)}\n\n"
                    f"DRAFTED RESPONSE:\n{response['response_text']}\n\n"
                    f"CITATIONS CLAIMED: {response['citations']}"
                )
            ),
        ]
    )

    # Deterministic: don't trust the model's self-report of whether it cited a
    # source — check the actual response text against the actual citation list.
    citation_present = bool(response["citations"]) and any(
        c.lower() in response["response_text"].lower() for c in response["citations"]
    )

    revision_required = (
        not verdict.requirement_addressed
        or not verdict.evidence_supported
        or len(verdict.unsupported_claims) > 0
        or not citation_present
        or verdict.validation_score < 0.6
    )

    validation = ValidationResult(
        requirement_id=req["requirement_id"],
        requirement_addressed=verdict.requirement_addressed,
        evidence_supported=verdict.evidence_supported,
        unsupported_claims=verdict.unsupported_claims,
        missing_elements=verdict.missing_elements,
        citation_present=citation_present,
        validation_score=verdict.validation_score,
        revision_required=revision_required,
        revision_reason=verdict.revision_reason,
    )

    revision_count = state.get("revision_count", 0)
    can_revise = revision_required and revision_count < config.MAX_REVISIONS

    trace = _trace(
        state,
        "validate_response",
        f"score={validation.validation_score}, revision_required={revision_required}, will_revise={can_revise} (attempt {revision_count + 1}/{config.MAX_REVISIONS + 1})",
    )

    if can_revise:
        return {
            "current_validation": validation.model_dump(mode="json"),
            "current_trace": trace,
            "revision_count": revision_count + 1,
            "current_node": "validate_response",
            "next_action": "revise",
        }

    # Finalize this requirement: bundle everything into a RequirementResult
    result = RequirementResult(
        requirement=req,
        evidence=state["current_evidence"],
        assessment=state["current_assessment"],
        gap=state["current_gap"],
        response=state["current_response"],
        validation=validation.model_dump(mode="json"),
        revision_count=revision_count,
        trace=trace,
    )
    results = list(state.get("results") or [])
    results.append(result.model_dump(mode="json"))

    next_index = idx + 1
    is_last = next_index >= len(requirements)

    return {
        "results": results,
        "current_validation": None,
        "current_evidence": [],
        "current_assessment": None,
        "current_gap": None,
        "current_response": None,
        "current_trace": [],
        "revision_count": 0,
        "current_index": next_index,
        "current_node": "validate_response",
        "next_action": "done" if is_last else "next_requirement",
    }


def route_after_validation(state: GraphState) -> str:
    action = state.get("next_action")
    if action == "revise":
        return "draft_response"
    if action == "next_requirement":
        return "retrieve_evidence"
    return "final_output"


# ---------------------------------------------------------------------------
# final_output — deterministic aggregation + one short LLM narrative
# ---------------------------------------------------------------------------

def final_output(state: GraphState) -> dict:
    results = state.get("results") or []
    total = len(results)

    counts = {status.value: 0 for status in CapabilityStatus}
    for r in results:
        counts[r["assessment"]["capability_status"]] += 1

    fully = counts[CapabilityStatus.FULLY_SUPPORTED.value]
    partial = counts[CapabilityStatus.PARTIALLY_SUPPORTED.value]
    not_supported = counts[CapabilityStatus.NOT_SUPPORTED.value]
    insufficient = counts[CapabilityStatus.INSUFFICIENT_EVIDENCE.value]
    coverage = round(((fully + 0.5 * partial) / total) * 100, 1) if total else 0.0

    gap_lines = [
        f"- {r['requirement']['requirement_id']} ({r['requirement']['requirement_category']}): {r['gap']['gap_type']} — {r['gap']['rationale']}"
        for r in results
        if r["gap"]["gap_type"] != GapType.NONE.value
    ]
    stats_block = (
        f"Total requirements: {total}\nFully supported: {fully}\nPartially supported: {partial}\n"
        f"Not supported: {not_supported}\nInsufficient evidence: {insufficient}\nCoverage: {coverage}%\n\n"
        f"Gaps:\n" + ("\n".join(gap_lines) if gap_lines else "None")
    )

    narrative_llm = get_chat_model()
    narrative_msg = narrative_llm.invoke(
        [
            SystemMessage(content=prompts.FINAL_NARRATIVE_SYSTEM),
            HumanMessage(content=stats_block),
        ]
    )
    narrative = narrative_msg.content if isinstance(narrative_msg.content, str) else str(narrative_msg.content)

    summary = ExecutiveSummary(
        total_requirements=total,
        fully_supported=fully,
        partially_supported=partial,
        not_supported=not_supported,
        insufficient_evidence=insufficient,
        overall_coverage_pct=coverage,
        narrative=narrative.strip(),
    )

    by_category: dict[str, list[dict]] = {}
    for r in results:
        by_category.setdefault(r["requirement"]["requirement_category"], []).append(r)

    sections = []
    for category, items in by_category.items():
        sections.append(f"## {category}\n")
        for r in items:
            sections.append(f"**{r['requirement']['requirement_id']} — {r['requirement']['original_requirement']}**\n")
            sections.append(r["response"]["response_text"] + "\n")
    consolidated_response = "\n".join(sections)

    human_review_items = []
    for r in results:
        req_id = r["requirement"]["requirement_id"]
        if r["response"]["requires_human_confirmation"]:
            human_review_items.append(
                HumanReviewItem(
                    requirement_id=req_id,
                    reason=r["response"].get("confirmation_reason") or "Response depends on a judgment call or partial/missing evidence.",
                    category="Confirmation Needed",
                )
            )
        if r["validation"]["unsupported_claims"]:
            human_review_items.append(
                HumanReviewItem(
                    requirement_id=req_id,
                    reason="; ".join(r["validation"]["unsupported_claims"]),
                    category="Unsupported Claim",
                )
            )
        if r["gap"]["gap_type"] == GapType.EVIDENCE_GAP.value:
            human_review_items.append(
                HumanReviewItem(requirement_id=req_id, reason=r["gap"]["rationale"], category="Missing Evidence")
            )
        if r["gap"]["gap_type"] == GapType.AMBIGUOUS_REQUIREMENT.value:
            human_review_items.append(
                HumanReviewItem(requirement_id=req_id, reason=r["gap"]["rationale"], category="Ambiguous Requirement")
            )

    final = FinalAnalysis(
        job_id=state["job_id"],
        executive_summary=summary,
        requirement_results=results,
        consolidated_response=consolidated_response,
        human_review_items=human_review_items,
    )

    return {"final_analysis": final.model_dump(mode="json"), "status": "completed", "current_node": "final_output"}
