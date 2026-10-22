"""Команда vacuum: безопасная оптимизация базы данных."""

import argparse
import os
from typing import Literal

from ..config import resolve_db_path
from ..i18n import _
from ..maintenance import (
    MaintenanceError,
    auto_vacuum_label,
    backup_database,
    check_integrity,
    checkpoint_wal,
    collect_health,
    detect_db_users,
    format_bytes,
    free_space_check,
)
from ..store import open_store
from ..utils import build_help_epilog, confirm

_VACUUM_EXAMPLES = [
    ("", "help.vacuum.e0"),
    ("--force", "help.vacuum.e1"),
    ("--no-backup", "help.vacuum.e2"),
    ("--auto-vacuum", "help.vacuum.e3"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "vacuum",
        help=_("help.cmd.vacuum"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("vacuum", _VACUUM_EXAMPLES) + "\n\n" + _("help.vacuum.notes"),
    )
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    backup = p.add_mutually_exclusive_group()
    backup.add_argument(
        "--backup",
        action="store_true",
        default=None,
        help="Create a verified backup (default)",
    )
    backup.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup (not recommended)",
    )
    p.add_argument(
        "--skip-lock-check",
        action="store_true",
        help="Continue even if the database may be in use",
    )
    p.add_argument(
        "--full-check",
        action="store_true",
        help="Use full integrity_check instead of quick_check",
    )
    p.add_argument(
        "--auto-vacuum",
        action="store_true",
        help="Enable incremental auto-vacuum",
    )


def run(args, db) -> Literal[0] | Literal[1]:
    store = open_store(db)
    if store.schema.read_only:
        print(_("schema.unsupported_write"))
        return 1

    db_path = resolve_db_path()[0]
    health = collect_health(db, db_path)
    full_check = _arg(args, "full_check", False)
    with_backup = not _arg(args, "no_backup", False)
    if _arg(args, "backup", False) and _arg(args, "no_backup", False):
        print(_("vacuum.backup_conflict"))
        return 1

    users = detect_db_users(db_path)
    skip_lock = _arg(args, "skip_lock_check", False)
    if users.in_use and not skip_lock:
        pids = ", ".join(str(pid) for pid in users.pids)
        print(_("vacuum.lock_in_use", pids=pids))
        print(_("vacuum.close_opencode"))
        return 1
    if not users.available and not skip_lock:
        print(_("vacuum.lock_unknown"))
        print(_("vacuum.lock_unknown_hint"))
        return 1

    integrity = check_integrity(db, full=full_check)
    if not integrity.ok:
        print(_("vacuum.integrity_failed", message=integrity.message))
        return 1

    space = free_space_check(db_path, with_backup)
    if not space.ok:
        print(
            _(
                "vacuum.no_space",
                required=format_bytes(space.required),
                free=format_bytes(space.free),
            )
        )
        print(_("vacuum.no_space_hint"))
        return 1

    print()
    print(f"  {_('vacuum.header')}")
    print(f"  {'─' * 40}")
    print(f"  {_('vacuum.path'):<16s}: {db_path}")
    print(f"  {_('vacuum.size_before'):<16s}: {format_bytes(health.file_size)}")
    print(f"  {_('vacuum.wal'):<16s}: {format_bytes(health.wal_size)}")
    print(f"  {_('vacuum.freelist'):<16s}: {format_bytes(health.freelist_bytes)}")
    print(f"  {_('vacuum.journal'):<16s}: {health.journal_mode}")
    print(
        f"  {_('vacuum.backup'):<16s}: "
        f"{_('vacuum.backup_enabled') if with_backup else _('vacuum.backup_disabled')}"
    )
    print(
        f"  {_('vacuum.free_space'):<16s}: {format_bytes(space.free)} "
        f"({_('vacuum.required')}: ~{format_bytes(space.required)})"
    )
    if users.in_use:
        pids = ", ".join(str(pid) for pid in users.pids)
        print(f"  {_('vacuum.lock'):<16s}: {_('vacuum.lock_skipped', pids=pids)}")
    elif users.available:
        print(f"  {_('vacuum.lock'):<16s}: {_('vacuum.lock_free')}")
    else:
        print(f"  {_('vacuum.lock'):<16s}: {_('vacuum.lock_unknown_short')}")

    if not with_backup:
        print(_("vacuum.no_backup_warning"))

    if not _arg(args, "force", False) and not confirm(_("vacuum.confirm")):
        print(_("vacuum.canceled"))
        return 0

    ok, message = checkpoint_wal(db)
    if not ok:
        print(_("vacuum.checkpoint_failed", message=message))
        return 1
    print(f"  {_('vacuum.checkpoint')}: {_('vacuum.done')}")

    backup_path = None
    if with_backup:
        print(f"  {_('vacuum.backup_creating')}", end=" ", flush=True)
        try:
            backup_path = backup_database(db, db_path)
        except MaintenanceError as exc:
            print(_("vacuum.error", error=exc))
            return 1
        print(_("vacuum.done"))
        print(f"  {_('vacuum.backup_path')}: {backup_path}")
    else:
        print(f"  {_('vacuum.backup_skipped')}")

    if _arg(args, "auto_vacuum", False):
        db.execute("PRAGMA auto_vacuum = INCREMENTAL")
        mode = int(db.execute("PRAGMA auto_vacuum").fetchone()[0])
        print(f"  {_('vacuum.auto_vacuum')}: {auto_vacuum_label(mode)}")

    print(f"  {_('vacuum.vacuum')}", end=" ", flush=True)
    try:
        db.execute("VACUUM")
        print(_("vacuum.done"))
    except Exception as exc:
        print(_("vacuum.error", error=exc))
        return 1

    current_mode = str(db.execute("PRAGMA journal_mode").fetchone()[0]).lower()
    if health.journal_mode == "wal" and current_mode != "wal":
        try:
            restored = str(db.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
        except Exception as exc:
            print(_("vacuum.journal_restore_failed", error=exc))
            return 1
        if restored == "wal":
            print(f"  {_('vacuum.journal_restored')}")
        else:
            print(_("vacuum.journal_restore_failed", error=restored))
            return 1

    for label, statement in (
        ("vacuum.reindex", "REINDEX"),
        ("vacuum.analyze", "ANALYZE"),
    ):
        print(f"  {_(label)}", end=" ", flush=True)
        try:
            db.execute(statement)
            print(_("vacuum.done"))
        except Exception as exc:
            print(_("vacuum.error", error=exc))

    checkpoint_ok, checkpoint_message = checkpoint_wal(db)
    if not checkpoint_ok:
        print(_("vacuum.final_checkpoint_failed", message=checkpoint_message))

    final = check_integrity(db, full=full_check)
    if not final.ok:
        print(_("vacuum.post_check_failed", message=final.message))
        if backup_path:
            print(_("vacuum.restore_hint", backup=backup_path, path=db_path))
        return 1

    size_after = _file_size(db_path)
    saved = health.file_size - size_after
    print()
    print(f"  {_('vacuum.size_after')}: {format_bytes(size_after)}")
    if saved > 0:
        print(f"  {_('vacuum.freed')}:  {format_bytes(saved)}")
    else:
        print(f"  {_('vacuum.freed')}:  {format_bytes(0)}")
    if backup_path:
        print(f"  {_('vacuum.backup_path')}: {backup_path}")
    print()
    return 0


def _arg(args, name, default=False):
    return getattr(args, name, default)


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0
