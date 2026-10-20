"""Команда directories: все директории запусков OpenCode."""

import argparse
from typing import Literal

from ..formatters import print_json, print_table_simple
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_cost, format_ts, shorten_path

_DIRECTORIES_EXAMPLES = [
    ("", "help.directories.e0"),
    ("--missing", "help.directories.e1"),
    ("--json", "help.directories.e2"),
    ("--no-check", "help.directories.e3"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "directories",
        aliases=["dirs"],
        help=_("help.cmd.directories"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("directories", _DIRECTORIES_EXAMPLES),
    )
    p.add_argument("--missing", action="store_true", help="Only missing directories")
    p.add_argument("--existing", action="store_true", help="Only existing directories")
    p.add_argument("--project", type=str, help="Filter by project ID")
    p.add_argument(
        "--sort",
        choices=["date", "sessions", "cost", "path"],
        default="date",
        help="Sort order (default: date)",
    )
    p.add_argument("--limit", type=int, default=50, help="Max results (default 50)")
    p.add_argument("--no-check", action="store_true", help="Skip filesystem check")
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[1] | Literal[0]:
    if getattr(args, "missing", False) and getattr(args, "existing", False):
        print(_("directories.conflict"))
        return 1

    entries = open_store(db).get_directories(check_exists=not getattr(args, "no_check", False))

    if getattr(args, "project", None):
        entries = [
            entry
            for entry in entries
            if args.project == entry["project_id"] or args.project in entry["project_ids"]
        ]
    if getattr(args, "missing", False):
        entries = [entry for entry in entries if entry["exists"] is False]
    elif getattr(args, "existing", False):
        entries = [entry for entry in entries if entry["exists"] is True]

    sorters = {
        "date": lambda entry: entry["last_ts"] or 0,
        "sessions": lambda entry: entry["sessions"],
        "cost": lambda entry: entry["cost"],
        "path": lambda entry: entry["path"],
    }
    reverse = getattr(args, "sort", "date") != "path"
    entries.sort(key=sorters[getattr(args, "sort", "date")], reverse=reverse)
    if getattr(args, "limit", 50):
        entries = entries[: getattr(args, "limit", 50)]

    if getattr(args, "json", False):
        data = [
            {
                "path": entry["path"],
                "exists": entry["exists"],
                "project_id": entry["project_id"],
                "project_ids": entry["project_ids"],
                "project": entry["project_label"],
                "is_global": entry["is_global"],
                "sessions": entry["sessions"],
                "first_activity": format_ts(entry["first_ts"]) if entry["first_ts"] else None,
                "last_activity": format_ts(entry["last_ts"]) if entry["last_ts"] else None,
                "tokens_input": entry["tokens_input"],
                "tokens_output": entry["tokens_output"],
                "tokens_reasoning": entry["tokens_reasoning"],
                "tokens_cache_read": entry["tokens_cache_read"],
                "tokens_cache_write": entry["tokens_cache_write"],
                "cost": entry["cost"],
                "sources": entry["sources"],
            }
            for entry in entries
        ]
        print_json(data)
        return 0

    if not entries:
        print(_("directories.none"))
        return 0

    status_icon = {True: "✓", False: "✗", None: "?"}
    table = []
    for entry in entries:
        status = {
            True: _("directories.exists"),
            False: _("directories.missing"),
            None: _("directories.unknown"),
        }[entry["exists"]]
        last = format_ts(entry["last_ts"], "%Y-%m-%d") if entry["last_ts"] else "—"
        table.append(
            [
                shorten_path(entry["path"], 52),
                f"{status_icon[entry['exists']]} {status}",
                entry["project_label"][:22],
                str(entry["sessions"]),
                last,
                format_cost(entry["cost"]),
            ]
        )

    print(f"\n  {_('directories.title')}")
    print_table_simple(
        [
            _("directories.header.path"),
            _("directories.header.status"),
            _("directories.header.project"),
            _("directories.header.sessions"),
            _("directories.header.last"),
            _("directories.header.cost"),
        ],
        table,
    )

    missing = sum(1 for entry in entries if entry["exists"] is False)
    sessions = sum(entry["sessions"] for entry in entries)
    print(_("directories.summary", total=len(entries), sessions=sessions, missing=missing))
    return 0
