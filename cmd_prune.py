"""Команда prune: массовая очистка (alias для delete)."""

import argparse

from cmd_delete import run as delete_run
from i18n import _
from utils import build_help_epilog

_PRUNE_EXAMPLES = [
    ("--older-than 90d", "help.prune.e0"),
    ("--keep-last 20", "help.prune.e1"),
    ("--dry-run", "help.prune.e2"),
    ("--force", "help.prune.e3"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "prune",
        help=_("help.cmd.prune"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("prune", _PRUNE_EXAMPLES),
    )
    p.add_argument("--older-than", type=str, help="Delete sessions older than (30d, 6m, 1y)")
    p.add_argument("--keep-last", type=int, help="Keep N most recent sessions")
    p.add_argument("--project", type=str, help="Limit to project")
    p.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")


def run(args, db) -> int:
    return delete_run(args, db)
