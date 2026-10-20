"""Команда tree: дерево ветвления сессий."""

import argparse

from ..db import SessionError
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_ts

_TREE_EXAMPLES = [
    ("", "help.tree.e0"),
    ("<session_id>", "help.tree.e1"),
    ("--depth 3", "help.tree.e2"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "tree",
        help=_("help.cmd.tree"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("tree", _TREE_EXAMPLES),
    )
    p.add_argument("session_id", nargs="?", help="Start from this session")
    p.add_argument("--project", type=str, help="Filter by project")
    p.add_argument("--depth", type=int, default=5, help="Max depth")


def _build_tree(store, parent_id, depth, max_depth, project_id=None, indent=0, visited=None):
    if visited is None:
        visited = set()
    if depth > max_depth:
        return []

    lines = []
    rows = store.get_tree_rows(parent_id, project_id)

    for row in rows:
        if row["id"] in visited:
            continue
        visited.add(row["id"])

        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        title = store.get_session_title(row)
        created = format_ts(row["time_created"], "%Y-%m-%d")
        lines.append(f"{prefix}{row['id'][:24]}  {created}  {title}")

        lines.extend(
            _build_tree(
                store,
                row["id"],
                depth + 1,
                max_depth,
                project_id,
                indent + 1,
                visited,
            )
        )

    return lines


def run(args, db) -> int:
    store = open_store(db)

    if args.session_id:
        try:
            full_id = store.resolve_session_id(args.session_id)
        except SessionError as e:
            print(e.message)
            return 1
        info = store.get_session_brief(full_id)
        if not info:
            print(_("session.not_found", session_id=args.session_id))
            return 1

        title = store.get_session_title(info)
        print(f"\n  {_('tree.header', title=title)}")
        print(f"  {'─' * 55}")

        lines = _build_tree(store, full_id, 1, args.depth)
        for line in lines:
            print(f"  {line}")

    elif args.project:
        print(f"\n  {_('tree.header_project', project=args.project)}")
        print(f"  {'─' * 55}")

        lines = _build_tree(store, None, 1, args.depth, project_id=args.project)
        for line in lines:
            print(f"  {line}")

    else:
        print(f"\n  {_('tree.header_all')}")
        print(f"  {'─' * 55}")
        lines = _build_tree(store, None, 1, args.depth)
        for line in lines:
            print(f"  {line}")

    print()
    return 0
