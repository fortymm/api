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
