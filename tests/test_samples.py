"""Integration tests for /api/samples endpoints."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/samples
# ---------------------------------------------------------------------------


def test_list_samples_returns_all_three():
    response = client.get("/api/samples")
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()["samples"]]
    assert set(ids) == {"tomato", "coal", "environment_water"}


def test_list_samples_shape():
    response = client.get("/api/samples")
    sample = response.json()["samples"][0]
    assert "id" in sample
    assert "name" in sample


# ---------------------------------------------------------------------------
# GET /api/samples/{sample_id}/analyses
# ---------------------------------------------------------------------------


def test_list_analyses_tomato():
    response = client.get("/api/samples/tomato/analyses")
    assert response.status_code == 200
    body = response.json()
    assert body["sample_id"] == "tomato"
    ids = [a["id"] for a in body["analyses"]]
    assert "moisture" in ids
    assert "sulfur" in ids


def test_list_analyses_unknown_sample_returns_404():
    response = client.get("/api/samples/unknown_sample/analyses")
    assert response.status_code == 404


def test_list_analyses_shape():
    response = client.get("/api/samples/coal/analyses")
    analysis = response.json()["analyses"][0]
    assert "id" in analysis
    assert "label" in analysis


# ---------------------------------------------------------------------------
# POST /api/samples/{sample_id}/analyses/form
# ---------------------------------------------------------------------------


def test_build_form_returns_requested_analyses():
    response = client.post(
        "/api/samples/tomato/analyses/form",
        json={"requested_analyses": ["moisture", "sulfur"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sample_id"] == "tomato"
    ids = [a["id"] for a in body["analyses"]]
    assert ids == ["moisture", "sulfur"]


def test_build_form_single_analysis():
    response = client.post(
        "/api/samples/coal/analyses/form",
        json={"requested_analyses": ["calorific"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["analyses"]) == 1
    assert body["analyses"][0]["id"] == "calorific"


def test_build_form_unknown_analysis_is_ignored():
    response = client.post(
        "/api/samples/tomato/analyses/form",
        json={"requested_analyses": ["moisture", "does_not_exist"]},
    )
    assert response.status_code == 200
    ids = [a["id"] for a in response.json()["analyses"]]
    assert ids == ["moisture"]


def test_build_form_empty_request_returns_empty_analyses():
    response = client.post(
        "/api/samples/tomato/analyses/form",
        json={"requested_analyses": []},
    )
    assert response.status_code == 200
    assert response.json()["analyses"] == []


def test_build_form_unknown_sample_returns_404():
    response = client.post(
        "/api/samples/unknown_sample/analyses/form",
        json={"requested_analyses": ["moisture"]},
    )
    assert response.status_code == 404


def test_build_form_analysis_template_shape():
    response = client.post(
        "/api/samples/tomato/analyses/form",
        json={"requested_analyses": ["moisture"]},
    )
    analysis = response.json()["analyses"][0]
    assert "workerForm" in analysis
    assert "calculations" in analysis
    assert "template" in analysis
    assert "questions" in analysis["workerForm"]
