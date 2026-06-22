"""Integration tests for /api/samples endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import (CALORIFIC_TEMPLATE_ID, COAL_ID,
                            PROXIMATE_TEMPLATE_ID)

_NEW_SAMPLE = {"name": "Test Sample", "description": "For testing"}
_NEW_EXPERIMENT_TEMPLATE = {
    "name": "Test Analysis",
    "description": "A test analysis",
    "clientForm": {"name": "Client", "questions": []},
    "labForm": {"name": "Test Form", "questions": []},
    "calculations": {
        "x": {"formula": "values['a'] + values['b']", "result": ""},
    },
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
    assert "lineage_id" in response.json()
    assert response.json()["version"] == 1


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
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    updated = {**_NEW_EXPERIMENT_TEMPLATE, "name": "Updated Analysis"}
    response = await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}", json=updated
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


async def test_create_experiment_template_duplicate_id_across_forms_returns_422(
    client: AsyncClient,
):
    body = {
        **_NEW_EXPERIMENT_TEMPLATE,
        "name": "__dup_id_across_forms",
        "clientForm": {
            "name": "C",
            "questions": [{"id": "sample_id", "type": "string", "label": "Sample ID"}],
        },
        "labForm": {
            "name": "L",
            "questions": [{"id": "sample_id", "type": "number", "label": "Sample ID"}],
        },
        "calculations": {},
    }
    response = await client.post(f"/api/samples/{COAL_ID}/experiments", json=body)
    assert response.status_code == 422
    assert "sample_id" in response.json()["detail"]["errors"][0]


async def test_create_experiment_template_duplicate_repeatable_group_child_id_returns_422(
    client: AsyncClient,
):
    body = {
        **_NEW_EXPERIMENT_TEMPLATE,
        "name": "__dup_id_in_repeatable_group",
        "clientForm": {"name": "C", "questions": []},
        "labForm": {
            "name": "L",
            "questions": [
                {"id": "reading_a", "type": "number", "label": "Top-level"},
                {
                    "id": "measurement",
                    "type": "repeatable-group",
                    "label": "Measurements",
                    "config": {
                        "count": 3,
                        "questions": [
                            {"id": "reading_a", "type": "number", "label": "Reading A"}
                        ],
                    },
                },
            ],
        },
        "calculations": {},
    }
    response = await client.post(f"/api/samples/{COAL_ID}/experiments", json=body)
    assert response.status_code == 422
    assert "reading_a" in response.json()["detail"]["errors"][0]


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


# ---------------------------------------------------------------------------
# PDF template endpoints
# ---------------------------------------------------------------------------

_PDF_COMPONENTS = [{"type": "text", "x": 10, "y": 20, "content": "Hello"}]


async def test_get_pdf_template_no_pdf_returns_404(client: AsyncClient):
    # Freshly created template has no PDF yet
    tid = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()["id"]
    assert (
        await client.get(f"/api/samples/{COAL_ID}/experiments/{tid}/pdf")
    ).status_code == 404


async def test_upsert_pdf_template_creates_and_returns_200(client: AsyncClient):
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    response = await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": _PDF_COMPONENTS},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["components"] == _PDF_COMPONENTS
    assert body["is_current"] is True
    assert "template_id" in body


async def test_get_pdf_template_returns_200_after_upsert(client: AsyncClient):
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    template_id = created["id"]
    await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": _PDF_COMPONENTS},
    )
    response = await client.get(f"/api/samples/{COAL_ID}/experiments/{template_id}/pdf")
    assert response.status_code == 200
    assert response.json()["components"] == _PDF_COMPONENTS


async def test_upsert_pdf_template_updates_in_place_when_no_experiments(
    client: AsyncClient,
):
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    original_id = created["id"]

    await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": _PDF_COMPONENTS},
    )
    updated_components = [{"type": "text", "x": 50, "y": 60, "content": "Updated"}]
    response = await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": updated_components},
    )
    assert response.status_code == 200
    # Same template_id — no new version created
    assert response.json()["template_id"] == original_id
    assert response.json()["components"] == updated_components


async def test_upsert_pdf_template_creates_new_version_when_experiments_exist(
    client: AsyncClient,
):
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    original_template_id = created["id"]

    # Give it a PDF first
    await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": _PDF_COMPONENTS},
    )

    # Create an experiment referencing this template version
    await client.post(
        "/api/experiments",
        json={
            "exp_id": str(uuid.uuid4()),
            "sample_id": str(COAL_ID),
            "lineage_id": lineage_id,
        },
    )

    # Now update the PDF — should produce a new template version
    new_components = [{"type": "image", "x": 0, "y": 0, "src": "logo.png"}]
    response = await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": new_components},
    )
    assert response.status_code == 200
    body = response.json()
    # New template_id — SCD2 row was created
    assert body["template_id"] != original_template_id
    assert body["components"] == new_components
    assert body["is_current"] is True


async def test_delete_pdf_template_returns_204(client: AsyncClient):
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    tid = created["id"]
    await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": _PDF_COMPONENTS},
    )
    assert (
        await client.delete(f"/api/samples/{COAL_ID}/experiments/{tid}/pdf")
    ).status_code == 204


async def test_delete_pdf_template_is_gone_after_delete(client: AsyncClient):
    created = (
        await client.post(
            f"/api/samples/{COAL_ID}/experiments", json=_NEW_EXPERIMENT_TEMPLATE
        )
    ).json()
    lineage_id = created["lineage_id"]
    tid = created["id"]
    await client.put(
        f"/api/samples/{COAL_ID}/experiments/{lineage_id}/pdf",
        json={"components": _PDF_COMPONENTS},
    )
    await client.delete(f"/api/samples/{COAL_ID}/experiments/{tid}/pdf")
    assert (
        await client.get(f"/api/samples/{COAL_ID}/experiments/{tid}/pdf")
    ).status_code == 404


async def test_upsert_pdf_template_unknown_lineage_returns_404(client: AsyncClient):
    assert (
        await client.put(
            f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}/pdf",
            json={"components": []},
        )
    ).status_code == 404


async def test_get_pdf_template_unknown_template_returns_404(client: AsyncClient):
    assert (
        await client.get(f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}/pdf")
    ).status_code == 404


async def test_delete_pdf_template_unknown_returns_404(client: AsyncClient):
    assert (
        await client.delete(f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}/pdf")
    ).status_code == 404
