"""Команда todos: просмотр задач (todo) из сессий."""

from typing import Literal

from db import resolve_session_id
from i18n import _
from utils import format_ts


def register(subparsers) -> None:
    p = subparsers.add_parser("todos", help=_("help.cmd.todos"))
    p.add_argument("session_id", nargs="?", help="Session ID")
    p.add_argument(
        "--status",
        choices=["pending", "completed", "cancelled"],
        help="Filter by status",
    )
    p.add_argument("--limit", type=int, default=30, help="Max entries")
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[0]:
    conditions = []
    params = []

    if args.session_id:
        full_id = resolve_session_id(db, args.session_id)
        conditions.append("t.session_id = ?")
        params.append(full_id)

    if args.status:
        conditions.append("t.status = ?")
        params.append(args.status)

    where = " AND ".join(conditions) if conditions else "1=1"

    rows = db.execute(
        f"""
        SELECT t.session_id, t.content, t.status, t.priority,
               t.position, t.time_created, t.time_updated,
               s.title as session_title
        FROM todo t
        JOIN session s ON s.id = t.session_id
        WHERE {where}
        ORDER BY t.time_created DESC
        LIMIT ?
    """,
        (*params, args.limit),
    ).fetchall()

    if args.json:
        from formatters import print_json

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
