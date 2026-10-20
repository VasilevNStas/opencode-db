"""Команда schema: семейство схемы, миграции и возможности."""

import argparse
from typing import Literal

from ..config import resolve_db_path
from ..formatters import print_json
from ..i18n import _
from ..schema import describe_schema, detect_schema
from ..utils import build_help_epilog

_SCHEMA_EXAMPLES = [
    ("", "help.schema.e0"),
    ("--json", "help.schema.e1"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "schema",
        help=_("help.cmd.schema"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("schema", _SCHEMA_EXAMPLES),
    )
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[0]:
    info = detect_schema(db)
    data = describe_schema(info)
    data["db_path"] = resolve_db_path()[0]

    if args.json:
        print_json(data)
        return 0

    print()
    print(f"  {_('schema.title')}")
    print(f"  {'─' * 50}")
    print(f"  {_('schema.db_path'):16s}: {data['db_path']}")
    print(f"  {_('schema.family'):16s}: {info.label}")
    print(f"  {_('schema.tables'):16s}: {data['table_count']}")
    print(f"  {_('schema.migrations'):16s}: {data['migration_count']}")
    print(f"  {_('schema.max_migration'):16s}: {info.max_migration or '—'}")
    capabilities = ", ".join(data["capabilities"]) or "—"
    print(f"  {_('schema.capabilities'):16s}: {capabilities}")

    manifest = data["manifest"]
    if manifest.get("ref"):
        commit = (manifest.get("commit") or "")[:10]
        print(f"  {_('schema.manifest'):16s}: {manifest['ref']} @ {commit}")

    for warning in data["warnings"]:
        print(_("schema.warning", message=warning))
    print()
    return 0
