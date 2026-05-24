"""Integration tests for /api/experiments endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import COAL_ID, PROXIMATE_TEMPLATE_ID

_EXP_ID = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")

_VALID_BODY = {
    "exp_id": str(_EXP_ID),
    "sample_id": str(COAL_ID),
    "template_id": str(PROXIMATE_TEMPLATE_ID),
}

# State blob sent on PUT — full snapshot with worker values embedded
_STATE_WITH_VALUES = {
    "id": str(PROXIMATE_TEMPLATE_ID),
    "name": "Proximate Analysis",
    "description": "Determine moisture, ash, volatile matter, and fixed carbon",
    "workerForm": {"title": "Proximate Form", "questions": []},
    "calculations": {"result": "value * 100"},
    "template": "Result: {{result}}%",
    "crucible_mass": 1.23,
    "sample_mass": 4.56,
}


# ---------------------------------------------------------------------------
# POST /api/experiments
# ---------------------------------------------------------------------------


async def test_create_experiment_returns_201(client: AsyncClient):
    response = await client.post("/api/experiments", json=_VALID_BODY)
    assert response.status_code == 201


async def test_create_experiment_response_shape(client: AsyncClient):
    body = (await client.post("/api/experiments", json=_VALID_BODY)).json()
    assert body["exp_id"] == str(_EXP_ID)
    assert body["sample_id"] == str(COAL_ID)
    assert body["template_id"] == str(PROXIMATE_TEMPLATE_ID)
    assert body["state"]["id"] == str(PROXIMATE_TEMPLATE_ID)
    assert body["state"]["name"] == "Proximate Analysis"
    assert "created_at" in body
    assert "template" not in body
    assert "values" not in body


async def test_create_experiment_duplicate_exp_id_returns_409(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    assert (await client.post("/api/experiments", json=_VALID_BODY)).status_code == 409


async def test_create_experiment_unknown_sample_returns_404(client: AsyncClient):
    body = {**_VALID_BODY, "exp_id": str(uuid.uuid4()), "sample_id": str(uuid.uuid4())}
    assert (await client.post("/api/experiments", json=body)).status_code == 404


async def test_create_experiment_unknown_template_returns_404(client: AsyncClient):
    body = {**_VALID_BODY, "exp_id": str(uuid.uuid4()), "template_id": str(uuid.uuid4())}
    assert (await client.post("/api/experiments", json=body)).status_code == 404


# ---------------------------------------------------------------------------
# GET /api/experiments
# ---------------------------------------------------------------------------


async def test_list_experiments_returns_200(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    response = await client.get("/api/experiments")
    assert response.status_code == 200
    assert "experiments" in response.json()


async def test_list_experiments_summary_shape(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    exp = (await client.get("/api/experiments")).json()["experiments"][0]
    assert "exp_id" in exp
    assert "sample_id" in exp
    assert "template_id" in exp
    assert "created_at" in exp
    assert "state" not in exp
    assert "values" not in exp
    assert "template" not in exp


# ---------------------------------------------------------------------------
# GET /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


async def test_get_experiment_returns_full_detail(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (await client.get(f"/api/experiments/{_EXP_ID}")).json()
    assert body["exp_id"] == str(_EXP_ID)
    assert "state" in body
    assert body["state"]["id"] == str(PROXIMATE_TEMPLATE_ID)


async def test_get_experiment_unknown_returns_404(client: AsyncClient):
    assert (await client.get(f"/api/experiments/{uuid.uuid4()}")).status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


async def test_update_experiment_stores_state(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (
        await client.put(f"/api/experiments/{_EXP_ID}", json={"state": _STATE_WITH_VALUES})
    ).json()
    assert body["state"]["crucible_mass"] == 1.23
    assert body["state"]["sample_mass"] == 4.56


async def test_update_experiment_returns_updated_state(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (
        await client.put(f"/api/experiments/{_EXP_ID}", json={"state": _STATE_WITH_VALUES})
    ).json()
    assert body["state"]["id"] == str(PROXIMATE_TEMPLATE_ID)
    assert body["sample_id"] == str(COAL_ID)


async def test_update_experiment_unknown_returns_404(client: AsyncClient):
    assert (
        await client.put(f"/api/experiments/{uuid.uuid4()}", json={"state": {}})
    ).status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


async def test_delete_experiment_returns_204(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    assert (await client.delete(f"/api/experiments/{_EXP_ID}")).status_code == 204


async def test_delete_experiment_is_gone_after_delete(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    await client.delete(f"/api/experiments/{_EXP_ID}")
    assert (await client.get(f"/api/experiments/{_EXP_ID}")).status_code == 404


async def test_delete_experiment_unknown_returns_404(client: AsyncClient):
    assert (await client.delete(f"/api/experiments/{uuid.uuid4()}")).status_code == 404
