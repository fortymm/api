from httpx import AsyncClient

from tests.factories import create_permission as _create_permission


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
    assert body["permission_ids"] == []
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


async def test_create_role_with_permission_ids_persists_them(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    p1 = await _create_permission(
        client, headers, code="matches.score", name="Score", group_name="Matches"
    )
    p2 = await _create_permission(
        client, headers, code="matches.void", name="Void", group_name="Matches"
    )

    response = await client.post(
        "/v1/roles",
        headers=headers,
        json={"name": "Umpire", "permission_ids": [p1["id"], p2["id"]]},
    )

    assert response.status_code == 201
    body = response.json()
    assert sorted(body["permission_ids"]) == sorted([p1["id"], p2["id"]])


async def test_create_role_with_unknown_permission_id_returns_400(
    client: AsyncClient, me: dict
) -> None:
    bogus = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/v1/roles",
        headers=me["headers"],
        json={"name": "Bad", "permission_ids": [bogus]},
    )

    assert response.status_code == 400
    assert bogus in response.json()["detail"]


async def test_create_role_with_duplicate_permission_ids_dedups(
    client: AsyncClient, me: dict
) -> None:
    headers = me["headers"]
    perm = await _create_permission(client, headers)

    response = await client.post(
        "/v1/roles",
        headers=headers,
        json={"name": "Dup", "permission_ids": [perm["id"], perm["id"]]},
    )

    assert response.status_code == 201
    assert response.json()["permission_ids"] == [perm["id"]]


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


async def test_patch_role_replaces_permission_ids(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    p1 = await _create_permission(client, headers, code="a.read", name="A")
    p2 = await _create_permission(client, headers, code="b.read", name="B")
    p3 = await _create_permission(client, headers, code="c.read", name="C")

    created = (
        await client.post(
            "/v1/roles",
            headers=headers,
            json={"name": "Reader", "permission_ids": [p1["id"], p2["id"]]},
        )
    ).json()

    response = await client.patch(
        f"/v1/roles/{created['slug']}",
        headers=headers,
        json={"permission_ids": [p2["id"], p3["id"]]},
    )

    assert response.status_code == 200
    assert sorted(response.json()["permission_ids"]) == sorted([p2["id"], p3["id"]])


async def test_patch_role_with_null_permission_ids_leaves_them_untouched(
    client: AsyncClient, me: dict
) -> None:
    headers = me["headers"]
    perm = await _create_permission(client, headers)
    created = (
        await client.post(
            "/v1/roles",
            headers=headers,
            json={"name": "Reader", "permission_ids": [perm["id"]]},
        )
    ).json()

    response = await client.patch(
        f"/v1/roles/{created['slug']}",
        headers=headers,
        json={"description": "Updated."},
    )

    assert response.status_code == 200
    assert response.json()["permission_ids"] == [perm["id"]]


async def test_patch_role_with_empty_list_clears_permission_ids(
    client: AsyncClient, me: dict
) -> None:
    headers = me["headers"]
    perm = await _create_permission(client, headers)
    created = (
        await client.post(
            "/v1/roles",
            headers=headers,
            json={"name": "Reader", "permission_ids": [perm["id"]]},
        )
    ).json()

    response = await client.patch(
        f"/v1/roles/{created['slug']}",
        headers=headers,
        json={"permission_ids": []},
    )

    assert response.status_code == 200
    assert response.json()["permission_ids"] == []


async def test_list_roles_includes_permission_ids_for_each_role(
    client: AsyncClient, me: dict
) -> None:
    headers = me["headers"]
    p1 = await _create_permission(client, headers, code="a.read", name="A")
    p2 = await _create_permission(client, headers, code="b.read", name="B")

    await client.post(
        "/v1/roles",
        headers=headers,
        json={"name": "First", "permission_ids": [p1["id"]]},
    )
    await client.post(
        "/v1/roles",
        headers=headers,
        json={"name": "Second", "permission_ids": [p1["id"], p2["id"]]},
    )
    await client.post("/v1/roles", headers=headers, json={"name": "Third"})

    body = (await client.get("/v1/roles", headers=headers)).json()
    by_name = {r["name"]: r for r in body}
    assert by_name["First"]["permission_ids"] == [p1["id"]]
    assert sorted(by_name["Second"]["permission_ids"]) == sorted([p1["id"], p2["id"]])
    assert by_name["Third"]["permission_ids"] == []


async def test_delete_role_cascades_role_permissions(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    perm = await _create_permission(client, headers)
    created = (
        await client.post(
            "/v1/roles",
            headers=headers,
            json={"name": "Temp", "permission_ids": [perm["id"]]},
        )
    ).json()

    deleted = await client.delete(f"/v1/roles/{created['slug']}", headers=headers)
    assert deleted.status_code == 204

    # Permission still exists; the join row is gone.
    perm_after = await client.get(f"/v1/permissions/{perm['code']}", headers=headers)
    assert perm_after.status_code == 200


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

    assert "permission_ids" in components["RolePublic"]["properties"]

    assert "/v1/roles" in schema["paths"]
    assert "/v1/roles/{role}" in schema["paths"]
    assert "/v1/roles/{role}/members" in schema["paths"]
    assert "/v1/roles/{role}/members/{user_id}" in schema["paths"]
