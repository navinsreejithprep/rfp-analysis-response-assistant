from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import Response

from app import config
from app.api.pipeline import run_pipeline_job
from app.parsing.document_parser import parse_document_bytes
from app.rag import vectorstore
from app.storage import jobs

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

@router.get("/knowledge-base/documents")
def list_documents():
    return {"documents": vectorstore.list_indexed_documents()}


@router.post("/knowledge-base/documents")
async def upload_documents(files: list[UploadFile]):
    added = []
    for f in files:
        content = await f.read()
        try:
            text = parse_document_bytes(f.filename, content)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        chunk_count = vectorstore.add_document(f.filename, text)
        added.append({"filename": f.filename, "chunks_indexed": chunk_count})
    return {"added": added}


# ---------------------------------------------------------------------------
# RFP analysis
# ---------------------------------------------------------------------------

@router.post("/rfp/analyze")
async def analyze_rfp(background_tasks: BackgroundTasks, file: UploadFile):
    content = await file.read()
    try:
        rfp_text = parse_document_bytes(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not vectorstore.list_indexed_documents():
        raise HTTPException(
            status_code=400,
            detail="Knowledge base is empty. Upload at least one reference document before analyzing an RFP.",
        )

    job_id = jobs.create_job()
    background_tasks.add_task(run_pipeline_job, job_id, rfp_text)
    return {"job_id": job_id}


def _progress_payload(job: dict) -> dict:
    state = job.get("state") or {}
    requirements = state.get("requirements") or []
    results = state.get("results") or []
    results_by_id = {r["requirement"]["requirement_id"]: r for r in results}
    current_index = state.get("current_index", 0)

    items = []
    for i, req in enumerate(requirements):
        req_id = req["requirement_id"]
        if req_id in results_by_id:
            r = results_by_id[req_id]
            items.append(
                {
                    "requirement_id": req_id,
                    "original_requirement": req["original_requirement"],
                    "category": req["requirement_category"],
                    "node_status": "completed",
                    "capability_status": r["assessment"]["capability_status"],
                }
            )
        elif i == current_index and job["status"] == "running":
            items.append(
                {
                    "requirement_id": req_id,
                    "original_requirement": req["original_requirement"],
                    "category": req["requirement_category"],
                    "node_status": "in_progress",
                    "current_node": state.get("current_node"),
                    "capability_status": None,
                }
            )
        else:
            items.append(
                {
                    "requirement_id": req_id,
                    "original_requirement": req["original_requirement"],
                    "category": req["requirement_category"],
                    "node_status": "pending",
                    "capability_status": None,
                }
            )

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "error": job.get("error"),
        "current_node": state.get("current_node"),
        "total_requirements": len(requirements),
        "completed_requirements": len(results),
        "requirements": items,
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _progress_payload(job)


@router.get("/jobs/{job_id}/requirements/{requirement_id}")
def get_requirement_detail(job_id: str, requirement_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    state = job.get("state") or {}
    results = state.get("results") or []
    for r in results:
        if r["requirement"]["requirement_id"] == requirement_id:
            return r

    # Not finished yet — if it's the requirement currently in flight, surface the partial trace.
    requirements = state.get("requirements") or []
    current_index = state.get("current_index", 0)
    if 0 <= current_index < len(requirements) and requirements[current_index]["requirement_id"] == requirement_id:
        return {
            "requirement": requirements[current_index],
            "evidence": state.get("current_evidence") or [],
            "assessment": state.get("current_assessment"),
            "gap": state.get("current_gap"),
            "response": state.get("current_response"),
            "validation": state.get("current_validation"),
            "revision_count": state.get("revision_count", 0),
            "trace": state.get("current_trace") or [],
            "in_progress": True,
        }

    raise HTTPException(status_code=404, detail="Requirement not found for this job.")


@router.get("/jobs/{job_id}/final")
def get_final_analysis(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Job is not completed yet (status={job['status']}).")
    state = job.get("state") or {}
    final_analysis = state.get("final_analysis")
    if not final_analysis:
        raise HTTPException(status_code=500, detail="Job completed but no final analysis was produced.")
    return final_analysis


@router.get("/jobs/{job_id}/export")
def export_final_analysis(job_id: str):
    job = jobs.get_job(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Completed job not found.")
    state = job.get("state") or {}
    final_analysis = state.get("final_analysis")
    if not final_analysis:
        raise HTTPException(status_code=500, detail="No final analysis available.")

    summary = final_analysis["executive_summary"]
    lines = [
        f"# RFP Analysis & Response Package — Job {job_id}",
        "",
        "## Executive Summary",
        f"- Total requirements: {summary['total_requirements']}",
        f"- Fully supported: {summary['fully_supported']}",
        f"- Partially supported: {summary['partially_supported']}",
        f"- Not supported: {summary['not_supported']}",
        f"- Insufficient evidence: {summary['insufficient_evidence']}",
        f"- Overall coverage: {summary['overall_coverage_pct']}%",
        "",
        summary["narrative"],
        "",
        "## Requirement Matrix",
        "",
        "| ID | Requirement | Category | Capability | Gap | Human Review |",
        "|----|-------------|----------|------------|-----|--------------|",
    ]
    for r in final_analysis["requirement_results"]:
        req = r["requirement"]
        lines.append(
            f"| {req['requirement_id']} | {req['original_requirement'][:80].replace(chr(10), ' ')} | "
            f"{req['requirement_category']} | {r['assessment']['capability_status']} | "
            f"{r['gap']['gap_type']} | {'Yes' if r['gap']['requires_human_review'] else 'No'} |"
        )

    lines += ["", "## Capability Gap Analysis", ""]
    for r in final_analysis["requirement_results"]:
        if r["gap"]["gap_type"] != "None":
            lines.append(f"- **{r['requirement']['requirement_id']}**: {r['gap']['rationale']}")

    lines += ["", "## Draft Response", "", final_analysis["consolidated_response"]]

    lines += ["", "## Human Review Required", ""]
    for item in final_analysis["human_review_items"]:
        lines.append(f"- **{item['requirement_id']}** [{item['category']}]: {item['reason']}")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="rfp_analysis_{job_id}.md"'},
    )


# ---------------------------------------------------------------------------
# Evaluation metrics (computed offline by eval/run_eval.py, served here as-is)
# ---------------------------------------------------------------------------

@router.get("/eval/results")
def get_eval_results():
    results_path = Path(config.BASE_DIR) / "eval" / "results.json"
    if not results_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No evaluation results yet. Run `python -m eval.run_eval` from the backend directory.",
        )
    return json.loads(results_path.read_text(encoding="utf-8"))
