from httpx import AsyncClient


async def _create_role(client: AsyncClient, headers: dict[str, str], name: str = "Crew") -> dict:
    response = await client.post("/v1/roles", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()


async def test_members_initially_empty(client: AsyncClient, me: dict) -> None:
    role = await _create_role(client, me["headers"])

    response = await client.get(f"/v1/roles/{role['slug']}/members", headers=me["headers"])

    assert response.status_code == 200
    assert response.json() == []


async def test_put_member_is_idempotent(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    role = await _create_role(client, headers)
    membership_url = f"/v1/roles/{role['slug']}/members/{me['user']['id']}"

    first = await client.put(membership_url, headers=headers)
    second = await client.put(membership_url, headers=headers)

    assert first.status_code == 204
    assert second.status_code == 204

    listing = await client.get(f"/v1/roles/{role['slug']}/members", headers=headers)
    body = listing.json()
    assert len(body) == 1
    assert body[0]["user"]["id"] == me["user"]["id"]
    assert body[0]["user"]["username"] == me["user"]["username"]
    assert body[0]["assigned_at"]


async def test_member_count_reflected_in_list(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    role = await _create_role(client, headers, name="With member")

    await client.put(f"/v1/roles/{role['slug']}/members/{me['user']['id']}", headers=headers)

    listing = (await client.get("/v1/roles", headers=headers)).json()
    matched = next(r for r in listing if r["slug"] == role["slug"])
    assert matched["member_count"] == 1


async def test_delete_member_removes(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    role = await _create_role(client, headers)
    membership_url = f"/v1/roles/{role['slug']}/members/{me['user']['id']}"

    await client.put(membership_url, headers=headers)
    removed = await client.delete(membership_url, headers=headers)
    again = await client.delete(membership_url, headers=headers)

    assert removed.status_code == 204
    assert again.status_code == 404


async def test_put_member_unknown_user_returns_404(client: AsyncClient, me: dict) -> None:
    role = await _create_role(client, me["headers"])

    response = await client.put(
        f"/v1/roles/{role['slug']}/members/00000000-0000-0000-0000-000000000000",
        headers=me["headers"],
    )

    assert response.status_code == 404


async def test_delete_role_cascades_memberships(client: AsyncClient, me: dict) -> None:
    headers = me["headers"]
    role = await _create_role(client, headers)

    await client.put(f"/v1/roles/{role['slug']}/members/{me['user']['id']}", headers=headers)
    await client.delete(f"/v1/roles/{role['slug']}", headers=headers)

    new_role = (await client.post("/v1/roles", headers=headers, json={"name": role["name"]})).json()
    assert new_role["slug"] == role["slug"]
    assert new_role["member_count"] == 0

    listing = (await client.get(f"/v1/roles/{new_role['slug']}/members", headers=headers)).json()
    assert listing == []
