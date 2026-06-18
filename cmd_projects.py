"""Команда projects: список проектов со статистикой."""

import argparse
from typing import Literal

from i18n import _
from utils import build_help_epilog, format_cost, format_tokens, format_ts

_PROJECTS_EXAMPLES = [
    ("", "help.projects.e0"),
    ("--json", "help.projects.e1"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "projects",
        help=_("help.cmd.projects"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("projects", _PROJECTS_EXAMPLES),
    )
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[0]:
    rows = db.execute("""
        SELECT p.id, p.name, p.worktree, p.time_created, p.time_updated,
               COUNT(DISTINCT s.id) as session_count,
               COALESCE(SUM(s.cost), 0) as total_cost,
               COALESCE(SUM(s.tokens_input), 0) as total_ti,
               COALESCE(SUM(s.tokens_output), 0) as total_to,
               COALESCE(SUM(s.tokens_reasoning), 0) as total_tr
        FROM project p
        LEFT JOIN session s ON s.project_id = p.id
        GROUP BY p.id
        ORDER BY p.time_updated DESC
    """).fetchall()

    if args.json:
        from formatters import print_json

        data = []
        for r in rows:
            data.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "worktree": r["worktree"],
                    "time_created": format_ts(r["time_created"]) if r["time_created"] else None,
                    "time_updated": format_ts(r["time_updated"]) if r["time_updated"] else None,
                    "sessions": r["session_count"],
                    "cost": r["total_cost"],
                    "tokens_input": r["total_ti"],
                    "tokens_output": r["total_to"],
                    "tokens_reasoning": r["total_tr"],
                    "tokens_total": r["total_ti"] + r["total_to"] + r["total_tr"],
                }
            )
        print_json(data)
        return 0

    from formatters import print_table_simple

    table = []
    for r in rows:
        name = r["name"] or "—"
        updated = format_ts(r["time_updated"], "%Y-%m-%d") if r["time_updated"] else "—"
        total_tokens = r["total_ti"] + r["total_to"] + r["total_tr"]

        table.append(
            [
                r["id"][:12],
                name[:20],
                updated,
                str(r["session_count"]),
                format_tokens(total_tokens),
                format_cost(r["total_cost"]),
            ]
        )

    print_table_simple(
        [
            _("projects.header.id"),
            _("projects.header.name"),
            _("projects.header.activity"),
            _("projects.header.sessions"),
            _("projects.header.tokens"),
            _("projects.header.cost"),
        ],
        table,
    )

    return 0
