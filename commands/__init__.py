"""Реестр команд. Импортирует модули команд и регистрирует их.

Каждый модуль (cmd_xxx.py) экспортирует:
  - register(subparsers) — регистрирует subparser
  - run(args, db) — выполняет команду

Добавление новой команды:
  1. Создать cmd_xxx.py
  2. Добавить import cmd_xxx
  3. Добавить "xxx": cmd_xxx в COMMANDS
"""

import cmd_costs
import cmd_delete
import cmd_export
import cmd_help
import cmd_info
import cmd_list
import cmd_projects
import cmd_prune
import cmd_search
import cmd_stats
import cmd_todos
import cmd_tree
import cmd_vacuum
import cmd_view

# Словарь {имя_команды: модуль}
# Модуль должен иметь register(subparsers) и run(args, db)
COMMANDS = {
    "list": cmd_list,
    "info": cmd_info,
    "export": cmd_export,
    "delete": cmd_delete,
    "costs": cmd_costs,
    "prune": cmd_prune,
    "search": cmd_search,
    "tree": cmd_tree,
    "projects": cmd_projects,
    "stats": cmd_stats,
    "todos": cmd_todos,
    "vacuum": cmd_vacuum,
    "view": cmd_view,
    "help": cmd_help,
}


def get_handler(name):
    return COMMANDS.get(name)


def get_all():
    return COMMANDS
