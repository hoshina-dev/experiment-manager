"""Integration tests for POST /api/experiments/{exp_id}/calculate."""

import uuid

from httpx import AsyncClient

from tests.conftest import COAL_ID, PROXIMATE_TEMPLATE_ID

_EXP_ID = uuid.UUID("eeeeeeee-0000-0000-0000-000000000099")
_EXP_ID_2 = uuid.UUID("eeeeeeee-0000-0000-0000-000000000098")

_CREATE_BODY = {
    "exp_id": str(_EXP_ID),
    "sample_id": str(COAL_ID),
    "lineage_id": str(PROXIMATE_TEMPLATE_ID),
}


async def test_calculate_returns_200_with_results(client: AsyncClient):
    await client.post("/api/experiments", json=_CREATE_BODY)
    await client.put(
        f"/api/experiments/{_EXP_ID}",
        json={
            "clientForm": {"name": "Client", "questions": []},
            "labForm": {"name": "Form", "questions": []},
            "calculations": {
                "result": {"formula": "values['value'] * 100", "result": ""},
            },
            "values": {"value": 5},
        },
    )
    response = await client.post(f"/api/experiments/{_EXP_ID}/calculate")
    assert response.status_code == 200
    body = response.json()
    assert body["calculations"]["result"]["result"] == 500.0


async def test_calculate_result_persisted_in_state(client: AsyncClient):
    await client.post("/api/experiments", json=_CREATE_BODY)
    await client.put(
        f"/api/experiments/{_EXP_ID}",
        json={
            "clientForm": {"name": "Client", "questions": []},
            "labForm": {"name": "Form", "questions": []},
            "calculations": {
                "result": {"formula": "values['value'] * 100", "result": ""},
            },
            "values": {"value": 2},
        },
    )
    await client.post(f"/api/experiments/{_EXP_ID}/calculate")
    get_response = await client.get(f"/api/experiments/{_EXP_ID}")
    assert get_response.json()["calculations"]["result"]["result"] == 200.0


async def test_calculate_unknown_exp_returns_404(client: AsyncClient):
    response = await client.post(f"/api/experiments/{uuid.uuid4()}/calculate")
    assert response.status_code == 404


async def test_calculate_division_by_zero_returns_422(client: AsyncClient):
    await client.post(
        "/api/experiments", json={**_CREATE_BODY, "exp_id": str(_EXP_ID_2)}
    )
    await client.put(
        f"/api/experiments/{_EXP_ID_2}",
        json={
            "clientForm": {"name": "Client", "questions": []},
            "labForm": {"name": "Form", "questions": []},
            "calculations": {
                "bad": {"formula": "1 / values['value']", "result": ""},
            },
            "values": {"value": 0},
        },
    )
    response = await client.post(f"/api/experiments/{_EXP_ID_2}/calculate")
    assert response.status_code == 422
    assert "Division by zero" in response.json()["detail"]
