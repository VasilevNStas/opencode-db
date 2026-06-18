"""Команда delete: удаление сессии."""

import argparse

from db import (
    SessionError,
    get_message_count,
    get_part_count,
    get_session_info,
    get_session_title,
    parse_model,
)
from i18n import _
from utils import build_help_epilog, confirm, format_cost, format_ts

_DELETE_EXAMPLES = [
    ("<session_id>", "help.delete.e0"),
    ("<session_id> --dry-run", "help.delete.e1"),
    ("<session_id> --force", "help.delete.e2"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "delete",
        help=_("help.cmd.delete"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("delete", _DELETE_EXAMPLES),
    )
    p.add_argument("session_id", help="Session ID to delete")
    p.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")


def run(args, db) -> int:
    try:
        info = get_session_info(db, args.session_id)
    except SessionError as e:
        print(e.message)
        return 1
    session_id = info["id"]
    title = get_session_title(info)
    model = parse_model(info)

    msg_count = get_message_count(db, session_id)
    part_count = get_part_count(db, session_id)
    created = format_ts(info["time_created"])

    print(f"\n{'=' * 50}")
    print(f"  {_('delete.header')}")
    print(f"{'=' * 50}")
    print(f"  {_('delete.id')}:         {session_id}")
    print(f"  {_('delete.title')}:   {title}")
    print(f"  {_('delete.model')}:     {model}")
    print(f"  {_('delete.created')}:    {created}")
    print(f"  {_('delete.messages')}:  {msg_count}")
    print(f"  {_('delete.parts')}:     {part_count}")
    print(f"  {_('delete.cost')}:  {format_cost(info['cost'])}")

    if args.dry_run:
        print(f"\n{_('delete.dry_run')}")
        print(f"  {_('delete.dry_run_hint')}")
        return 0

    if not args.force and not confirm(_("delete.confirm", id=session_id[:24])):
        print(_("canceled"))
        return 0

    db.execute("DELETE FROM session WHERE id = ?", (session_id,))
    db.commit()

    print(f"\n{_('delete.done', id=session_id[:24])}")
    print(_("delete.done_detail", msg=msg_count, parts=part_count))
    return 0
