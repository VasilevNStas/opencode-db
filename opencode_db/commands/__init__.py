"""Реестр команд. Импортирует модули команд и регистрирует их.

Каждый модуль (cmd_xxx.py) экспортирует:
  - register(subparsers) — регистрирует subparser
  - run(args, db) — выполняет команду

Добавление новой команды:
  1. Создать opencode_db/commands/cmd_xxx.py
  2. Добавить `from . import cmd_xxx`
  3. Добавить "xxx": cmd_xxx в COMMANDS
"""

from . import (
    cmd_backup,
    cmd_backups,
    cmd_costs,
    cmd_delete,
    cmd_directories,
    cmd_export,
    cmd_health,
    cmd_help,
    cmd_info,
    cmd_list,
    cmd_projects,
    cmd_prune,
    cmd_schema,
    cmd_search,
    cmd_stats,
    cmd_todos,
    cmd_tree,
    cmd_vacuum,
    cmd_view,
)

# Словарь {имя_команды: модуль}
# Модуль должен иметь register(subparsers) и run(args, db)
COMMANDS = {
    "backup": cmd_backup,
    "backups": cmd_backups,
    "list": cmd_list,
    "info": cmd_info,
    "export": cmd_export,
    "delete": cmd_delete,
    "directories": cmd_directories,
    "dirs": cmd_directories,
    "costs": cmd_costs,
    "prune": cmd_prune,
    "search": cmd_search,
    "tree": cmd_tree,
    "projects": cmd_projects,
    "stats": cmd_stats,
    "schema": cmd_schema,
    "health": cmd_health,
    "todos": cmd_todos,
    "vacuum": cmd_vacuum,
    "view": cmd_view,
    "help": cmd_help,
}


def get_handler(name):
    return COMMANDS.get(name)


def get_all():
    return COMMANDS
