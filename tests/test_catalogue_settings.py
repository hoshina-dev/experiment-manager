import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from tests.conftest import COAL_ID, NO_PDF_TEMPLATE_ID, PROXIMATE_TEMPLATE_ID, TOMATO_ID


async def sample_ids(client):
    return [row["id"] for row in (await client.get("/api/samples")).json()["samples"]]


async def template_rows(client, sample_id=COAL_ID):
    return (await client.get(f"/api/samples/{sample_id}/experiments")).json()[
        "experiments"
    ]


async def test_new_entries_are_hidden_and_append(client: AsyncClient):
    before = (await client.get("/api/samples")).json()["samples"]
    sample = (await client.post("/api/samples", json={"name": "A new specimen"})).json()
    assert sample["is_visible_on_web"] is False
    assert sample["display_order"] == max(row["display_order"] for row in before) + 1
    created = (
        await client.post(
            f'/api/samples/{sample["id"]}/experiments',
            json={
                "name": "New test",
                "clientForm": {"name": "Client", "questions": []},
                "labForm": {"name": "Lab", "questions": []},
                "calculations": {},
            },
        )
    ).json()
    assert created["is_visible_on_web"] is False
    assert created["display_order"] == 1
    assert created["has_pdf_template"] is False


async def test_sample_visibility_persists_without_hiding_backend_rows(
    client: AsyncClient,
):
    result = await client.patch(
        f"/api/samples/{COAL_ID}/web-visibility", json={"is_visible_on_web": False}
    )
    assert result.status_code == 200
    assert result.json()["is_visible_on_web"] is False
    assert (await client.get(f"/api/samples/{COAL_ID}")).json()[
        "is_visible_on_web"
    ] is False
    assert str(COAL_ID) in await sample_ids(client)


async def test_orders_persist_and_include_hidden_entries(client: AsyncClient):
    ids = await sample_ids(client)
    await client.patch(
        f"/api/samples/{COAL_ID}/web-visibility", json={"is_visible_on_web": False}
    )
    result = await client.put("/api/samples/web-order", json={"sample_ids": ids[::-1]})
    assert result.status_code == 200
    assert await sample_ids(client) == ids[::-1]
    rows = await template_rows(client)
    lineages = [row["lineage_id"] for row in rows]
    result = await client.put(
        f"/api/samples/{COAL_ID}/experiments/web-order",
        json={"lineage_ids": lineages[::-1]},
    )
    assert result.status_code == 200
    after = await template_rows(client)
    assert [row["lineage_id"] for row in after] == lineages[::-1]
    assert [row["display_order"] for row in after] == list(range(1, len(after) + 1))


@pytest.mark.parametrize(
    "kind,status", [("duplicate", 422), ("unknown", 404), ("missing", 409)]
)
async def test_invalid_sample_order_is_atomic(client: AsyncClient, kind, status):
    original = await sample_ids(client)
    ids = original[::-1]
    if kind == "duplicate":
        ids.append(ids[0])
    if kind == "unknown":
        ids.append(str(uuid.uuid4()))
    if kind == "missing":
        ids.pop()
    response = await client.put("/api/samples/web-order", json={"sample_ids": ids})
    assert response.status_code == status
    assert await sample_ids(client) == original


@pytest.mark.parametrize(
    "kind,status", [("duplicate", 422), ("unknown", 404), ("missing", 409)]
)
async def test_invalid_template_order_is_atomic(client: AsyncClient, kind, status):
    original = [row["lineage_id"] for row in await template_rows(client)]
    ids = original[::-1]
    if kind == "duplicate":
        ids.append(ids[0])
    if kind == "unknown":
        ids.append(str(uuid.uuid4()))
    if kind == "missing":
        ids.pop()
    response = await client.put(
        f"/api/samples/{COAL_ID}/experiments/web-order", json={"lineage_ids": ids}
    )
    assert response.status_code == status
    assert [row["lineage_id"] for row in await template_rows(client)] == original


async def test_visibility_scope_and_unknown_ids(client: AsyncClient):
    body = {"is_visible_on_web": True}
    for path in [
        f"/api/samples/{uuid.uuid4()}/web-visibility",
        f"/api/samples/{TOMATO_ID}/experiments/{PROXIMATE_TEMPLATE_ID}/web-visibility",
        f"/api/samples/{COAL_ID}/experiments/{uuid.uuid4()}/web-visibility",
    ]:
        assert (await client.patch(path, json=body)).status_code == 404
    assert (
        await client.put(
            f"/api/samples/{TOMATO_ID}/experiments/web-order",
            json={"lineage_ids": [str(PROXIMATE_TEMPLATE_ID)]},
        )
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/samples/{COAL_ID}/web-visibility", json={"is_visible_on_web": "yes"}
        )
    ).status_code == 422


async def test_visible_no_pdf_cannot_be_requested_and_hidden_ready_can(
    client: AsyncClient,
):
    await client.patch(
        f"/api/samples/{COAL_ID}/experiments/{NO_PDF_TEMPLATE_ID}/web-visibility",
        json={"is_visible_on_web": True},
    )
    no_pdf = next(
        row
        for row in await template_rows(client)
        if row["id"] == str(NO_PDF_TEMPLATE_ID)
    )
    assert no_pdf["is_visible_on_web"] and not no_pdf["has_pdf_template"]
    assert (
        await client.post(
            "/api/experiments",
            json={
                "exp_id": str(uuid.uuid4()),
                "sample_id": str(COAL_ID),
                "lineage_id": str(NO_PDF_TEMPLATE_ID),
            },
        )
    ).status_code == 422
    await client.patch(
        f"/api/samples/{COAL_ID}/experiments/{PROXIMATE_TEMPLATE_ID}/web-visibility",
        json={"is_visible_on_web": False},
    )
    assert (
        await client.post(
            "/api/experiments",
            json={
                "exp_id": str(uuid.uuid4()),
                "sample_id": str(COAL_ID),
                "lineage_id": str(PROXIMATE_TEMPLATE_ID),
            },
        )
    ).status_code == 201


async def test_empty_pdf_is_not_requestable(client: AsyncClient):
    await client.put(
        f"/api/samples/{COAL_ID}/experiments/{NO_PDF_TEMPLATE_ID}/pdf",
        json={"components": []},
    )
    row = (
        await client.get(f"/api/samples/{COAL_ID}/experiments/{NO_PDF_TEMPLATE_ID}")
    ).json()
    assert row["has_pdf_template"] is False
    assert (
        await client.post(
            "/api/experiments",
            json={
                "exp_id": str(uuid.uuid4()),
                "sample_id": str(COAL_ID),
                "lineage_id": str(NO_PDF_TEMPLATE_ID),
            },
        )
    ).status_code == 422


async def test_settings_do_not_fork_and_survive_form_and_pdf_versions(
    client: AsyncClient,
):
    path = f"/api/samples/{COAL_ID}/experiments/{PROXIMATE_TEMPLATE_ID}"
    original = (await client.get(path)).json()
    await client.patch(path + "/web-visibility", json={"is_visible_on_web": False})
    ids = [row["lineage_id"] for row in await template_rows(client)]
    ids.remove(str(PROXIMATE_TEMPLATE_ID))
    ids.insert(0, str(PROXIMATE_TEMPLATE_ID))
    await client.put(
        f"/api/samples/{COAL_ID}/experiments/web-order", json={"lineage_ids": ids}
    )
    assert len((await client.get(path + "/history")).json()["versions"]) == 1
    exp = (
        await client.post(
            "/api/experiments",
            json={
                "exp_id": str(uuid.uuid4()),
                "sample_id": str(COAL_ID),
                "lineage_id": str(PROXIMATE_TEMPLATE_ID),
            },
        )
    ).json()
    update = {
        key: original[key]
        for key in ["name", "description", "clientForm", "labForm", "calculations"]
    }
    update["name"] += " updated"
    version = (await client.put(path, json=update)).json()
    assert version["id"] != original["id"]
    assert version["is_visible_on_web"] is False and version["display_order"] == 1
    await client.post(
        "/api/experiments",
        json={
            "exp_id": str(uuid.uuid4()),
            "sample_id": str(COAL_ID),
            "lineage_id": str(PROXIMATE_TEMPLATE_ID),
        },
    )
    await client.put(
        path + "/pdf",
        json={"components": [{"type": "text", "x": 10, "y": 20, "content": "Changed"}]},
    )
    current = next(
        row
        for row in await template_rows(client)
        if row["lineage_id"] == str(PROXIMATE_TEMPLATE_ID)
    )
    assert current["version"] == 3
    assert current["is_visible_on_web"] is False and current["display_order"] == 1
    assert (await client.get(f'/api/experiments/{exp["id"]}')).json()[
        "name"
    ] == original["name"]


async def test_migration_backfills_and_rolls_back(test_engine):
    from sqlalchemy import text

    schema = "catalogue_migration_" + uuid.uuid4().hex
    async with test_engine.connect() as conn:
        async with conn.begin():
            await conn.execute(text(f"CREATE SCHEMA {schema}"))
            await conn.execute(text(f"SET LOCAL search_path TO {schema}, public"))
            await conn.execute(
                text(
                    "CREATE TABLE sample_types(id UUID PRIMARY KEY, name TEXT, deleted_at TIMESTAMPTZ)"
                )
            )
            await conn.execute(
                text(
                    "CREATE TABLE experiment_templates(id UUID PRIMARY KEY, lineage_id UUID, sample_type_id UUID, name TEXT, version INTEGER, is_current BOOLEAN, deleted_at TIMESTAMPTZ)"
                )
            )
            await conn.execute(
                text("INSERT INTO sample_types VALUES (:id, :name, NULL)"),
                {"id": COAL_ID, "name": "Coal"},
            )
            for version in [1, 2]:
                await conn.execute(
                    text(
                        "INSERT INTO experiment_templates VALUES (:id, :lineage, :sample, :name, :version, :current, NULL)"
                    ),
                    {
                        "id": uuid.uuid4(),
                        "lineage": PROXIMATE_TEMPLATE_ID,
                        "sample": COAL_ID,
                        "name": "Test",
                        "version": version,
                        "current": version == 2,
                    },
                )
            root = Path(__file__).resolve().parents[1] / "migrations"
            for statement in (
                (root / "008_catalogue_web_settings.up.sql").read_text().split(";")
            ):
                if statement.strip() and statement.strip() not in ("BEGIN", "COMMIT"):
                    await conn.execute(text(statement))
            assert (
                await conn.execute(
                    text("SELECT is_visible_on_web, display_order FROM sample_types")
                )
            ).one() == (True, 1)
            assert (
                await conn.execute(
                    text(
                        "SELECT is_visible_on_web, display_order FROM experiment_template_web_settings"
                    )
                )
            ).one() == (True, 1)
            for statement in (
                (root / "008_catalogue_web_settings.down.sql").read_text().split(";")
            ):
                if statement.strip() and statement.strip() not in ("BEGIN", "COMMIT"):
                    await conn.execute(text(statement))
            assert (
                await conn.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.columns WHERE table_schema=:schema AND column_name='is_visible_on_web'"
                    ),
                    {"schema": schema},
                )
                == 0
            )
            await conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))


async def test_collection_locks_serialize_creates_and_reorders(test_engine):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.repositories.sample_repository import lock_web_collection

    async with test_engine.connect() as first, test_engine.connect() as second:
        async with first.begin(), second.begin():
            session = AsyncSession(bind=first)
            await lock_web_collection(session, COAL_ID)
            key = f"catalogue:templates:{COAL_ID}"
            statement = text(
                "SELECT pg_try_advisory_xact_lock(hashtextextended(:key, 0))"
            )
            assert await second.scalar(statement, {"key": key}) is False
            assert (
                await second.scalar(
                    statement, {"key": f"catalogue:templates:{TOMATO_ID}"}
                )
                is True
            )
            await session.close()
        async with second.begin():
            assert await second.scalar(statement, {"key": key}) is True
