"""Integration tests for /api/samples endpoints."""

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET /api/samples
# ---------------------------------------------------------------------------


def test_list_samples_returns_all_three(client: TestClient):
    response = client.get("/api/samples")
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()["samples"]]
    assert set(ids) == {"tomato", "coal", "environment_water"}


def test_list_samples_shape(client: TestClient):
    response = client.get("/api/samples")
    sample = response.json()["samples"][0]
    assert "id" in sample
    assert "name" in sample


# ---------------------------------------------------------------------------
# GET /api/samples/{sample_id}/analyses
# ---------------------------------------------------------------------------


def test_list_analyses_tomato(client: TestClient):
    response = client.get("/api/samples/tomato/analyses")
    assert response.status_code == 200
    body = response.json()
    assert body["sample_id"] == "tomato"
    ids = [a["id"] for a in body["analyses"]]
    assert "moisture" in ids
    assert "sulfur" in ids


def test_list_analyses_unknown_sample_returns_404(client: TestClient):
    response = client.get("/api/samples/unknown_sample/analyses")
    assert response.status_code == 404


def test_list_analyses_shape(client: TestClient):
    response = client.get("/api/samples/coal/analyses")
    analysis = response.json()["analyses"][0]
    assert "id" in analysis
    assert "label" in analysis
