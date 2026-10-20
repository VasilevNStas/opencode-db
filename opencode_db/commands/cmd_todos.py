"""Команда todos: просмотр задач (todo) из сессий."""

import argparse

from ..db import SessionError
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_ts

_TODOS_EXAMPLES = [
    ("", "help.todos.e0"),
    ("<session_id>", "help.todos.e1"),
    ("--status pending", "help.todos.e2"),
    ("--json", "help.todos.e3"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "todos",
        help=_("help.cmd.todos"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("todos", _TODOS_EXAMPLES),
    )
    p.add_argument("session_id", nargs="?", help="Session ID")
    p.add_argument(
        "--status",
        choices=["pending", "completed", "cancelled"],
        help="Filter by status",
    )
    p.add_argument("--limit", type=int, default=30, help="Max entries")
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> int:
    store = open_store(db)
    session_id = None
    if args.session_id:
        try:
            session_id = store.resolve_session_id(args.session_id)
        except SessionError as e:
            print(e.message)
            return 1

    rows = store.get_todos_filtered(
        session_id=session_id,
        status=args.status,
        limit=args.limit,
    )

    if args.json:
        from ..formatters import print_json

        data = []
        for r in rows:
            data.append(
                {
                    "session_id": r["session_id"][:24],
                    "session_title": r["session_title"],
                    "content": r["content"],
                    "status": r["status"],
                    "priority": r["priority"],
                    "created": format_ts(r["time_created"]) if r["time_created"] else None,
                }
            )
        print_json(data)
        return 0

    if not rows:
        print(_("todos.none"))
        return 0

    status_icon = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
    priority_mark = {"high": " 🔴", "medium": "", "low": " 🟢"}

    print(_("todos.header", n=len(rows)))
    print(f"  {'─' * 55}")

    for r in rows:
        icon = status_icon.get(r["status"], "📝")
        prio = priority_mark.get(r["priority"], "")
        created = format_ts(r["time_created"], "%Y-%m-%d") if r["time_created"] else "—"
        title = r["session_title"] or "—"

        print(f"  {icon} {r['content'][:60]}{prio}")
        print(f"     {_('todos.session')}: {title[:40]}")
        print(f"     {_('todos.status')}: {r['status']}, {_('todos.created')}: {created}")
        print()

    return 0
