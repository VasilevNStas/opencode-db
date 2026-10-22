"""Команда backup: создать управляемый снимок БД."""

import argparse
from pathlib import Path
from typing import Literal

from ..backups import BackupError, create_backup
from ..config import get_backup_dir, resolve_db_path
from ..i18n import _
from ..maintenance import MaintenanceError, format_bytes
from ..utils import build_help_epilog

_BACKUP_EXAMPLES = [
    ("", "help.backup.e0"),
    ("--dry-run", "help.backup.e1"),
    ("--output ~/backups", "help.backup.e2"),
    ("--no-compress", "help.backup.e3"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "backup",
        help=_("help.cmd.backup"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("backup", _BACKUP_EXAMPLES),
    )
    p.add_argument("--output", type=str, help="Backup directory")
    p.add_argument(
        "--no-compress",
        action="store_true",
        help="Store an uncompressed .db snapshot",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing anything",
    )


def run(args, db) -> Literal[0] | Literal[1]:
    db_path = resolve_db_path()[0]
    directory = str(Path(args.output or get_backup_dir()).expanduser())
    compress = not args.no_compress

    print()
    print(f"  {_('backup.header')}")
    print(f"  {'─' * 48}")
    print(f"  {_('backup.source'):16s}: {db_path}")
    print(f"  {_('backup.output'):16s}: {directory}")
    print(
        f"  {_('backup.format'):16s}: "
        f"{_('backup.format_gzip') if compress else _('backup.format_plain')}"
    )

    if args.dry_run:
        print(f"  {_('backup.dry_run'):16s}: {_('backup.dry_run_hint')}")
        print()
        return 0

    try:
        path, entry = create_backup(db, db_path, backup_dir=directory, compress=compress)
    except (BackupError, MaintenanceError, OSError) as exc:
        print(_("backup.error", error=exc))
        return 1

    print()
    print(_("backup.saved", path=path))
    print(
        _(
            "backup.size",
            size=format_bytes(entry.size),
            raw=format_bytes(entry.raw_size),
        )
    )
    print(
        _(
            "backup.counts",
            sessions=entry.sessions,
            messages=entry.messages,
            parts=entry.parts,
        )
    )
    print(_("backup.sha", sha=entry.sha256))
    print()
    return 0
