"""Integration tests for POST /api/calculations/evaluate.

The dry run exists so a template author can run their formulas during
onboarding, before any experiment exists. Its contract differs from
`/api/experiments/{id}/calculate` in one important way: a broken formula is
reported *alongside* the ones that worked instead of aborting the request, so
these tests assert partial success as much as they assert results.
"""

from httpx import AsyncClient

ENDPOINT = "/api/calculations/evaluate"


def _lab_form(questions: list[dict]) -> dict:
    return {"name": "Lab Form", "questions": questions}


async def test_evaluates_dependency_chain(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "loss": {
                    "formula": "values['start_mass'] - values['end_mass']",
                },
                "loss_pct": {"formula": "round(100 * loss / values['start_mass'], 1)"},
            },
            "values": {"start_mass": 20.0, "end_mass": 15.0},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calculations"]["loss"]["status"] == "ok"
    assert body["calculations"]["loss"]["result"] == 5.0
    assert body["calculations"]["loss_pct"]["result"] == 25.0
    assert body["missing_values"] == []


async def test_response_shape(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {"doubled": {"formula": "values['x'] * 2"}},
            "values": {"x": 3},
        },
    )

    body = response.json()
    assert set(body) == {
        "values",
        "order",
        "calculations",
        "missing_values",
        "duplicate_question_ids",
    }
    assert body["order"] == ["doubled"]
    assert body["values"] == {"x": 3}
    assert body["calculations"]["doubled"] == {
        "formula": "values['x'] * 2",
        "status": "ok",
        "result": 6,
        "error": None,
    }


async def test_order_follows_dependencies_but_rows_keep_declaration_order(
    client: AsyncClient,
):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "total": {"formula": "half * 2"},
                "half": {"formula": "values['x'] / 2"},
            },
            "values": {"x": 10},
        },
    )

    body = response.json()
    assert body["order"] == ["half", "total"]
    assert list(body["calculations"]) == ["total", "half"]
    assert body["calculations"]["total"]["result"] == 10.0


async def test_question_defaults_fill_missing_values(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "labForm": _lab_form(
                [
                    {
                        "id": "crucible_mass",
                        "type": "number",
                        "label": "Crucible mass (g)",
                        "config": {"default": 20.0},
                    }
                ]
            ),
            "calculations": {"total": {"formula": "values['crucible_mass'] + 1"}},
        },
    )

    body = response.json()
    assert body["values"] == {"crucible_mass": 20.0}
    assert body["calculations"]["total"]["result"] == 21.0
    assert body["missing_values"] == []


async def test_typo_in_question_id_is_reported_as_missing_value(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {"total": {"formula": "values['sample_mas'] * 2"}},
            "values": {"sample_mass": 1.5},
        },
    )

    assert response.status_code == 200
    body = response.json()
    outcome = body["calculations"]["total"]
    assert outcome["status"] == "error"
    assert outcome["error"]["kind"] == "missing_value"
    assert outcome["error"]["names"] == ["sample_mas"]
    assert body["missing_values"] == ["sample_mas"]


async def test_one_bad_formula_does_not_hide_the_good_ones(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "fine": {"formula": "values['x'] + 1"},
                "bad": {"formula": "1 / values['zero']"},
                "also_fine": {"formula": "values['x'] * 3"},
            },
            "values": {"x": 2, "zero": 0},
        },
    )

    assert response.status_code == 200
    calcs = response.json()["calculations"]
    assert calcs["fine"]["result"] == 3
    assert calcs["also_fine"]["result"] == 6
    assert calcs["bad"]["status"] == "error"
    assert calcs["bad"]["error"]["kind"] == "zero_division"


async def test_dependent_of_a_failed_formula_is_skipped(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "broken": {"formula": "1 / values['zero']"},
                "downstream": {"formula": "broken + 1"},
            },
            "values": {"zero": 0},
        },
    )

    calcs = response.json()["calculations"]
    assert calcs["broken"]["status"] == "error"
    assert calcs["downstream"]["status"] == "skipped"
    assert calcs["downstream"]["error"]["kind"] == "dependency_failed"
    assert calcs["downstream"]["error"]["names"] == ["broken"]
    assert calcs["downstream"]["result"] is None


async def test_circular_dependency_reported_without_blocking_others(
    client: AsyncClient,
):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "a": {"formula": "b + 1"},
                "b": {"formula": "a + 1"},
                "independent": {"formula": "values['x'] * 10"},
            },
            "values": {"x": 4},
        },
    )

    assert response.status_code == 200
    body = response.json()
    calcs = body["calculations"]
    assert body["order"] == ["independent"]
    assert calcs["independent"]["result"] == 40
    assert calcs["a"]["error"]["kind"] == "circular"
    assert calcs["b"]["error"]["kind"] == "circular"
    assert calcs["a"]["error"]["names"] == ["b"]


async def test_undefined_name_names_the_identifier(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={"calculations": {"r": {"formula": "mystery + 1"}}, "values": {}},
    )

    error = response.json()["calculations"]["r"]["error"]
    assert error["kind"] == "undefined_name"
    assert error["names"] == ["mystery"]


async def test_dunder_access_rejected(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "r": {"formula": "().__class__.__bases__[0].__subclasses__()"}
            },
            "values": {},
        },
    )

    error = response.json()["calculations"]["r"]["error"]
    assert error["kind"] == "dunder"
    assert "dunder" in error["message"]


async def test_syntax_error_reported_per_formula(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={"calculations": {"r": {"formula": "x =\n+ 1"}}, "values": {}},
    )

    assert response.json()["calculations"]["r"]["error"]["kind"] == "syntax"


async def test_non_finite_result_reported(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={"calculations": {"r": {"formula": "math.nan"}}, "values": {}},
    )

    assert response.json()["calculations"]["r"]["error"]["kind"] == "non_finite"


async def test_multiline_formula_with_result_variable(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "y": {"formula": "tmp = values['x'] + 2\nresult = tmp * 10"}
            },
            "values": {"x": 3},
        },
    )

    assert response.json()["calculations"]["y"]["result"] == 50


async def test_numeric_strings_are_coerced_and_echoed_back(client: AsyncClient):
    response = await client.post(
        ENDPOINT,
        json={
            "calculations": {
                "delta": {
                    "formula": "values['temp_final'] - values['temp_initial']",
                }
            },
            "values": {"temp_final": "30.5", "temp_initial": "24.5"},
        },
    )

    body = response.json()
    assert body["values"] == {"temp_final": 30.5, "temp_initial": 24.5}
    assert body["calculations"]["delta"]["result"] == 6.0


async def test_duplicate_question_ids_reported(client: AsyncClient):
    question = {"id": "mass", "type": "number", "label": "Mass"}
    response = await client.post(
        ENDPOINT,
        json={
            "clientForm": {"name": "Client", "questions": [question]},
            "labForm": _lab_form([question]),
            "calculations": {},
            "values": {"mass": 1},
        },
    )

    assert response.json()["duplicate_question_ids"] == ["mass"]


async def test_empty_calculations_is_not_an_error(client: AsyncClient):
    response = await client.post(
        ENDPOINT, json={"calculations": {}, "values": {"x": 1}}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calculations"] == {}
    assert body["order"] == []
    assert body["missing_values"] == []


async def test_calculations_field_is_required(client: AsyncClient):
    response = await client.post(ENDPOINT, json={"values": {"x": 1}})

    assert response.status_code == 422


async def test_dry_run_persists_nothing(client: AsyncClient):
    before = (await client.get("/api/experiments")).json()["experiments"]
    await client.post(
        ENDPOINT,
        json={
            "calculations": {"r": {"formula": "values['x'] * 2"}},
            "values": {"x": 1},
        },
    )
    after = (await client.get("/api/experiments")).json()["experiments"]

    assert before == after
