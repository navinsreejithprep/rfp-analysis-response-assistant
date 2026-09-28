"""Runs the compiled LangGraph pipeline for one job and streams state into the job store.

Executed as a FastAPI BackgroundTask (which runs sync callables in a
threadpool), so a slow multi-requirement analysis doesn't block the event
loop or other requests.
"""

from __future__ import annotations

from app.graph.graph import build_graph
from app.storage import jobs


def run_pipeline_job(job_id: str, rfp_text: str) -> None:
    graph = build_graph()
    jobs.update_job(job_id, status="running")

    initial_state = {
        "job_id": job_id,
        "rfp_text": rfp_text,
        "status": "running",
        "current_trace": [],
    }

    # LangGraph's default recursion_limit (25 super-steps) is sized for small
    # graphs, not a per-requirement loop: this pipeline visits ~5 nodes per
    # requirement (more with revisions), so a 19-requirement RFP alone needs
    # ~95+ steps. Set a generous ceiling instead of a count tied to one RFP.
    run_config = {"recursion_limit": 1000}

    final_state: dict = {}
    try:
        for state_snapshot in graph.stream(initial_state, config=run_config, stream_mode="values"):
            final_state = state_snapshot
            jobs.update_job(job_id, state=state_snapshot, status=state_snapshot.get("status", "running"))

        if final_state.get("status") == "error":
            jobs.update_job(job_id, status="error", error=final_state.get("error"))
        else:
            jobs.update_job(job_id, status="completed", state=final_state)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the API instead of losing it in a background thread
        jobs.update_job(job_id, status="error", error=str(exc), state=final_state)
