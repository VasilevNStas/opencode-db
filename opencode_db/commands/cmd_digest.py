"""Команда digest: сводки compaction для сессии."""

import argparse
from typing import Literal

from ..db import SessionError
from ..formatters import print_json
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_ts, summarize_val

_DIGEST_EXAMPLES = [
    ("<session_id>", "help.digest.e0"),
    ("<session_id> --last 3", "help.digest.e1"),
    ("<session_id> --json", "help.digest.e2"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "digest",
        help=_("help.cmd.digest"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("digest", _DIGEST_EXAMPLES),
    )
    p.add_argument("session_id", help="Session ID (full or prefix)")
    p.add_argument("--last", type=int, default=None, help="Show only the last N digests")
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[0] | Literal[1]:
    if args.last is not None and args.last < 1:
        print(_("digest.invalid_last"))
        return 1

    store = open_store(db)
    try:
        session_id = store.resolve_session_id(args.session_id)
        session_info = store.get_session_info(session_id)
    except SessionError as exc:
        print(exc.message)
        return 1

    digests = store.get_compaction_digests(session_id, args.last)
    title = store.get_session_title(session_info)
    data = {
        "session_id": session_id,
        "title": title,
        "schema": store.schema.family.value,
        "count": len(digests),
        "digests": digests,
    }
    if args.json:
        print_json(data)
        return 0

    print()
    print(f"  {_('digest.header', title=title)}")
    print(f"  {'─' * 56}")
    if not digests:
        print(f"  {_('digest.empty')}")
        print()
        return 0

    for index, digest in enumerate(digests, 1):
        ts = format_ts(digest["time_created"])
        meta = []
        if digest.get("agent"):
            meta.append(str(digest["agent"]))
        if digest.get("cost") is not None:
            meta.append(f"${digest['cost']:.6f}")
        suffix = f"  ({', '.join(meta)})" if meta else ""
        print(f"  {index:2d}. {ts}{suffix}")
        text = str(digest.get("text") or "").strip()
        if text:
            for line in summarize_val(text, 800).splitlines():
                print(f"      {line}")
        else:
            print(f"      {_('digest.no_text')}")
        print()

    return 0
