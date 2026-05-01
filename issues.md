# Known issues / follow-ups

## Permissions API

### Race: permission deleted between FK validation and INSERT (low)
`_set_role_permissions` in `app/api/v1/roles.py` validates that all `permission_ids`
exist via a `SELECT`, then later issues `INSERT INTO role_permissions`. If another
request deletes one of the validated permissions in between, the INSERT raises
`IntegrityError` and bubbles up as a 500. Narrow window, but mappable to a 400 with
a useful detail. Catch `IntegrityError` in the helper and re-raise as
`HTTPException(400, "Unknown permission ids: ...")`.

### Undocumented response ordering (low)
`RolePublic.permission_ids` and the list returned by `GET /v1/permissions` are sorted
by UUID (via `sorted(desired)` in `_set_role_permissions` and `ORDER BY` clauses
elsewhere). Clients sending `[A, C, B]` get back `[A, B, C]`. Document this in the
Pydantic model description so the SPA doesn't accidentally rely on insertion order.

### Missing test cases (low)
- `PATCH /v1/permissions/{nonexistent}` → 404 path is uncovered.
- Diff-preservation: the whole point of the diff logic in `_set_role_permissions` is
  that `granted_at` stays unchanged when a permission stays in the set across a PATCH.
  Add a test that asserts `granted_at` doesn't move for unchanged rows.
- `create_role` failure path: when `_set_role_permissions` raises 400 *after* the role
  has been flushed, no orphan role should remain. Add a test:
  `POST /v1/roles` with valid name + bogus `permission_ids` → 400 →
  `GET /v1/roles` returns `[]`.

## Jobs API (arq + CP-SAT)

### `GET /v1/jobs/{id}` is untested (med)
`tests/test_jobs.py` covers the solver and the POST enqueue path, but the GET endpoint
in `app/api/v1/jobs.py` has zero coverage. All four branches are uncovered:
`not_found` → 404, `queued`/`in_progress` → status only, `complete` + `info.success` →
result, `complete` + failure → error. Add tests using `fakeredis.aioredis.FakeRedis`
so `arq.jobs.Job(job_id, redis=...)` round-trips through a stand-in Redis without
needing real infra in CI.

### No auth on `/v1/jobs/*` (med, blocks real jobs)
The new endpoints don't go through `parse_bearer_user` like `/v1/roles` etc. Anyone
can enqueue work or poll any job id. Job ids are random 16-byte hex so polling is
effectively unguessable, but enqueue is fully open. Acceptable for the hello-world
connection test; gate behind the existing bearer dependency before any non-trivial
job ships.

### `error=repr(info.result)` can leak internals (med, blocks real jobs)
`app/api/v1/jobs.py:46` returns `repr(info.result)` when a job fails. For real jobs
that may surface file paths, SQL fragments, stack-trace fragments, or secrets via the
public API. Replace with a sanitized payload (e.g. `{"type": type(info.result).__name__,
"detail": "Job failed"}`) and log the full repr server-side instead.

### Workers race on `alembic upgrade head` at startup (low)
`docker-entrypoint.sh` runs `alembic upgrade head` before exec, so every worker
container also runs migrations. Alembic takes a transactional lock so it's safe, but
N workers each try and (N-1) no-op. Consider a separate entrypoint for workers that
skips migrations, or gate migration runs to a single init container in deploy.

### Worker function name is a string literal (low)
`enqueue_job("hello_cpsat")` in `app/api/v1/jobs.py:28` references the worker function
by string. If the function in `app/jobs.py` is renamed, the call site silently breaks
at runtime. Once there are 2+ jobs, define a registry/enum so renames are caught at
import time.
