"""Команда backups: управление сохранёнными снимками БД."""

import argparse
from typing import Literal

from ..backups import (
    BackupError,
    entry_path,
    file_sha256,
    find_entry,
    load_manifest,
    prune_backups,
    remove_backup,
    summary_for_connection,
    verify_backup,
)
from ..formatters import print_json, print_table_simple
from ..i18n import _
from ..maintenance import format_bytes
from ..utils import build_help_epilog, confirm

_BACKUPS_EXAMPLES = [
    ("list", "help.backups.e0"),
    ("view <file>", "help.backups.e1"),
    ("verify <file>", "help.backups.e2"),
    ("remove <file>", "help.backups.e3"),
    ("prune 5", "help.backups.e4"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "backups",
        help=_("help.cmd.backups"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("backups", _BACKUPS_EXAMPLES),
    )
    actions = p.add_subparsers(dest="backups_action", required=True)

    listing = actions.add_parser("list", help=_("help.backups.list"))
    listing.add_argument("--dir", type=str, help="Backup directory")
    listing.add_argument("--json", action="store_true", help="JSON output")

    view = actions.add_parser("view", help=_("help.backups.view"))
    view.add_argument("file")
    view.add_argument("--dir", type=str, help="Backup directory")
    view.add_argument("--json", action="store_true", help="JSON output")

    verify = actions.add_parser("verify", help=_("help.backups.verify"))
    verify.add_argument("file")
    verify.add_argument("--dir", type=str, help="Backup directory")

    remove = actions.add_parser("remove", help=_("help.backups.remove"))
    remove.add_argument("file")
    remove.add_argument("--dir", type=str, help="Backup directory")
    remove.add_argument("--yes", action="store_true", help="Skip confirmation")

    prune = actions.add_parser("prune", help=_("help.backups.prune"))
    prune.add_argument("keep", type=int, help="Number of newest backups to keep")
    prune.add_argument("--dir", type=str, help="Backup directory")
    prune.add_argument("--yes", action="store_true", help="Skip confirmation")


def run(args, db) -> Literal[0] | Literal[1]:
    action = args.backups_action
    if action == "list":
        return _list(args)
    if action == "view":
        return _view(args, db)
    if action == "verify":
        return _verify(args)
    if action == "remove":
        return _remove(args)
    if action == "prune":
        return _prune(args)
    print(_("cmd.unknown", cmd=action))
    return 1


def _entries(args):
    try:
        return load_manifest(getattr(args, "dir", None))
    except BackupError as exc:
        print(_("backups.error", error=exc))
        return None


def _list(args) -> Literal[0] | Literal[1]:
    entries = _entries(args)
    if entries is None:
        return 1
    if args.json:
        print_json([entry.to_dict() for entry in entries])
        return 0
    if not entries:
        print(_("backups.empty"))
        return 0

    rows = []
    for entry in entries:
        rows.append(
            [
                entry.created_at,
                entry.file,
                format_bytes(entry.size),
                entry.schema,
                str(entry.sessions),
                str(entry.messages),
            ]
        )
    print_table_simple(
        [
            _("backups.header.date"),
            _("backups.header.file"),
            _("backups.header.size"),
            _("backups.header.schema"),
            _("backups.header.sessions"),
            _("backups.header.messages"),
        ],
        rows,
    )
    return 0


def _view(args, db) -> Literal[0] | Literal[1]:
    entries = _entries(args)
    if entries is None:
        return 1
    entry = find_entry(args.file, entries)
    if entry is None:
        print(_("backups.not_found", file=args.file))
        return 1

    path = entry_path(entry, getattr(args, "dir", None))
    exists = path.is_file()
    try:
        sha_ok = exists and file_sha256(path) == entry.sha256
    except OSError:
        sha_ok = False
    aligned = None
    if db is not None:
        try:
            live = summary_for_connection(db, include_parts=False)
            aligned = (
                entry.sessions == live.get("sessions")
                and entry.messages == live.get("messages")
                and entry.max_updated == live.get("max_updated")
            )
        except Exception:
            aligned = None

    data = entry.to_dict()
    data.update({"path": str(path), "exists": exists, "sha256_ok": sha_ok, "aligned": aligned})
    if args.json:
        print_json(data)
        return 0

    print()
    print(f"  {_('backups.view_title')}")
    print(f"  {'─' * 48}")
    print(f"  {_('backups.header.file'):16s}: {entry.file}")
    print(f"  {_('backups.view.path'):16s}: {path}")
    print(f"  {_('backups.header.date'):16s}: {entry.created_at}")
    print(f"  {_('backups.header.size'):16s}: {format_bytes(entry.size)}")
    print(f"  {_('backups.view.raw_size'):16s}: {format_bytes(entry.raw_size)}")
    print(
        f"  {_('backups.view.compression'):16s}: "
        f"{_('backups.view.gzip') if entry.compressed else _('backups.view.plain')}"
    )
    print(f"  {_('backups.header.schema'):16s}: {entry.schema}")
    print(f"  {_('backups.header.sessions'):16s}: {entry.sessions}")
    print(f"  {_('backups.header.messages'):16s}: {entry.messages}")
    print(f"  {_('backups.header.parts'):16s}: {entry.parts}")
    print(f"  {_('backups.view.max_updated'):16s}: {entry.max_updated or '—'}")
    print(f"  {_('backups.view.source'):16s}: {entry.source}")
    print(
        f"  {_('backups.view.sha256'):16s}: "
        f"{_('backups.view.ok') if sha_ok else _('backups.view.bad')}"
    )
    if aligned is None:
        alignment = _("backups.view.alignment_unknown")
    elif aligned:
        alignment = _("backups.view.aligned")
    else:
        alignment = _("backups.view.out_of_sync")
    print(f"  {_('backups.view.alignment'):16s}: {alignment}")
    print()
    return 0


def _verify(args) -> Literal[0] | Literal[1]:
    entries = _entries(args)
    if entries is None:
        return 1
    entry = find_entry(args.file, entries)
    if entry is None:
        print(_("backups.not_found", file=args.file))
        return 1
    ok, message = verify_backup(entry, getattr(args, "dir", None))
    if not ok:
        print(_("backups.verify_failed", file=entry.file, error=message))
        return 1
    print(_("backups.verify_ok", file=entry.file, message=message))
    return 0


def _remove(args) -> Literal[0] | Literal[1]:
    entries = _entries(args)
    if entries is None:
        return 1
    entry = find_entry(args.file, entries)
    if entry is None:
        print(_("backups.not_found", file=args.file))
        return 1
    if not args.yes and not confirm(_("backups.remove_confirm", file=entry.file)):
        print(_("canceled"))
        return 0
    try:
        path = remove_backup(entry, getattr(args, "dir", None))
    except BackupError as exc:
        print(_("backups.error", error=exc))
        return 1
    print(_("backups.removed", file=entry.file))
    print(_("backups.removed_path", path=path))
    return 0


def _prune(args) -> Literal[0] | Literal[1]:
    entries = _entries(args)
    if entries is None:
        return 1
    if args.keep < 1:
        print(_("backups.prune_invalid"))
        return 1
    if len(entries) <= args.keep:
        print(_("backups.prune_nothing", keep=args.keep))
        return 0
    count = len(entries) - args.keep
    if not args.yes and not confirm(_("backups.prune_confirm", count=count, keep=args.keep)):
        print(_("canceled"))
        return 0
    try:
        removed = prune_backups(args.keep, getattr(args, "dir", None))
    except BackupError as exc:
        print(_("backups.error", error=exc))
        return 1
    print(_("backups.prune_done", count=len(removed), keep=args.keep))
    return 0
