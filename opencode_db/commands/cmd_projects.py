"""Команда projects: список проектов со статистикой."""

import argparse
import os
from typing import Literal

from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_cost, format_tokens, format_ts, shorten_path

_PROJECTS_EXAMPLES = [
    ("", "help.projects.e0"),
    ("--json", "help.projects.e1"),
    ("--no-global", "help.projects.e2"),
    ("--missing", "help.projects.e3"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "projects",
        help=_("help.cmd.projects"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("projects", _PROJECTS_EXAMPLES),
    )
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--no-global", action="store_true", help="Hide the Global project")
    p.add_argument("--missing", action="store_true", help="Only projects with a missing path")


def _project_view(r) -> dict:
    worktree = r["worktree"]
    is_global = r["id"] == "global"
    path = None if is_global else worktree
    exists = None if is_global else (os.path.isdir(path) if path else False)
    name = r["name"]
    if not name and path and not is_global:
        name = os.path.basename(str(path).rstrip("/")) or None
    return {
        "id": r["id"],
        "name": name,
        "worktree": worktree,
        "path": path,
        "exists": exists,
        "is_global": is_global,
        "time_created": format_ts(r["time_created"]) if r["time_created"] else None,
        "time_updated": format_ts(r["time_updated"]) if r["time_updated"] else None,
        "sessions": r["session_count"],
        "cost": r["total_cost"],
        "tokens_input": r["total_ti"],
        "tokens_output": r["total_to"],
        "tokens_reasoning": r["total_tr"],
        "tokens_total": r["total_ti"] + r["total_to"] + r["total_tr"],
    }


def run(args, db) -> Literal[0]:
    rows = open_store(db).get_projects()
    views = [_project_view(r) for r in rows]
    if getattr(args, "no_global", False):
        views = [v for v in views if not v["is_global"]]
    if getattr(args, "missing", False):
        views = [v for v in views if v["exists"] is False]

    if args.json:
        from ..formatters import print_json

        data = []
        for v in views:
            data.append(
                {
                    "id": v["id"],
                    "name": v["name"],
                    "worktree": v["worktree"],
                    "path": v["path"],
                    "exists": v["exists"],
                    "is_global": v["is_global"],
                    "time_created": v["time_created"],
                    "time_updated": v["time_updated"],
                    "sessions": v["sessions"],
                    "cost": v["cost"],
                    "tokens_input": v["tokens_input"],
                    "tokens_output": v["tokens_output"],
                    "tokens_reasoning": v["tokens_reasoning"],
                    "tokens_total": v["tokens_total"],
                }
            )
        print_json(data)
        return 0

    from ..formatters import print_table_simple

    if not views:
        print(_("projects.none"))
        return 0

    table = []
    for v in views:
        name = _("projects.global") if v["is_global"] else (v["name"] or "—")
        path = "—" if v["is_global"] else shorten_path(v["path"], 40)
        if v["exists"] is False:
            path = f"{path} ({_('projects.missing')})"
        updated = v["time_updated"][:10] if v["time_updated"] else "—"

        table.append(
            [
                v["id"][:12],
                name[:20],
                path,
                updated,
                str(v["sessions"]),
                format_tokens(v["tokens_total"]),
                format_cost(v["cost"]),
            ]
        )

    print_table_simple(
        [
            _("projects.header.id"),
            _("projects.header.name"),
            _("projects.header.path"),
            _("projects.header.activity"),
            _("projects.header.sessions"),
            _("projects.header.tokens"),
            _("projects.header.cost"),
        ],
        table,
    )

    return 0
