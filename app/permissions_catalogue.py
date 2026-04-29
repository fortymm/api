"""Static permission catalogue.

Permissions are not enforced or persisted — this module is a frozen list of the
29 permission codes the admin SPA renders, transcribed verbatim from the design.
A real `permissions` table and role↔permission assignments will replace this
later; until then, `GET /v1/permissions` reads from here.
"""

from typing import Final


def _g(key: str, label: str, perms: list[tuple[str, str, str]]) -> dict:
    return {
        "key": key,
        "label": label,
        "permissions": [
            {"code": code, "name": name, "description": description}
            for code, name, description in perms
        ],
    }


PERMISSION_GROUPS: Final[list[dict]] = [
    _g(
        "tournaments",
        "TOURNAMENTS",
        [
            ("tournaments.read", "View tournaments", "See draws, schedules, standings."),
            (
                "tournaments.create",
                "Create tournaments",
                "Spin up new events and configure formats.",
            ),
            (
                "tournaments.update",
                "Edit tournaments",
                "Modify draws, brackets, seeding, schedule.",
            ),
            (
                "tournaments.delete",
                "Delete tournaments",
                "Permanently remove an event and its history.",
            ),
            (
                "tournaments.publish",
                "Publish to spectator view",
                "Make a draw publicly visible.",
            ),
        ],
    ),
    _g(
        "matches",
        "MATCHES",
        [
            ("matches.read", "View match data", "Read scores, splits, rallies."),
            (
                "matches.score",
                "Score live matches",
                "Use the scoring console during live play.",
            ),
            (
                "matches.adjust",
                "Adjust historical scores",
                "Edit a match after it has been called.",
            ),
            ("matches.void", "Void / replay matches", "Discard a result and rematch."),
        ],
    ),
    _g(
        "players",
        "PLAYERS",
        [
            ("players.read", "View player profiles", "See ratings, history, club."),
            ("players.invite", "Invite players", "Send a sign-up link."),
            ("players.merge", "Merge duplicates", "Combine two profiles into one."),
            (
                "players.delete",
                "Delete players",
                "Hard-delete a profile and all matches.",
            ),
        ],
    ),
    _g(
        "solver",
        "SOLVER",
        [
            ("solver.run", "Run the SMT solver", "Trigger schedule generation."),
            (
                "solver.constraints",
                "Edit solver constraints",
                "Add / remove / weight constraints.",
            ),
            (
                "solver.override",
                "Override solver output",
                "Manually move a match against the solution.",
            ),
        ],
    ),
    _g(
        "users_access",
        "USERS & ACCESS",
        [
            ("users.read", "View users", "List FortyMM staff and their details."),
            ("users.invite", "Invite users", "Send an invite to join FortyMM staff."),
            (
                "users.update",
                "Edit user details",
                "Change name, email, club, contact info.",
            ),
            ("users.suspend", "Suspend / reactivate", "Temporarily revoke access."),
            ("users.delete", "Delete users", "Permanently remove a user account."),
            (
                "users.reset_pw",
                "Send password resets",
                "Trigger a reset email for any user.",
            ),
            ("roles.read", "View roles", "See role list and assignments."),
            (
                "roles.update",
                "Edit roles",
                "Create custom roles, change permissions.",
            ),
            ("roles.assign", "Assign roles to users", "Change a user's role."),
        ],
    ),
    _g(
        "reports",
        "REPORTS & DATA",
        [
            (
                "reports.read",
                "View reports",
                "Tournament summaries, court utilisation.",
            ),
            ("reports.export", "Export reports", "Download CSV / PDF."),
            (
                "audit.read",
                "Read audit log",
                "See every admin action across the platform.",
            ),
            ("billing.read", "View billing", "(There is none. Free forever.)"),
        ],
    ),
]
