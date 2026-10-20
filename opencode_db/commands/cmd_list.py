"""Команда list: список сессий с фильтрацией и сортировкой."""

import argparse
from typing import Literal

from ..db import get_session_title, parse_model
from ..formatters import print_json, print_table_simple
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_ts

_LIST_EXAMPLES = [
    ("", "help.list.e0"),
    ("--limit 10", "help.list.e1"),
    ("--sort cost", "help.list.e2"),
    ("--project proj_xxx", "help.list.e3"),
    ("--json", "help.list.e4"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "list",
        help=_("help.cmd.list"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("list", _LIST_EXAMPLES),
    )
    p.add_argument("--limit", type=int, default=25, help="Max results (default 25)")
    p.add_argument("--offset", type=int, default=0, help="Offset")
    p.add_argument("--project", type=str, help="Filter by project ID")
    p.add_argument("--agent", type=str, help="Filter by agent type")
    p.add_argument("--model", type=str, help="Filter by model name")
    p.add_argument(
        "--sort",
        choices=["date", "cost", "tokens", "messages"],
        default="date",
        help="Sort order (default: date)",
    )
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--all", action="store_true", help="Show all (no limit)")


def run(args, db) -> Literal[0]:
    store = open_store(db)
    limit = 999999 if args.all else args.limit
    rows = store.list_sessions(
        project_id=args.project,
        agent=args.agent,
        model=args.model,
        sort=args.sort,
        limit=limit,
        offset=args.offset,
    )

    if args.json:
        data = []
        for r in rows:
            data.append(
                {
                    "id": r["id"],
                    "title": get_session_title(r),
                    "project_id": r["project_id"],
                    "model": parse_model(r),
                    "agent": r["agent"],
                    "cost": r["cost"],
                    "tokens_input": r["tokens_input"],
                    "tokens_output": r["tokens_output"],
                    "messages": r["msg_count"],
                    "last_activity": format_ts(r["last_time"]) if r["last_time"] else None,
                }
            )
        print_json(data)
        return 0

    table_rows = []
    for r in rows:
        project_name = store.get_project_name(r["project_id"]) if r["project_id"] else "—"
        model_name = parse_model(r)
        last_act = format_ts(r["last_time"], "%Y-%m-%d %H:%M") if r["last_time"] else "—"

        table_rows.append(
            [
                r["id"][:24],
                get_session_title(r)[:32],
                project_name[:16],
                model_name[:20],
                last_act,
                str(r["msg_count"]),
                f"${r['cost']:.4f}" if r["cost"] else "—",
            ]
        )

    print_table_simple(
        [
            _("list.header.id"),
            _("list.header.title"),
            _("list.header.project"),
            _("list.header.model"),
            _("list.header.activity"),
            _("list.header.messages"),
            _("list.header.cost"),
        ],
        table_rows,
    )

    return 0
