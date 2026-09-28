"""Evaluation harness.

Run from the backend/ directory:

    python -m eval.run_eval

This calls the SAME node functions the live app uses (app/graph/nodes.py)
against the hand-labeled cases in eval/dataset.py, and writes real,
computed metrics to eval/results.json. It makes real OpenAI API calls and
costs a small amount of money to run — nothing here is mocked or faked.

What it measures, mapped to project requirements:
  - requirement extraction quality  -> extract_requirements() vs. a manually
    counted requirement total in the sample RFP
  - retrieval quality                -> vectorstore.retrieve() hit-rate against
    hand-labeled expected source documents
  - capability classification         -> assess_capability() vs. hand-labeled
    expected capability_status
  - evidence grounding                -> whether draft_response() citations are
    a subset of the evidence actually retrieved
  - response validation               -> validate_response() recall on
    deliberately flawed, hand-written drafts (does it actually catch them?)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.graph import nodes
from app.rag import vectorstore
from eval.dataset import REQUIREMENT_CASES, VALIDATION_CASES

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"
SAMPLE_RFP_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_rfp" / "sample_rfp.md"

# Manually counted requirement statements in sample_rfp.md: the 19 numbered
# items in sections 2-8, plus the response-deadline commitment in the header
# ("Proposals must be submitted within 30 days...") — a genuine requirement
# that's easy to undercount if you only look at the numbered body items.
EXPECTED_RFP_REQUIREMENT_COUNT = 20

REQUIRED_REQUIREMENT_FIELDS = [
    "requirement_id",
    "original_requirement",
    "requirement_category",
    "mandatory_or_optional",
    "requested_capability",
    "evidence_needed",
]


def _case_to_requirement_dict(case: dict) -> dict:
    return {
        "requirement_id": case["requirement_id"],
        "original_requirement": case["original_requirement"],
        "requirement_category": case["requirement_category"],
        "mandatory_or_optional": case["mandatory_or_optional"],
        "deadline_or_timeline": None,
        "requested_capability": case["requested_capability"],
        "evaluation_criteria": None,
        "evidence_needed": case["evidence_needed"],
    }


def eval_requirement_extraction() -> dict:
    text = SAMPLE_RFP_PATH.read_text(encoding="utf-8")
    # Calls the same node the live app uses (including its section-chunking),
    # not a re-implementation of the extraction call.
    result = nodes.extract_requirements({"rfp_text": text})
    extracted = result["requirements"]
    complete = sum(
        1 for r in extracted if all(str(r.get(f, "")).strip() for f in REQUIRED_REQUIREMENT_FIELDS)
    )
    return {
        "expected_count": EXPECTED_RFP_REQUIREMENT_COUNT,
        "extracted_count": len(extracted),
        "extraction_ratio": round(len(extracted) / EXPECTED_RFP_REQUIREMENT_COUNT, 3),
        "field_completeness_rate": round(complete / len(extracted), 3) if extracted else 0.0,
    }


def eval_pipeline_stages() -> tuple[dict, dict, dict, dict]:
    retrieval_details = []
    classification_details = []
    grounding_details = []
    ambiguous_detail = None

    retrieval_hits = 0
    retrieval_scored = 0
    classification_correct = 0
    classification_scored = 0
    grounding_ok = 0
    grounding_scored = 0

    for case in REQUIREMENT_CASES:
        req = _case_to_requirement_dict(case)
        state = {"requirements": [req], "current_index": 0, "current_trace": []}

        state.update(nodes.retrieve_evidence(state))
        retrieved_sources = sorted({e["source_document"] for e in state["current_evidence"]})

        if case["expected_source_documents"]:
            retrieval_scored += 1
            hit = any(src in retrieved_sources for src in case["expected_source_documents"])
            retrieval_hits += int(hit)
            retrieval_details.append(
                {"requirement_id": case["requirement_id"], "expected": case["expected_source_documents"], "retrieved": retrieved_sources, "hit": hit}
            )

        state.update(nodes.assess_capability(state))
        predicted_status = state["current_assessment"]["capability_status"]

        state.update(nodes.identify_gaps(state))

        if case["case_type"] == "ambiguous":
            ambiguous_detail = {
                "requirement_id": case["requirement_id"],
                "predicted_capability_status": predicted_status,
                "gap_type": state["current_gap"]["gap_type"],
                "requires_human_review": state["current_gap"]["requires_human_review"],
                "handled_as_expected": bool(state["current_gap"]["requires_human_review"]),
            }
        else:
            classification_scored += 1
            correct = predicted_status == case["expected_capability_status"]
            classification_correct += int(correct)
            classification_details.append(
                {
                    "requirement_id": case["requirement_id"],
                    "expected": case["expected_capability_status"],
                    "predicted": predicted_status,
                    "correct": correct,
                }
            )

        state["current_validation"] = None
        state.update(nodes.draft_response(state))
        response = state["current_response"]
        evidence_sources = {e["source_document"] for e in state["current_evidence"]}
        citations = response.get("citations") or []
        grounded = all(c in evidence_sources for c in citations) if citations else False
        grounding_scored += 1
        grounding_ok += int(grounded)
        grounding_details.append(
            {
                "requirement_id": case["requirement_id"],
                "citations": citations,
                "available_evidence_sources": sorted(evidence_sources),
                "fully_grounded": grounded,
            }
        )

    retrieval = {
        "cases_evaluated": retrieval_scored,
        "hit_rate": round(retrieval_hits / retrieval_scored, 3) if retrieval_scored else None,
        "details": retrieval_details,
    }
    classification = {
        "cases_evaluated": classification_scored,
        "accuracy": round(classification_correct / classification_scored, 3) if classification_scored else None,
        "details": classification_details,
    }
    grounding = {
        "cases_evaluated": grounding_scored,
        "grounding_rate": round(grounding_ok / grounding_scored, 3) if grounding_scored else None,
        "details": grounding_details,
    }
    ambiguous = ambiguous_detail or {}
    return retrieval, classification, grounding, ambiguous


def eval_response_validation() -> dict:
    details = []
    caught = 0
    for case in VALIDATION_CASES:
        state = {
            "requirements": [{"requirement_id": case["requirement_id"], "original_requirement": case["original_requirement"]}],
            "current_index": 0,
            "current_evidence": case["evidence"],
            "current_response": {
                "requirement_id": case["requirement_id"],
                "response_text": case["bad_response_text"],
                "citations": case["bad_citations"],
                "requires_human_confirmation": False,
                "confirmation_reason": None,
            },
            "current_assessment": {"requirement_id": case["requirement_id"], "capability_status": "Not Supported", "supporting_evidence": "", "source_documents": [], "capability_gap": "", "recommended_action": "", "confidence": 0.5},
            "current_gap": {"requirement_id": case["requirement_id"], "gap_type": "Capability Gap", "severity": "High", "requires_human_review": True, "rationale": ""},
            "current_trace": [],
            "revision_count": 0,
        }
        result = nodes.validate_response(state)
        validation = result.get("current_validation") or (result.get("results") or [{}])[0].get("validation")
        revision_required = bool(validation and validation.get("revision_required"))
        details.append(
            {
                "requirement_id": case["requirement_id"],
                "reason_for_flaw": case["reason"],
                "expected_revision_required": case["expect_revision_required"],
                "actual_revision_required": revision_required,
                "correctly_caught": revision_required == case["expect_revision_required"],
            }
        )
        caught += int(revision_required == case["expect_revision_required"])

    return {
        "cases_evaluated": len(VALIDATION_CASES),
        "recall_on_flawed_drafts": round(caught / len(VALIDATION_CASES), 3) if VALIDATION_CASES else None,
        "details": details,
    }


def main() -> None:
    print("Seeding knowledge base if needed...")
    vectorstore.seed_knowledge_base_if_empty()

    print("Evaluating requirement extraction on sample_rfp.md...")
    extraction = eval_requirement_extraction()

    print("Evaluating retrieval, classification, and grounding on hand-labeled cases...")
    retrieval, classification, grounding, ambiguous = eval_pipeline_stages()

    print("Evaluating response validation on deliberately flawed drafts...")
    validation = eval_response_validation()

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": config.OPENAI_CHAT_MODEL,
        "embedding_model": config.OPENAI_EMBEDDING_MODEL,
        "requirement_extraction": extraction,
        "retrieval": retrieval,
        "capability_classification": classification,
        "evidence_grounding": grounding,
        "ambiguous_requirement_handling": ambiguous,
        "response_validation": validation,
    }

    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {RESULTS_PATH}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
