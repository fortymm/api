from httpx import AsyncClient

EXPECTED_GROUPS = {
    "tournaments": 5,
    "matches": 4,
    "players": 4,
    "solver": 3,
    "users_access": 9,
    "reports": 4,
}


async def test_permissions_returns_29_across_6_groups(client: AsyncClient) -> None:
    response = await client.get("/v1/permissions")

    assert response.status_code == 200
    body = response.json()

    groups = {g["key"]: g for g in body["groups"]}
    assert set(groups) == set(EXPECTED_GROUPS)
    for key, expected_count in EXPECTED_GROUPS.items():
        assert len(groups[key]["permissions"]) == expected_count, key

    total = sum(len(g["permissions"]) for g in body["groups"])
    assert total == 29


async def test_permissions_payload_shape(client: AsyncClient) -> None:
    body = (await client.get("/v1/permissions")).json()

    sample = body["groups"][0]["permissions"][0]
    assert set(sample) == {"code", "name", "description"}
    assert sample["code"]
    assert sample["name"]
    assert sample["description"]


async def test_openapi_exposes_permissions_response(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert "/v1/permissions" in schema["paths"]
    components = schema["components"]["schemas"]
    for name in ("PermissionsResponse", "PermissionGroup", "PermissionItem"):
        assert name in components
