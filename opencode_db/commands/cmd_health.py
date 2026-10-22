"""Команда health: read-only отчёт о хранилище SQLite."""

import argparse
from typing import Literal

from ..config import resolve_db_path
from ..formatters import print_json
from ..i18n import _
from ..maintenance import (
    auto_vacuum_label,
    collect_health,
    detect_db_users,
    format_bytes,
)
from ..schema import detect_schema
from ..utils import build_help_epilog

_HEALTH_EXAMPLES = [
    ("", "help.health.e0"),
    ("--json", "help.health.e1"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "health",
        help=_("help.cmd.health"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("health", _HEALTH_EXAMPLES),
    )
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[0]:
    db.execute("PRAGMA query_only=ON")
    db_path = resolve_db_path()[0]
    health = collect_health(db, db_path)
    schema = detect_schema(db)
    users = detect_db_users(db_path)

    data = {
        "db_path": db_path,
        "file_size": health.file_size,
        "wal_size": health.wal_size,
        "shm_size": health.shm_size,
        "page_size": health.page_size,
        "page_count": health.page_count,
        "freelist_count": health.freelist_count,
        "freelist_bytes": health.freelist_bytes,
        "freelist_pct": round(health.freelist_pct, 2),
        "live_bytes": health.live_bytes,
        "reclaimable_bytes": health.freelist_bytes,
        "auto_vacuum": health.auto_vacuum,
        "auto_vacuum_label": auto_vacuum_label(health.auto_vacuum),
        "journal_mode": health.journal_mode,
        "schema": schema.family.value,
        "schema_label": schema.label,
        "read_only": schema.read_only,
        "in_use": users.in_use,
        "pids": list(users.pids),
        "lock_check_available": users.available,
        "lock_check_method": users.method,
    }

    if args.json:
        print_json(data)
        return 0

    print()
    print(f"  {_('health.title')}")
    print(f"  {'─' * 50}")
    print(f"  {_('health.path'):16s}: {db_path}")
    print(f"  {_('health.file'):16s}: {format_bytes(health.file_size)}")
    if health.wal_size:
        print(f"  {_('health.wal'):16s}: {format_bytes(health.wal_size)}")
    if health.shm_size:
        print(f"  {_('health.shm'):16s}: {format_bytes(health.shm_size)}")
    print(f"  {_('health.pages'):16s}: {format_bytes(health.page_size)} × {health.page_count:,}")
    print(f"  {_('health.live'):16s}: {format_bytes(health.live_bytes)}")
    print(
        f"  {_('health.freelist'):16s}: {format_bytes(health.freelist_bytes)} "
        f"({health.freelist_pct:.1f}%)"
    )
    print(f"  {_('health.reclaimable'):16s}: ~{format_bytes(health.freelist_bytes)}")
    print(f"  {_('health.auto_vacuum'):16s}: {auto_vacuum_label(health.auto_vacuum)}")
    print(f"  {_('health.journal'):16s}: {health.journal_mode}")
    print(f"  {_('health.schema'):16s}: {schema.label}")
    print(
        f"  {_('health.read_only'):16s}: {_('health.yes') if schema.read_only else _('health.no')}"
    )

    if not users.available:
        print(f"  {_('health.lock'):16s}: {_('health.lock_unknown')}")
    elif users.in_use:
        pids = ", ".join(str(pid) for pid in users.pids)
        print(f"  {_('health.lock'):16s}: {_('health.lock_in_use', pids=pids)}")
    else:
        print(f"  {_('health.lock'):16s}: {_('health.lock_free')}")
    print()
    return 0
