"""Команда tree: дерево ветвления сессий."""

from typing import Literal

from db import get_session_title, resolve_session_id
from i18n import _
from utils import format_ts


def register(subparsers) -> None:
    p = subparsers.add_parser("tree", help=_("help.cmd.tree"))
    p.add_argument("session_id", nargs="?", help="Start from this session")
    p.add_argument("--project", type=str, help="Filter by project")
    p.add_argument("--depth", type=int, default=5, help="Max depth")


def _build_tree(db, parent_id, depth, max_depth, indent=0, visited=None):
    if visited is None:
        visited = set()
    if depth > max_depth:
        return []

    lines = []

    if parent_id is None:
        rows = db.execute("""
            SELECT id, title, time_created
            FROM session
            WHERE parent_id IS NULL
            ORDER BY time_created
        """).fetchall()
    else:
        rows = db.execute(
            """
            SELECT id, title, time_created
            FROM session
            WHERE parent_id = ?
            ORDER BY time_created
        """,
            (parent_id,),
        ).fetchall()

    for r in rows:
        if r["id"] in visited:
            continue
        visited.add(r["id"])

        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        title = get_session_title(r)
        created = format_ts(r["time_created"], "%Y-%m-%d")
        lines.append(f"{prefix}{r['id'][:24]}  {created}  {title}")

        lines.extend(_build_tree(db, r["id"], depth + 1, max_depth, indent + 1, visited))

    return lines


def run(args, db) -> Literal[0]:
    if args.session_id:
        full_id = resolve_session_id(db, args.session_id)
        info = db.execute(
            "SELECT id, title, time_created FROM session WHERE id = ?", (full_id,)
        ).fetchone()

        title = get_session_title(info)
        print(f"\n  {_('tree.header', title=title)}")
        print(f"  {'─' * 55}")

        lines = _build_tree(db, full_id, 1, args.depth, 0)
        for line in lines:
            print(f"  {line}")

    elif args.project:
        print(f"\n  {_('tree.header_project', project=args.project)}")
        print(f"  {'─' * 55}")

        lines = _build_tree(db, None, 1, args.depth, 0)
        project_lines = []
        for line in lines:
            sid = line.split("  ")[0].strip().lstrip("└─ ")
            row = db.execute("SELECT project_id FROM session WHERE id = ?", (sid,)).fetchone()
            if row and row["project_id"] == args.project:
                project_lines.append(line)
        for line in project_lines:
            print(f"  {line}")

    else:
        print(f"\n  {_('tree.header_all')}")
        print(f"  {'─' * 55}")
        lines = _build_tree(db, None, 1, args.depth, 0)
        for line in lines:
            print(f"  {line}")

    print()
    return 0
