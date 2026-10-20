"""Команда prune: массовая очистка (alias для delete)."""

import argparse

from ..i18n import _
from ..utils import build_help_epilog
from .cmd_delete import run as delete_run

_PRUNE_EXAMPLES = [
    ("--older-than 90d", "help.prune.e0"),
    ("--keep-last 20", "help.prune.e1"),
    ("--dry-run", "help.prune.e2"),
    ("--force", "help.prune.e3"),
    ("--missing-directories", "help.prune.e4"),
    ("--missing-directories --execute", "help.prune.e5"),
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
    p.add_argument(
        "--missing-directories",
        action="store_true",
        help="Sessions whose directory no longer exists (preview by default)",
    )
    p.add_argument("--execute", action="store_true", help="Execute missing-directory cleanup")
    p.add_argument("--backup", action="store_true", help="Create a DB backup before deletion")
    p.add_argument("--no-backup", action="store_true", help="Skip the DB backup")


def run(args, db) -> int:
    return delete_run(args, db)
