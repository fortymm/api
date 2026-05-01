import asyncio
from typing import Any

from arq.connections import RedisSettings
from ortools.sat.python import cp_model

from app.config import settings


def solve_hello_cpsat() -> dict[str, Any]:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 10, "x")
    y = model.new_int_var(0, 10, "y")
    model.add(x + y == 10)
    model.add(x >= y)

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT failed: {solver.status_name(status)}")

    return {
        "x": int(solver.value(x)),
        "y": int(solver.value(y)),
        "status": solver.status_name(status),
    }


async def hello_cpsat(_ctx: dict) -> dict[str, Any]:
    return await asyncio.to_thread(solve_hello_cpsat)


class WorkerSettings:
    functions = [hello_cpsat]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
