"""Integration tests for /api/experiments endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import COAL_ID, DIVISOR_TEMPLATE_ID, PROXIMATE_TEMPLATE_ID

_DIVISOR_EXP_ID = uuid.UUID("eeeeeeee-0000-0000-0000-000000000002")

_DIVISOR_VALID_BODY = {
    "exp_id": str(_DIVISOR_EXP_ID),
    "sample_id": str(COAL_ID),
    "lineage_id": str(DIVISOR_TEMPLATE_ID),
}

_EXP_ID = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")

_VALID_BODY = {
    "exp_id": str(_EXP_ID),
    "sample_id": str(COAL_ID),
    "lineage_id": str(PROXIMATE_TEMPLATE_ID),
}

_STATE_WITH_VALUES = {
    "clientForm": {"name": "Client", "questions": []},
    "labForm": {"name": "Proximate Form", "questions": []},
    "calculations": {
        "result": {"formula": "values['value'] * 100", "result": ""},
    },
    "values": {"value": 5},
}


async def test_create_experiment_returns_201(client: AsyncClient):
    response = await client.post("/api/experiments", json=_VALID_BODY)
    assert response.status_code == 201


async def test_create_experiment_response_shape(client: AsyncClient):
    body = (await client.post("/api/experiments", json=_VALID_BODY)).json()
    assert body["id"] == str(_EXP_ID)
    assert body["sample_id"] == str(COAL_ID)
    assert body["template_id"] == str(PROXIMATE_TEMPLATE_ID)
    assert body["name"] == "Proximate Analysis"
    assert "labForm" in body
    assert "calculations" in body
    assert "values" in body
    assert "state" not in body
    assert "created_at" in body


async def test_create_experiment_duplicate_exp_id_returns_409(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    assert (await client.post("/api/experiments", json=_VALID_BODY)).status_code == 409


async def test_create_experiment_unknown_sample_returns_404(client: AsyncClient):
    body = {**_VALID_BODY, "exp_id": str(uuid.uuid4()), "sample_id": str(uuid.uuid4())}
    assert (await client.post("/api/experiments", json=body)).status_code == 404


async def test_create_experiment_unknown_template_returns_404(client: AsyncClient):
    body = {
        **_VALID_BODY,
        "exp_id": str(uuid.uuid4()),
        "lineage_id": str(uuid.uuid4()),
    }
    assert (await client.post("/api/experiments", json=body)).status_code == 404


async def test_list_experiments_returns_200(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    response = await client.get("/api/experiments")
    assert response.status_code == 200
    assert "experiments" in response.json()


async def test_list_experiments_summary_shape(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    exp = (await client.get("/api/experiments")).json()["experiments"][0]
    assert "id" in exp
    assert "sample_id" in exp
    assert "template_id" in exp
    assert "created_at" in exp
    assert "state" not in exp
    assert "labForm" not in exp


async def test_get_experiment_returns_full_detail(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (await client.get(f"/api/experiments/{_EXP_ID}")).json()
    assert body["id"] == str(_EXP_ID)
    assert body["template_id"] == str(PROXIMATE_TEMPLATE_ID)
    assert "labForm" in body
    assert "state" not in body


async def test_get_experiment_unknown_returns_404(client: AsyncClient):
    assert (await client.get(f"/api/experiments/{uuid.uuid4()}")).status_code == 404


async def test_update_experiment_stores_state(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (
        await client.put(f"/api/experiments/{_EXP_ID}", json=_STATE_WITH_VALUES)
    ).json()
    assert body["labForm"]["name"] == "Proximate Form"
    assert body["calculations"]["result"]["formula"] == "values['value'] * 100"
    assert body["values"]["value"] == 5


async def test_update_experiment_returns_updated_state(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body = (
        await client.put(f"/api/experiments/{_EXP_ID}", json=_STATE_WITH_VALUES)
    ).json()
    assert body["template_id"] == str(PROXIMATE_TEMPLATE_ID)
    assert body["sample_id"] == str(COAL_ID)


async def test_update_experiment_unknown_returns_404(client: AsyncClient):
    assert (
        await client.put(f"/api/experiments/{uuid.uuid4()}", json=_STATE_WITH_VALUES)
    ).status_code == 404


async def test_update_experiment_drifted_calculation_formula_returns_422(
    client: AsyncClient,
):
    await client.post("/api/experiments", json=_VALID_BODY)
    drifted = {
        **_STATE_WITH_VALUES,
        "calculations": {
            "result": {"formula": "values['value'] * 999", "result": ""},
        },
    }
    response = await client.put(f"/api/experiments/{_EXP_ID}", json=drifted)
    assert response.status_code == 422
    drift = response.json()["detail"]["drift"]
    assert drift == ["calculations.result"]


async def test_update_experiment_drifted_labform_returns_422(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    drifted = {
        **_STATE_WITH_VALUES,
        "labForm": {"name": "Renamed Form", "questions": []},
    }
    response = await client.put(f"/api/experiments/{_EXP_ID}", json=drifted)
    assert response.status_code == 422
    drift = response.json()["detail"]["drift"]
    assert drift == ["labForm"]


async def test_update_experiment_drift_report_names_every_drifted_part(
    client: AsyncClient,
):
    await client.post("/api/experiments", json=_VALID_BODY)
    drifted = {
        "clientForm": {"name": "Renamed Client", "questions": []},
        "labForm": {"name": "Renamed Form", "questions": []},
        "calculations": {
            "result": {"formula": "values['value'] * 999", "result": ""},
            "extra": {"formula": "1", "result": ""},
        },
        "values": {"value": 5},
    }
    response = await client.put(f"/api/experiments/{_EXP_ID}", json=drifted)
    assert response.status_code == 422
    drift = response.json()["detail"]["drift"]
    assert drift == [
        "clientForm",
        "labForm",
        "calculations.extra",
        "calculations.result",
    ]


async def test_update_experiment_ignores_client_supplied_result(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    body_with_fabricated_result = {
        **_STATE_WITH_VALUES,
        "calculations": {
            "result": {"formula": "values['value'] * 100", "result": 999999},
        },
    }
    response = await client.put(
        f"/api/experiments/{_EXP_ID}", json=body_with_fabricated_result
    )
    assert response.status_code == 200
    assert response.json()["calculations"]["result"]["result"] == ""


async def test_update_experiment_calculations_replaces_formula(client: AsyncClient):
    await client.post("/api/experiments", json=_DIVISOR_VALID_BODY)
    response = await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}/calculations",
        json={
            "calculations": {
                "bad": {
                    "formula": "values['value'] / values['value'] if values['value'] else None"
                },
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["calculations"]["bad"]["formula"] == (
        "values['value'] / values['value'] if values['value'] else None"
    )
    assert body["calculations"]["bad"]["result"] == ""


async def test_update_experiment_calculations_does_not_touch_template_id(
    client: AsyncClient,
):
    await client.post("/api/experiments", json=_DIVISOR_VALID_BODY)
    response = await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}/calculations",
        json={"calculations": {"bad": {"formula": "1"}}},
    )
    assert response.json()["template_id"] == str(DIVISOR_TEMPLATE_ID)


async def test_update_experiment_calculations_leaves_forms_and_values_untouched(
    client: AsyncClient,
):
    await client.post("/api/experiments", json=_DIVISOR_VALID_BODY)
    await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}",
        json={
            "clientForm": {"name": "Client", "questions": []},
            "labForm": {"name": "Form", "questions": []},
            "calculations": {"bad": {"formula": "1 / values['value']", "result": ""}},
            "values": {"value": 5},
        },
    )
    response = await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}/calculations",
        json={"calculations": {"bad": {"formula": "1"}}},
    )
    assert response.status_code == 200
    assert response.json()["values"] == {"value": 5}


async def test_update_experiment_calculations_can_then_be_evaluated(
    client: AsyncClient,
):
    await client.post("/api/experiments", json=_DIVISOR_VALID_BODY)
    await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}",
        json={
            "clientForm": {"name": "Client", "questions": []},
            "labForm": {"name": "Form", "questions": []},
            "calculations": {"bad": {"formula": "1 / values['value']", "result": ""}},
            "values": {"value": 0},
        },
    )
    await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}/calculations",
        json={
            "calculations": {
                "bad": {"formula": "1 / values['value'] if values['value'] else 0"},
            }
        },
    )
    response = await client.post(f"/api/experiments/{_DIVISOR_EXP_ID}/calculate")
    assert response.status_code == 200
    assert response.json()["calculations"]["bad"]["result"] == 0


async def test_update_experiment_values_after_calculation_override_preserves_override(
    client: AsyncClient,
):
    """A per-experiment formula override (PUT /calculations) must survive a
    later values-only save (PUT /{exp_id}) instead of being flagged as
    template drift or silently reverted to the template's formula.
    """
    await client.post("/api/experiments", json=_DIVISOR_VALID_BODY)
    await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}/calculations",
        json={"calculations": {"bad": {"formula": "values['value'] * 2"}}},
    )
    current = (
        await client.get(f"/api/experiments/{_DIVISOR_EXP_ID}")
    ).json()

    response = await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}",
        json={
            "clientForm": current["clientForm"],
            "labForm": current["labForm"],
            "calculations": current["calculations"],
            "values": {"value": 9},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["values"]["value"] == 9
    assert body["calculations"]["bad"]["formula"] == "values['value'] * 2"


async def test_update_experiment_calculations_invalid_name_returns_422(
    client: AsyncClient,
):
    await client.post("/api/experiments", json=_DIVISOR_VALID_BODY)
    response = await client.put(
        f"/api/experiments/{_DIVISOR_EXP_ID}/calculations",
        json={"calculations": {"not a valid name!": {"formula": "1"}}},
    )
    assert response.status_code == 422


async def test_update_experiment_calculations_unknown_experiment_returns_404(
    client: AsyncClient,
):
    response = await client.put(
        f"/api/experiments/{uuid.uuid4()}/calculations",
        json={"calculations": {"bad": {"formula": "1"}}},
    )
    assert response.status_code == 404


async def test_delete_experiment_returns_204(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    assert (await client.delete(f"/api/experiments/{_EXP_ID}")).status_code == 204


async def test_delete_experiment_is_gone_after_delete(client: AsyncClient):
    await client.post("/api/experiments", json=_VALID_BODY)
    await client.delete(f"/api/experiments/{_EXP_ID}")
    assert (await client.get(f"/api/experiments/{_EXP_ID}")).status_code == 404


async def test_delete_experiment_unknown_returns_404(client: AsyncClient):
    assert (await client.delete(f"/api/experiments/{uuid.uuid4()}")).status_code == 404
