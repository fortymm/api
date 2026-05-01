from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.jobs import solve_hello_cpsat
from app.main import app
from app.queue import get_queue


class _FakeJob:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id


class _FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    async def enqueue_job(self, function: str, *args: Any, **kwargs: Any) -> _FakeJob:
        self.enqueued.append((function, args, kwargs))
        return _FakeJob(job_id=str(uuid4()))


@pytest.fixture
def fake_queue() -> _FakeQueue:
    queue = _FakeQueue()

    async def override() -> _FakeQueue:
        return queue

    app.dependency_overrides[get_queue] = override
    try:
        yield queue
    finally:
        app.dependency_overrides.pop(get_queue, None)


def test_solve_hello_cpsat_returns_valid_solution() -> None:
    result = solve_hello_cpsat()

    assert result["x"] + result["y"] == 10
    assert result["x"] >= result["y"]
    assert result["status"] in ("OPTIMAL", "FEASIBLE")


async def test_post_hello_cpsat_enqueues_job(client: AsyncClient, fake_queue: _FakeQueue) -> None:
    response = await client.post("/v1/jobs/hello-cpsat")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"]
    assert fake_queue.enqueued == [("hello_cpsat", (), {})]


async def test_post_hello_cpsat_returns_503_when_enqueue_fails(
    client: AsyncClient,
) -> None:
    class NullQueue:
        async def enqueue_job(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    async def override() -> NullQueue:
        return NullQueue()

    app.dependency_overrides[get_queue] = override
    try:
        response = await client.post("/v1/jobs/hello-cpsat")
    finally:
        app.dependency_overrides.pop(get_queue, None)

    assert response.status_code == 503
