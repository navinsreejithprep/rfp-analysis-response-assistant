"""API-level tests. The knowledge base seeding step (which makes a real
OpenAI embeddings call) is monkeypatched to a no-op so these tests run
offline and don't require a valid API key or network access.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.rag import vectorstore


def _client(monkeypatch):
    monkeypatch.setattr(vectorstore, "seed_knowledge_base_if_empty", lambda: 0)
    return TestClient(app)


def test_health(monkeypatch):
    with _client(monkeypatch) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_analyze_rejects_unsupported_file_type(monkeypatch):
    monkeypatch.setattr(vectorstore, "list_indexed_documents", lambda: ["company_overview.md"])
    with _client(monkeypatch) as client:
        resp = client.post(
            "/api/rfp/analyze",
            files={"file": ("archive.zip", b"not a real zip", "application/zip")},
        )
        assert resp.status_code == 400


def test_analyze_rejects_when_knowledge_base_empty(monkeypatch):
    monkeypatch.setattr(vectorstore, "list_indexed_documents", lambda: [])
    with _client(monkeypatch) as client:
        resp = client.post(
            "/api/rfp/analyze",
            files={"file": ("rfp.txt", b"Some RFP text.", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Knowledge base is empty" in resp.json()["detail"]


def test_get_unknown_job_returns_404(monkeypatch):
    with _client(monkeypatch) as client:
        resp = client.get("/api/jobs/does-not-exist")
        assert resp.status_code == 404


def test_get_final_analysis_for_unknown_job_returns_404(monkeypatch):
    with _client(monkeypatch) as client:
        resp = client.get("/api/jobs/does-not-exist/final")
        assert resp.status_code == 404
