from httpx import AsyncClient


async def test_list_roles_empty(client: AsyncClient, me: dict) -> None:
    response = await client.get("/v1/roles", headers=me["headers"])

    assert response.status_code == 200
    assert response.json() == []


async def test_create_role_returns_public_role(client: AsyncClient, me: dict) -> None:
    response = await client.post(
        "/v1/roles",
        headers=me["headers"],
        json={"name": "Tournament Director", "description": "Run events end-to-end."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Tournament Director"
    assert body["slug"] == "tournament-director"
    assert body["description"] == "Run events end-to-end."
    assert body["member_count"] == 0
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]


async def test_create_role_collision_appends_suffix(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    first = await client.post("/v1/roles", headers=headers, json={"name": "Support"})
    second = await client.post("/v1/roles", headers=headers, json={"name": "support"})
    third = await client.post("/v1/roles", headers=headers, json={"name": "SUPPORT!"})

    assert first.json()["slug"] == "support"
    assert second.json()["slug"] == "support-2"
    assert third.json()["slug"] == "support-3"


async def test_create_role_ignores_permission_codes(client: AsyncClient, me: dict) -> None:
    response = await client.post(
        "/v1/roles",
        headers=me["headers"],
        json={"name": "Umpire", "permission_codes": ["matches.score", "matches.void"]},
    )

    assert response.status_code == 201
    assert "permission_codes" not in response.json()


async def test_get_role_by_id_and_slug(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/roles", headers=headers, json={"name": "Scorer"})).json()

    by_id = await client.get(f"/v1/roles/{created['id']}", headers=headers)
    by_slug = await client.get(f"/v1/roles/{created['slug']}", headers=headers)

    assert by_id.status_code == 200
    assert by_slug.status_code == 200
    assert by_id.json()["id"] == by_slug.json()["id"] == created["id"]


async def test_get_role_unknown_returns_404(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    by_slug = await client.get("/v1/roles/nope", headers=headers)
    by_uuid = await client.get("/v1/roles/00000000-0000-0000-0000-000000000000", headers=headers)

    assert by_slug.status_code == 404
    assert by_uuid.status_code == 404


async def test_patch_role_updates_name_and_description(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/roles", headers=headers, json={"name": "Old name"})).json()

    response = await client.patch(
        f"/v1/roles/{created['slug']}",
        headers=headers,
        json={"name": "New name", "description": "Updated."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New name"
    assert body["description"] == "Updated."
    assert body["slug"] == created["slug"]


async def test_patch_role_accepts_and_ignores_permission_codes(
    client: AsyncClient, me: dict
) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/roles", headers=headers, json={"name": "Reader"})).json()

    response = await client.patch(
        f"/v1/roles/{created['slug']}",
        headers=headers,
        json={"permission_codes": ["reports.read"]},
    )

    assert response.status_code == 200


async def test_delete_role_then_get_404s(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    created = (await client.post("/v1/roles", headers=headers, json={"name": "Temp"})).json()

    deleted = await client.delete(f"/v1/roles/{created['slug']}", headers=headers)
    follow_up = await client.get(f"/v1/roles/{created['slug']}", headers=headers)

    assert deleted.status_code == 204
    assert follow_up.status_code == 404


async def test_endpoints_require_auth(client: AsyncClient) -> None:
    no_auth: dict[str, str] = {}
    bad_auth = {"Authorization": "Bearer not.a.real.jwt"}

    cases = [
        ("GET", "/v1/roles", None),
        ("POST", "/v1/roles", {"name": "x"}),
        ("GET", "/v1/roles/anything", None),
        ("PATCH", "/v1/roles/anything", {"name": "x"}),
        ("DELETE", "/v1/roles/anything", None),
        ("GET", "/v1/roles/anything/members", None),
        ("PUT", "/v1/roles/anything/members/00000000-0000-0000-0000-000000000000", None),
        ("DELETE", "/v1/roles/anything/members/00000000-0000-0000-0000-000000000000", None),
    ]
    for method, path, body in cases:
        for headers in (no_auth, bad_auth):
            kwargs: dict = {"headers": headers}
            if body is not None:
                kwargs["json"] = body
            response = await client.request(method, path, **kwargs)
            assert response.status_code == 401, f"{method} {path} with {headers}"


async def test_openapi_exposes_role_models(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    components = schema["components"]["schemas"]

    for name in ("RolePublic", "RoleCreate", "RoleUpdate", "RoleMember"):
        assert name in components

    assert "/v1/roles" in schema["paths"]
    assert "/v1/roles/{role}" in schema["paths"]
    assert "/v1/roles/{role}/members" in schema["paths"]
    assert "/v1/roles/{role}/members/{user_id}" in schema["paths"]
