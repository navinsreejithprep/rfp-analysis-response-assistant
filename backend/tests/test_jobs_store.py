from app.storage import jobs


def test_create_and_get_job():
    job_id = jobs.create_job()
    job = jobs.get_job(job_id)
    assert job is not None
    assert job["status"] == "pending"
    assert job["error"] is None


def test_update_job_merges_fields():
    job_id = jobs.create_job()
    jobs.update_job(job_id, status="running", state={"current_node": "ingest_rfp"})
    job = jobs.get_job(job_id)
    assert job["status"] == "running"
    assert job["state"]["current_node"] == "ingest_rfp"


def test_get_unknown_job_returns_none():
    assert jobs.get_job("does-not-exist") is None


def test_list_jobs_returns_newest_first():
    first = jobs.create_job()
    second = jobs.create_job()
    ids = [j["job_id"] for j in jobs.list_jobs()]
    assert ids.index(second) < ids.index(first)
