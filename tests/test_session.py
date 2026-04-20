import re
from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient

from app.auth import JWT_ALGORITHM
from app.config import settings

USERNAME_RE = re.compile(r"^[a-z]+-[a-z]+-[a-z2-9]{4}$")


async def _create(client: AsyncClient, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = await client.post("/v1/session", headers=headers)
    assert response.status_code == 200
    return response.json()


async def test_no_token_creates_user(client: AsyncClient) -> None:
    body = await _create(client)

    assert USERNAME_RE.match(body["user"]["username"])
    assert body["token"]
    assert body["user"]["id"]


async def test_valid_token_returns_same_user_with_new_token(client: AsyncClient) -> None:
    first = await _create(client)
    second = await _create(client, token=first["token"])

    assert second["user"]["id"] == first["user"]["id"]
    assert second["user"]["username"] == first["user"]["username"]
    assert second["token"] != first["token"]


async def test_garbage_token_creates_new_user(client: AsyncClient) -> None:
    first = await _create(client)
    second = await _create(client, token="not.a.real.jwt")

    assert second["user"]["id"] != first["user"]["id"]


async def test_expired_token_creates_new_user(client: AsyncClient) -> None:
    first = await _create(client)

    expired = jwt.encode(
        {
            "sub": first["user"]["id"],
            "iat": datetime.now(UTC) - timedelta(days=60),
            "exp": datetime.now(UTC) - timedelta(days=30),
        },
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )

    second = await _create(client, token=expired)
    assert second["user"]["id"] != first["user"]["id"]


async def test_token_claims_are_correct(client: AsyncClient) -> None:
    body = await _create(client)

    payload = jwt.decode(body["token"], settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == body["user"]["id"]

    expected_exp = datetime.now(UTC) + timedelta(seconds=settings.jwt_lifetime_seconds)
    actual_exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
    assert abs((actual_exp - expected_exp).total_seconds()) < 10


async def test_openapi_schema_exposes_session_models(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    post_session = schema["paths"]["/v1/session"]["post"]
    ref = post_session["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert ref == "#/components/schemas/SessionResponse"

    components = schema["components"]["schemas"]
    assert "SessionResponse" in components
    assert "UserPublic" in components
    assert components["SessionResponse"]["properties"]["user"]["$ref"].endswith("UserPublic")
