"""Команда help: подробная справка по opencode-db."""

import argparse
from typing import Literal

from ..i18n import _
from ..utils import build_help_epilog

_HELP_EXAMPLES = [
    ("", "help.help.e0"),
    ("<command>", "help.help.e1"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "help",
        help=_("help.cmd.help"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("help", _HELP_EXAMPLES),
    )
    p.add_argument("topic", nargs="?", help="Command name")
    p.add_argument("--json", action="store_true", help="JSON output")


_COMMANDS = [
    (
        "help",
        "help.cmd.help",
        [
            ("", "help.help.e0"),
            ("<command>", "help.help.e1"),
        ],
    ),
    (
        "list",
        "help.cmd.list",
        [
            ("", "help.list.e0"),
            ("--limit 10", "help.list.e1"),
            ("--sort cost", "help.list.e2"),
            ("--project proj_xxx", "help.list.e3"),
            ("--json", "help.list.e4"),
            ("--directory", "help.list.e5"),
        ],
    ),
    (
        "info",
        "help.cmd.info",
        [
            ("<session_id>", "help.info.e0"),
            ("<session_id> --json", "help.info.e1"),
        ],
    ),
    (
        "export",
        "help.cmd.export",
        [
            ("<session_id>", "help.export.e0"),
            ("--latest", "help.export.e1"),
            ("", "help.export.e2"),
            ("--full", "help.export.e3"),
            ("--force", "help.export.e4"),
            ('--note "text"', "help.export.e5"),
            ("--format json", "help.export.e6"),
            ("--last 5", "help.export.e7"),
            ("--since 2026-01-01", "help.export.e8"),
            ("--project proj_xxx", "help.export.e9"),
            ("--all", "help.export.e10"),
            ("--with-subagents", "help.export.e11"),
            ("--no-subagents", "help.export.e12"),
            ("--sanitize", "help.export.e13"),
        ],
    ),
    (
        "delete",
        "help.cmd.delete",
        [
            ("<session_id>", "help.delete.e0"),
            ("<session_id> --dry-run", "help.delete.e1"),
            ("<session_id> --force", "help.delete.e2"),
        ],
    ),
    (
        "digest",
        "help.cmd.digest",
        [
            ("<session_id>", "help.digest.e0"),
            ("<session_id> --last 3", "help.digest.e1"),
            ("<session_id> --json", "help.digest.e2"),
        ],
    ),
    (
        "costs",
        "help.cmd.costs",
        [
            ("", "help.costs.e0"),
            ("<session_id>", "help.costs.e1"),
            ("--total", "help.costs.e2"),
            ("--project proj_xxx", "help.costs.e3"),
            ("--json", "help.costs.e4"),
        ],
    ),
    (
        "prune",
        "help.cmd.prune",
        [
            ("--older-than 90d", "help.prune.e0"),
            ("--keep-last 20", "help.prune.e1"),
            ("--dry-run", "help.prune.e2"),
            ("--force", "help.prune.e3"),
        ],
    ),
    (
        "search",
        "help.cmd.search",
        [
            ('"text"', "help.search.e0"),
            ('"text" --session ses_1c9d', "help.search.e1"),
            ('"text" --json', "help.search.e2"),
        ],
    ),
    (
        "tree",
        "help.cmd.tree",
        [
            ("", "help.tree.e0"),
            ("<session_id>", "help.tree.e1"),
            ("--depth 3", "help.tree.e2"),
        ],
    ),
    (
        "projects",
        "help.cmd.projects",
        [
            ("", "help.projects.e0"),
            ("--json", "help.projects.e1"),
        ],
    ),
    (
        "directories",
        "help.cmd.directories",
        [
            ("", "help.directories.e0"),
            ("--missing", "help.directories.e1"),
            ("--json", "help.directories.e2"),
            ("--no-check", "help.directories.e3"),
        ],
    ),
    (
        "schema",
        "help.cmd.schema",
        [
            ("", "help.schema.e0"),
            ("--json", "help.schema.e1"),
        ],
    ),
    (
        "health",
        "help.cmd.health",
        [
            ("", "help.health.e0"),
            ("--json", "help.health.e1"),
        ],
    ),
    (
        "backup",
        "help.cmd.backup",
        [
            ("", "help.backup.e0"),
            ("--dry-run", "help.backup.e1"),
            ("--output ~/backups", "help.backup.e2"),
            ("--no-compress", "help.backup.e3"),
        ],
    ),
    (
        "backups",
        "help.cmd.backups",
        [
            ("list", "help.backups.e0"),
            ("view <file>", "help.backups.e1"),
            ("verify <file>", "help.backups.e2"),
            ("remove <file>", "help.backups.e3"),
            ("prune 5", "help.backups.e4"),
        ],
    ),
    (
        "stats",
        "help.cmd.stats",
        [
            ("", "help.stats.e0"),
            ("--json", "help.stats.e1"),
        ],
    ),
    (
        "todos",
        "help.cmd.todos",
        [
            ("", "help.todos.e0"),
            ("<session_id>", "help.todos.e1"),
            ("--status pending", "help.todos.e2"),
            ("--json", "help.todos.e3"),
        ],
    ),
    (
        "vacuum",
        "help.cmd.vacuum",
        [
            ("", "help.vacuum.e0"),
            ("--force", "help.vacuum.e1"),
            ("--no-backup", "help.vacuum.e2"),
            ("--auto-vacuum", "help.vacuum.e3"),
        ],
    ),
]

_COMMAND_MAP: dict[str, tuple[str, list]] = {}
for name, desc_key, examples in _COMMANDS:
    _COMMAND_MAP[name] = (desc_key, examples)


def _print_general_help() -> None:
    """Вывод полной справки."""
    print()
    print(f"  {_('help.header_box_top')}")
    print(f"  {_('help.header_title')}")
    print(f"  {_('help.header_box_bottom')}")
    print()
    print(f"  {_('help.intro')}")
    print(f"  {_('help.intro2')}")
    print()
    print(f"  {_('help.usage')}")
    print()

    for name, desc_key, examples in _COMMANDS:
        desc = _(desc_key)
        print(f"  {name:12s}  {desc}")
        for flag, example_key in examples:
            example_desc = _(example_key)
            if flag:
                print(f"    {'':12s}  opencode-db {name} {flag:30s}  # {example_desc}")
            else:
                print(f"    {'':12s}  opencode-db {name:33s}  # {example_desc}")
        print()

    print(f"  {'─' * 58}")
    print(f"  {_('help.footer')}")
    print(f"  {_('help.footer2')}")
    print(f"  {_('help.footer3')}")
    print()


def _print_command_help(cmd_name) -> Literal[1] | Literal[0]:
    """Вывод справки по одной команде."""
    entry = _COMMAND_MAP.get(cmd_name)
    if not entry:
        print(f"{_('help.unknown', cmd=cmd_name)}")
        print(f"   {_('help.available', cmds=', '.join(_COMMAND_MAP))}")
        return 1

    desc_key, examples = entry
    print()
    print(f"  {'─' * 55}")
    print(f"  {_('help.cmd_header', cmd=cmd_name, desc=_(desc_key))}")
    print(f"  {'─' * 55}")
    print()
    print(f"  {_('help.flags_header', cmd=cmd_name)}")
    print(f"    opencode-db {cmd_name} --help")
    print()
    print(f"  {_('help.usage_header', cmd=cmd_name)}")
    for flag, example_key in examples:
        example_desc = _(example_key)
        if flag:
            print(f"    opencode-db {cmd_name} {flag:30s}  # {example_desc}")
        else:
            print(f"    opencode-db {cmd_name:33s}  # {example_desc}")
    print()
    return 0


def run(args, db) -> Literal[1] | Literal[0]:
    import json

    if args.topic:
        return _print_command_help(args.topic)

    if args.json:
        data = []
        for name, desc_key, examples in _COMMANDS:
            data.append(
                {
                    "name": name,
                    "description": _(desc_key),
                    "examples": [
                        {"args": flag, "comment": _(example_key)} for flag, example_key in examples
                    ],
                }
            )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    _print_general_help()
    return 0
