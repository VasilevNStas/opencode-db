"""Команда list: список сессий с фильтрацией и сортировкой."""

from typing import Literal

import db as db_module
from db import get_session_title, parse_model
from formatters import print_json, print_table_simple
from i18n import _
from utils import format_ts


def register(subparsers) -> None:
    p = subparsers.add_parser("list", help=_("help.cmd.list"))
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
    conditions = []
    params = []

    if args.project:
        conditions.append("s.project_id = ?")
        params.append(args.project)

    if args.agent:
        conditions.append("s.agent = ?")
        params.append(args.agent)

    if args.model:
        conditions.append("s.model LIKE ?")
        params.append(f"%{args.model}%")

    where = " AND ".join(conditions) if conditions else "1=1"

    sort_map = {
        "date": "MAX(m.time_created) DESC",
        "cost": "s.cost DESC",
        "tokens": "(s.tokens_input + s.tokens_output) DESC",
        "messages": "msg_count DESC",
    }
    order = sort_map.get(args.sort, "MAX(m.time_created) DESC")

    limit = 999999 if args.all else args.limit

    rows = db.execute(
        f"""
        SELECT s.id, s.title, s.model, s.project_id, s.agent,
               s.cost, s.tokens_input, s.tokens_output,
               MAX(m.time_created) as last_time,
               COUNT(DISTINCT m.id) as msg_count
        FROM session s
        LEFT JOIN message m ON m.session_id = s.id
        WHERE {where}
        GROUP BY s.id
        ORDER BY {order}
        LIMIT ? OFFSET ?
    """,
        (*params, limit, args.offset),
    ).fetchall()

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
        project_name = db_module.get_project_name(db, r["project_id"]) if r["project_id"] else "—"
        model_name = parse_model(r)
        last_act = format_ts(r["last_time"], "%Y-%m-%d %H:%M") if r["last_time"] else "—"

        table_rows.append(
            [
                r["id"][:16],
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
