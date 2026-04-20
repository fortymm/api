from httpx import AsyncClient

from app.api.v1.router import PingResponse


async def test_ping_returns_pong(client: AsyncClient) -> None:
    response = await client.get("/v1/ping")

    assert response.status_code == 200
    assert response.json() == {"data": "pong"}


async def test_ping_response_matches_model(client: AsyncClient) -> None:
    response = await client.get("/v1/ping")

    parsed = PingResponse.model_validate(response.json())
    assert parsed.data == "pong"


async def test_openapi_schema_references_ping_response(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    schema = response.json()

    ping_200 = schema["paths"]["/v1/ping"]["get"]["responses"]["200"]
    ref = ping_200["content"]["application/json"]["schema"]["$ref"]
    assert ref == "#/components/schemas/PingResponse"

    ping_schema = schema["components"]["schemas"]["PingResponse"]
    assert ping_schema["properties"]["data"]["type"] == "string"
    assert ping_schema["required"] == ["data"]
