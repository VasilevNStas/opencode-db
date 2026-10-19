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
from .db import get_db  # noqa: E402
from .i18n import _, set_lang  # noqa: E402


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
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to opencode.db (default: ~/.local/share/opencode/opencode.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    for _name, mod in commands.get_all().items():
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

    if args.db_path:
        os.environ["OPENCODE_DB"] = args.db_path

    db = get_db()

    try:
        handler = commands.get_handler(args.command)
        if handler is None:
            print(_("cmd.unknown", cmd=args.command))
            return 1
        return handler.run(args, db)
    finally:
        db.close()
