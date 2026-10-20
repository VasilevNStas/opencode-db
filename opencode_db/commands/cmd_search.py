"""Команда search: поиск по тексту сообщений и частей."""

import argparse

from ..db import SessionError
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_ts

_SEARCH_EXAMPLES = [
    ('"text"', "help.search.e0"),
    ('"text" --session ses_xxx', "help.search.e1"),
    ('"text" --json', "help.search.e2"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "search",
        help=_("help.cmd.search"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("search", _SEARCH_EXAMPLES),
    )
    p.add_argument("query", help="Search text")
    p.add_argument("--session", type=str, help="Limit to session")
    p.add_argument("--limit", type=int, default=30, help="Max results")
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> int:
    store = open_store(db)
    session_id = None
    if args.session:
        try:
            session_id = store.resolve_session_id(args.session)
        except SessionError as e:
            print(e.message)
            return 1

    raw_results = store.search(args.query, session_id=session_id, limit=args.limit)
    results = [
        {
            "session_id": item["session_id"][:24],
            "message_id": item["message_id"][:12],
            "role": item["role"],
            "time": format_ts(item["time_created"]) if item["time_created"] else "—",
            "snippet": item["snippet"],
        }
        for item in raw_results
    ]

    if args.json:
        from ..formatters import print_json

        print_json(results)
        return 0

    if not results:
        print(_("search.none", query=args.query))
        return 0

    print(_("search.header", query=args.query))
    print(f"  {'─' * 60}")

    for r in results:
        print(f"  [{r['time']}] {r['role']}  {r['session_id']}  msg:{r['message_id']}")
        print(f"    {r['snippet']}")
        print()

    print(_("search.found", n=len(results)))
    return 0
