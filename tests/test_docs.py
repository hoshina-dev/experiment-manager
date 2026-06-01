import pytest
from httpx import ASGITransport, AsyncClient

from main import create_app


@pytest.fixture
async def docs_client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_swagger_docs_available(docs_client):
    response = await docs_client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


async def test_scalar_docs_available(docs_client):
    response = await docs_client.get("/scalar")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "scalar" in response.text.lower()


async def test_openapi_json_available(docs_client):
    response = await docs_client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Experiment Manager"
