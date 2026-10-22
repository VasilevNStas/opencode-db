"""Точка входа: парсинг аргументов и диспетчеризация команд.

Каждая команда регистрирует свой subparser через register(subparsers).
Это даёт:
  - Автоматический --help для каждой команды
  - Валидацию аргументов
  - Единообразный интерфейс
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Literal

from .runtime import require_python

require_python()

from . import commands  # noqa: E402
from .backups import BackupError, resolve_backup_source  # noqa: E402
from .db import get_db  # noqa: E402
from .i18n import _, set_lang  # noqa: E402
from .version import get_version  # noqa: E402

_WRITE_COMMANDS = {"delete", "prune", "vacuum"}
_DB_ENV = ("OPENCODE_DB", "OPENCODE_DB_READ_ONLY", "OPENCODE_DB_BACKUP_PATH")


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов со всеми подкомандами."""
    parser = argparse.ArgumentParser(
        prog="opencode-db",
        description="OpenCode database manager: browse, export, analyze, clean up sessions.",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ru"],
        default=None,
        help="Output language / язык вывода (en/ru)",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to opencode.db (default: ~/.local/share/opencode/opencode.db)",
    )
    source.add_argument(
        "--from-backup",
        type=str,
        default=None,
        help="Read from a managed backup file or alias (read-only)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    seen: set[str] = set()
    for mod in commands.get_all().values():
        if mod.__name__ in seen:
            continue
        seen.add(mod.__name__)
        mod.register(subparsers)
    return parser


def main(argv=None) -> Any | Literal[0] | Literal[1]:
    """Главная функция. Парсит аргументы, открывает БД, запускает команду.

    Args:
      argv: список аргументов (по умолчанию sys.argv[1:])

    Returns:
      int: код возврата (0 = успех, 1 = ошибка)
    """
    parser = build_parser()

    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.lang:
        set_lang(args.lang)

    previous_env = {name: os.environ.get(name) for name in _DB_ENV}
    source = None
    db = None
    needs_db = args.command != "backups"
    try:
        if needs_db and args.from_backup:
            try:
                source = resolve_backup_source(args.from_backup)
            except BackupError as exc:
                print(_("backup.source_error", error=exc))
                return 1
            os.environ["OPENCODE_DB"] = source.db_path
            os.environ["OPENCODE_DB_READ_ONLY"] = "1"
            os.environ["OPENCODE_DB_BACKUP_PATH"] = str(source.original_path)
        elif needs_db and args.db_path:
            os.environ["OPENCODE_DB"] = args.db_path

        if source is not None and args.command in _WRITE_COMMANDS:
            print(_("backup.read_only_command", command=args.command))
            return 1

        if needs_db:
            db = get_db(allow_unknown=args.command in {"schema", "health", "help"})
        handler = commands.get_handler(args.command)
        if handler is None:
            print(_("cmd.unknown", cmd=args.command))
            return 1
        return handler.run(args, db)
    finally:
        if db is not None:
            db.close()
        if source is not None:
            source.cleanup()
        for name, value in previous_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
