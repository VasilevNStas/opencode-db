"""Команда vacuum: оптимизация базы данных."""

import argparse
import os
from typing import Literal

from config import OPENCODE_DB
from i18n import _
from utils import build_help_epilog, confirm

_VACUUM_EXAMPLES = [
    ("", "help.vacuum.e0"),
    ("--force", "help.vacuum.e1"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "vacuum",
        help=_("help.cmd.vacuum"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("vacuum", _VACUUM_EXAMPLES),
    )
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")


def run(args, db) -> Literal[0] | Literal[1]:
    try:
        size_before = os.path.getsize(OPENCODE_DB)
    except OSError:
        size_before = 0

    size_before_mb = size_before / (1024 * 1024)

    print(f"\n  {_('vacuum.header')}")
    print(f"  {'─' * 40}")
    print(f"  {_('vacuum.size_before')}:   {size_before_mb:.1f} MB")
    print(f"  {_('vacuum.path')}:        {OPENCODE_DB}")

    if not args.force and not confirm(_("vacuum.confirm")):
        print(_("vacuum.canceled"))
        return 0

    print(f"  {_('vacuum.vacuum')}", end=" ", flush=True)
    try:
        db.execute("VACUUM")
        print(_("vacuum.done"))
    except Exception as e:
        print(_("vacuum.error", error=e))
        return 1

    print(f"  {_('vacuum.reindex')}", end=" ", flush=True)
    try:
        db.execute("REINDEX")
        print(_("vacuum.done"))
    except Exception as e:
        print(_("vacuum.error", error=e))

    print(f"  {_('vacuum.analyze')}", end=" ", flush=True)
    try:
        db.execute("ANALYZE")
        print(_("vacuum.done"))
    except Exception as e:
        print(_("vacuum.error", error=e))

    try:
        size_after = os.path.getsize(OPENCODE_DB)
        size_after_mb = size_after / (1024 * 1024)
        saved = size_before - size_after
        saved_mb = saved / (1024 * 1024)
        print(f"\n  {_('vacuum.size_after')}: {size_after_mb:.1f} MB")
        if saved > 0:
            print(f"  {_('vacuum.freed')}:  {saved_mb:.1f} MB")
    except OSError:
        pass

    print()
    return 0
