"""Integration tests for /api/experiments endpoints."""

from fastapi.testclient import TestClient

_VALID_BODY = {"sample_id": "tomato", "requested_analyses": ["moisture", "sulfur"]}


# ---------------------------------------------------------------------------
# POST /api/experiments
# ---------------------------------------------------------------------------


def test_create_experiment_returns_201(client: TestClient):
    response = client.post("/api/experiments", json=_VALID_BODY)
    assert response.status_code == 201


def test_create_experiment_response_shape(client: TestClient):
    body = client.post("/api/experiments", json=_VALID_BODY).json()
    assert "exp_id" in body
    assert body["sample_id"] == "tomato"
    assert set(body["requested_analyses"]) == {"moisture", "sulfur"}
    assert "form" in body
    assert "created_at" in body


def test_create_experiment_form_contains_templates(client: TestClient):
    ids = [a["id"] for a in client.post("/api/experiments", json=_VALID_BODY).json()["form"]]
    assert "moisture" in ids
    assert "sulfur" in ids


def test_create_experiment_unknown_sample_returns_404(client: TestClient):
    response = client.post("/api/experiments", json={"sample_id": "unknown", "requested_analyses": ["moisture"]})
    assert response.status_code == 404


def test_create_experiment_unknown_analysis_ignored(client: TestClient):
    response = client.post("/api/experiments", json={"sample_id": "tomato", "requested_analyses": ["moisture", "nope"]})
    assert response.status_code == 201
    assert [a["id"] for a in response.json()["form"]] == ["moisture"]


# ---------------------------------------------------------------------------
# GET /api/experiments
# ---------------------------------------------------------------------------


def test_list_experiments_returns_200(client: TestClient):
    client.post("/api/experiments", json=_VALID_BODY)
    response = client.get("/api/experiments")
    assert response.status_code == 200
    assert "experiments" in response.json()


def test_list_experiments_summary_has_no_form(client: TestClient):
    client.post("/api/experiments", json=_VALID_BODY)
    exp = client.get("/api/experiments").json()["experiments"][0]
    assert "exp_id" in exp
    assert "sample_id" in exp
    assert "created_at" in exp
    assert "form" not in exp


# ---------------------------------------------------------------------------
# GET /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


def test_get_experiment_returns_full_detail(client: TestClient):
    exp_id = client.post("/api/experiments", json=_VALID_BODY).json()["exp_id"]
    body = client.get(f"/api/experiments/{exp_id}").json()
    assert body["exp_id"] == exp_id
    assert len(body["form"]) == 2


def test_get_experiment_unknown_returns_404(client: TestClient):
    assert client.get("/api/experiments/does-not-exist").status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


def test_update_experiment_changes_analyses(client: TestClient):
    exp_id = client.post("/api/experiments", json=_VALID_BODY).json()["exp_id"]
    body = client.put(
        f"/api/experiments/{exp_id}",
        json={"sample_id": "tomato", "requested_analyses": ["moisture"]},
    ).json()
    assert body["requested_analyses"] == ["moisture"]
    assert len(body["form"]) == 1


def test_update_experiment_unknown_returns_404(client: TestClient):
    assert client.put("/api/experiments/does-not-exist", json=_VALID_BODY).status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


def test_delete_experiment_returns_204(client: TestClient):
    exp_id = client.post("/api/experiments", json=_VALID_BODY).json()["exp_id"]
    assert client.delete(f"/api/experiments/{exp_id}").status_code == 204


def test_delete_experiment_is_gone_after_delete(client: TestClient):
    exp_id = client.post("/api/experiments", json=_VALID_BODY).json()["exp_id"]
    client.delete(f"/api/experiments/{exp_id}")
    assert client.get(f"/api/experiments/{exp_id}").status_code == 404


def test_delete_experiment_unknown_returns_404(client: TestClient):
    assert client.delete("/api/experiments/does-not-exist").status_code == 404
