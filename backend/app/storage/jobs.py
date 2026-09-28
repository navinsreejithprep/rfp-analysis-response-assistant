"""In-memory job store.

This is a portfolio-scope choice, not an oversight: a single-process dict is
enough to demonstrate the workflow end to end, and swapping it for a
Postgres-backed store later only touches this file (see README "Future
improvements"). Jobs do not survive a server restart.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

_JOBS: dict[str, dict[str, Any]] = {}
_sequence = 0


def create_job() -> str:
    global _sequence
    _sequence += 1
    job_id = uuid.uuid4().hex[:10]
    _JOBS[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": time.time(),
        "updated_at": time.time(),
        "sequence": _sequence,
        "state": {},
        "error": None,
    }
    return job_id


def update_job(job_id: str, **kwargs: Any) -> None:
    if job_id not in _JOBS:
        return
    _JOBS[job_id].update(kwargs)
    _JOBS[job_id]["updated_at"] = time.time()


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    return _JOBS.get(job_id)


def list_jobs() -> list[dict[str, Any]]:
    return sorted(_JOBS.values(), key=lambda j: j["sequence"], reverse=True)
