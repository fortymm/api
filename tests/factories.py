from httpx import AsyncClient


def permission_payload(**overrides) -> dict:
    base = {
        "code": "tournaments.read",
        "name": "View tournaments",
        "description": "See draws, schedules, standings.",
        "group_name": "Tournaments",
    }
    base.update(overrides)
    return base


async def create_permission(client: AsyncClient, headers: dict, **overrides) -> dict:
    response = await client.post(
        "/v1/permissions", headers=headers, json=permission_payload(**overrides)
    )
    assert response.status_code == 201, response.text
    return response.json()
