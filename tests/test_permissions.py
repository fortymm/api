from httpx import AsyncClient

from tests.factories import permission_payload as _payload


async def test_list_permissions_empty(client: AsyncClient, me: dict) -> None:
    response = await client.get("/v1/permissions", headers=me["headers"])

    assert response.status_code == 200
    assert response.json() == []


async def test_create_permission_returns_public_permission(client: AsyncClient, me: dict) -> None:
    response = await client.post("/v1/permissions", headers=me["headers"], json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "tournaments.read"
    assert body["name"] == "View tournaments"
    assert body["description"] == "See draws, schedules, standings."
    assert body["group_name"] == "Tournaments"
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]


async def test_create_permission_with_invalid_code_format_returns_422(
    client: AsyncClient, me: dict
) -> None:
    cases = ["tournaments", "TOURNAMENTS.READ", ".read", "tournaments.", "tournaments..read"]
    for bad in cases:
        response = await client.post(
            "/v1/permissions", headers=me["headers"], json=_payload(code=bad)
        )
        assert response.status_code == 422, bad


async def test_create_permission_with_duplicate_code_returns_409(
    client: AsyncClient, me: dict
) -> None:
    headers = me["headers"]
    first = await client.post("/v1/permissions", headers=headers, json=_payload())
    assert first.status_code == 201

    second = await client.post("/v1/permissions", headers=headers, json=_payload(name="Other name"))
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


async def test_get_permission_by_id_and_code(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/permissions", headers=headers, json=_payload())).json()

    by_id = await client.get(f"/v1/permissions/{created['id']}", headers=headers)
    by_code = await client.get(f"/v1/permissions/{created['code']}", headers=headers)

    assert by_id.status_code == 200
    assert by_code.status_code == 200
    assert by_id.json()["id"] == by_code.json()["id"] == created["id"]


async def test_get_permission_unknown_returns_404(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    by_code = await client.get("/v1/permissions/nope.nope", headers=headers)
    by_uuid = await client.get(
        "/v1/permissions/00000000-0000-0000-0000-000000000000", headers=headers
    )

    assert by_code.status_code == 404
    assert by_uuid.status_code == 404


async def test_list_permissions_returns_all_ordered(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    await client.post(
        "/v1/permissions",
        headers=headers,
        json=_payload(code="matches.score", name="Score", group_name="Matches"),
    )
    await client.post(
        "/v1/permissions",
        headers=headers,
        json=_payload(code="matches.read", name="View", group_name="Matches"),
    )
    await client.post(
        "/v1/permissions",
        headers=headers,
        json=_payload(code="tournaments.read", name="View", group_name="Tournaments"),
    )

    body = (await client.get("/v1/permissions", headers=headers)).json()
    codes = [p["code"] for p in body]
    # Ordered by group_name, then code
    assert codes == ["matches.read", "matches.score", "tournaments.read"]


async def test_patch_permission_updates_name_and_description(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/permissions", headers=headers, json=_payload())).json()

    response = await client.patch(
        f"/v1/permissions/{created['code']}",
        headers=headers,
        json={"name": "New name", "description": "Updated."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New name"
    assert body["description"] == "Updated."
    assert body["code"] == created["code"]


async def test_patch_permission_cannot_change_code(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/permissions", headers=headers, json=_payload())).json()

    response = await client.patch(
        f"/v1/permissions/{created['code']}",
        headers=headers,
        json={"code": "something.else"},
    )

    assert response.status_code == 422


async def test_delete_permission_returns_204(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/permissions", headers=headers, json=_payload())).json()

    deleted = await client.delete(f"/v1/permissions/{created['code']}", headers=headers)
    follow_up = await client.get(f"/v1/permissions/{created['code']}", headers=headers)

    assert deleted.status_code == 204
    assert follow_up.status_code == 404


async def test_delete_permission_cascades_role_assignments(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    perm = (await client.post("/v1/permissions", headers=headers, json=_payload())).json()
    role = (
        await client.post(
            "/v1/roles",
            headers=headers,
            json={"name": "Reader", "permission_ids": [perm["id"]]},
        )
    ).json()
    assert role["permission_ids"] == [perm["id"]]

    await client.delete(f"/v1/permissions/{perm['id']}", headers=headers)

    refreshed = (await client.get(f"/v1/roles/{role['slug']}", headers=headers)).json()
    assert refreshed["permission_ids"] == []


async def test_endpoints_require_auth(client: AsyncClient) -> None:
    no_auth: dict[str, str] = {}
    bad_auth = {"Authorization": "Bearer not.a.real.jwt"}

    cases = [
        ("GET", "/v1/permissions", None),
        ("POST", "/v1/permissions", _payload()),
        ("GET", "/v1/permissions/anything", None),
        ("PATCH", "/v1/permissions/anything", {"name": "x"}),
        ("DELETE", "/v1/permissions/anything", None),
    ]
    for method, path, body in cases:
        for headers in (no_auth, bad_auth):
            kwargs: dict = {"headers": headers}
            if body is not None:
                kwargs["json"] = body
            response = await client.request(method, path, **kwargs)
            assert response.status_code == 401, f"{method} {path} with {headers}"


async def test_openapi_exposes_permission_models(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    components = schema["components"]["schemas"]

    for name in ("PermissionPublic", "PermissionCreate", "PermissionUpdate"):
        assert name in components

    assert "/v1/permissions" in schema["paths"]
    assert "/v1/permissions/{permission}" in schema["paths"]
