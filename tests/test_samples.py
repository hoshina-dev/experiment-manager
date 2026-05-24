"""Integration tests for /api/samples endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import (CALORIFIC_TEMPLATE_ID, COAL_ID,
                            PROXIMATE_TEMPLATE_ID)

_NEW_SAMPLE = {"name": "Test Sample", "description": "For testing"}
_NEW_EXPERIMENT_TEMPLATE = {
    "name": "Test Analysis",
    "description": "A test analysis",
    "workerForm": {"title": "Test Form", "questions": []},
    "calculations": {"x": "a + b"},
    "template": "Result: {{x}}",
}


# ---------------------------------------------------------------------------
# GET /api/samples
# ---------------------------------------------------------------------------


async def test_list_samples_returns_200(client: AsyncClient):
    response = await client.get("/api/samples")
    assert response.status_code == 200
    assert "samples" in response.json()


async def test_list_samples_contains_seeded_data(client: AsyncClient):
    ids = [s["id"] for s in (await client.get("/api/samples")).json()["samples"]]
    assert str(COAL_ID) in ids


# ---------------------------------------------------------------------------
# POST /api/samples
# ---------------------------------------------------------------------------


async def test_create_sample_returns_201(client: AsyncClient):
    response = await client.post("/api/samples", json=_NEW_SAMPLE)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test Sample"
    assert "id" in body


# ---------------------------------------------------------------------------
# GET /api/samples/{sample_id}
# ---------------------------------------------------------------------------


async def test_get_sample_returns_200(client: AsyncClient):
    response = await client.get(f"/api/samples/{COAL_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == str(COAL_ID)


async def test_get_sample_unknown_returns_404(client: AsyncClient):
    assert (await client.get(f"/api/samples/{uuid.uuid4()}")).status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/samples/{sample_id}
# ---------------------------------------------------------------------------


async def test_update_sample_returns_200(client: AsyncClient):
    r = await client.post("/api/samples", json=_NEW_SAMPLE)
    sid = r.json()["id"]
    response = await client.put(f"/api/samples/{sid}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


async def test_update_sample_unknown_returns_404(client: AsyncClient):
    assert (
        await client.put(f"/api/samples/{uuid.uuid4()}", json={"name": "X"})
    ).status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/samples/{sample_id}
# ---------------------------------------------------------------------------


async def test_delete_sample_returns_204(client: AsyncClient):
    sid = (await client.post("/api/samples", json=_NEW_SAMPLE)).json()["id"]
    assert (await client.delete(f"/api/samples/{sid}")).status_code == 204


async def test_delete_sample_is_gone_after_delete(client: AsyncClient):
    sid = (await client.post("/api/samples", json=_NEW_SAMPLE)).json()["id"]
    await client.delete(f"/api/samples/{sid}")
    assert (await client.get(f"/api/samples/{sid}")).status_code == 404


async def test_delete_sample_unknown_returns_404(client: AsyncClient):
    assert (await client.delete(f"/api/samples/{uuid.uuid4()}")).status_code == 404


# ---------------------------------------------------------------------------
# GET /api/samples/{sample_id}/experiments
# ---------------------------------------------------------------------------


async def test_list_experiment_templates_returns_200(client: AsyncClient):
    response = await client.get(f"/api/samples/{COAL_ID}/experiments")
    assert response.status_code == 200
    assert "experiments" in response.json()


async def test_list_experiment_templates_contains_seeded_templates(client: AsyncClient):
    names = [
        a["name"]
        for a in (await client.get(f"/api/samples/{COAL_ID}/experiments")).json()[
            "experiments"
        ]
    ]
    assert "Proximate Analysis" in names
    assert "Calorific Value" in names


async def test_list_experiment_templates_unknown_sample_returns_404(
    client: AsyncClient,
):
    assert (
        await client.get(f"/api/samples/{uuid.uuid4()}/experiments")
    ).status_code == 404


# ---------------------------------------------------------------------------
# POST /api/samples/{sample_id}/experiments
# ---------------------------------------------------------------------------


async def test_create_experiment_template_returns_201(client: AsyncClient):
    response = await client.post(
        f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Analysis"


async def test_create_experiment_template_unknown_sample_returns_404(
    client: AsyncClient,
):
    assert (
        await client.post(
            f"/api/samples/{uuid.uuid4()}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).status_code == 404


# ---------------------------------------------------------------------------
# GET /api/samples/{sample_id}/experiments/{template_id}
# ---------------------------------------------------------------------------


async def test_get_experiment_template_returns_200(client: AsyncClient):
    response = await client.get(
        f"/api/samples/{COAL_ID}/experiments/{PROXIMATE_TEMPLATE_ID}"
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Proximate Analysis"


async def test_get_experiment_template_unknown_returns_404(client: AsyncClient):
    assert (
        await client.get(f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}")
    ).status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/samples/{sample_id}/experiments/{template_id}
# ---------------------------------------------------------------------------


async def test_update_experiment_template_returns_200(client: AsyncClient):
    tid = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()["id"]
    updated = {**_NEW_EXPERIMENT_TEMPLATE, "name": "Updated Analysis"}
    response = await client.put(
        f"/api/samples/{COAL_ID}/experiments/{tid}", json=updated
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Analysis"


async def test_update_experiment_template_unknown_returns_404(client: AsyncClient):
    assert (
        await client.put(
            f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}",
            json=_NEW_EXPERIMENT_TEMPLATE,
        )
    ).status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/samples/{sample_id}/experiments/{template_id}
# ---------------------------------------------------------------------------


async def test_delete_experiment_template_returns_204(client: AsyncClient):
    tid = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()["id"]
    assert (
        await client.delete(f"/api/samples/{COAL_ID}/experiments/{tid}")
    ).status_code == 204


async def test_delete_experiment_template_is_gone_after_delete(client: AsyncClient):
    tid = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()["id"]
    await client.delete(f"/api/samples/{COAL_ID}/experiments/{tid}")
    assert (
        await client.get(f"/api/samples/{COAL_ID}/experiments/{tid}")
    ).status_code == 404


async def test_delete_experiment_template_unknown_returns_404(client: AsyncClient):
    assert (
        await client.delete(f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}")
    ).status_code == 404
