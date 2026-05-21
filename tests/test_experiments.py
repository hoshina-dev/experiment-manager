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
    assert body["template"]["id"] == str(PROXIMATE_TEMPLATE_ID)
    assert body["template"]["name"] == "Proximate Analysis"
    assert "values" in body
    assert "created_at" in body


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


async def test_list_experiments_summary_has_no_values(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    exp = (await client.get("/api/experiments")).json()["experiments"][0]
    assert "exp_id" in exp
    assert "sample_id" in exp
    assert "template_id" in exp
    assert "created_at" in exp
    assert "values" not in exp
    assert "template" not in exp


# ---------------------------------------------------------------------------
# GET /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


async def test_get_experiment_returns_full_detail(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (await client.get(f"/api/experiments/{_EXP_ID}")).json()
    assert body["exp_id"] == str(_EXP_ID)
    assert "template" in body
    assert "values" in body


async def test_get_experiment_unknown_returns_404(client: AsyncClient):
    assert (await client.get(f"/api/experiments/{uuid.uuid4()}")).status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/experiments/{exp_id}
# ---------------------------------------------------------------------------


async def test_update_experiment_stores_values(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    values = {"crucible_mass": 1.23, "sample_mass": 4.56}
    body = (
        await client.put(f"/api/experiments/{_EXP_ID}", json={"values": values})
    ).json()
    assert body["values"] == values


async def test_update_experiment_preserves_template(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (
        await client.put(f"/api/experiments/{_EXP_ID}", json={"values": {}})
    ).json()
    assert body["template"]["id"] == str(PROXIMATE_TEMPLATE_ID)


async def test_update_experiment_unknown_returns_404(client: AsyncClient):
    assert (
        await client.put(f"/api/experiments/{uuid.uuid4()}", json={"values": {}})
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
