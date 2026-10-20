"""Runtime detection of the OpenCode SQLite schema family.

The project supports the stable v1 schema and the preview v2 schema. Detection
is based on real tables and the migration journal, not on the OpenCode version
string, because a database can be older or newer than the binary that opens it.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path(__file__).with_name("schema_manifest.json")


class SchemaFamily(StrEnum):
    V1 = "v1"
    V2 = "v2"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SchemaInfo:
    family: SchemaFamily
    tables: frozenset[str]
    columns: dict[str, frozenset[str]]
    migrations: tuple[str, ...]
    max_migration: str | None
    capabilities: frozenset[str]
    warnings: tuple[str, ...] = ()
    manifest: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def read_only(self) -> bool:
        return "write" not in self.capabilities

    @property
    def supported(self) -> bool:
        return self.family is not SchemaFamily.UNKNOWN

    @property
    def label(self) -> str:
        labels = {
            SchemaFamily.V1: "v1 (OpenCode 1.19.x)",
            SchemaFamily.V2: "v2 preview (OpenCode 2.x)",
            SchemaFamily.UNKNOWN: "unknown",
        }
        return labels[self.family]


# Columns required by the commands. Extra columns are ignored on purpose: the
# upstream schema adds columns more often than it renames them.
REQUIRED: dict[SchemaFamily, dict[str, tuple[str, ...]]] = {
    SchemaFamily.V1: {
        "session": (
            "id",
            "title",
            "model",
            "cost",
            "tokens_input",
            "tokens_output",
            "tokens_reasoning",
            "time_created",
            "time_updated",
            "project_id",
            "parent_id",
        ),
        "message": ("id", "session_id", "time_created", "data"),
        "part": ("id", "message_id", "session_id", "time_created", "data"),
        "todo": ("session_id", "content", "status", "priority"),
        "project": ("id", "worktree", "name"),
    },
    SchemaFamily.V2: {
        "session_v2": (
            "id",
            "title",
            "model",
            "agent",
            "cost",
            "tokens_input",
            "tokens_output",
            "tokens_reasoning",
            "tokens_cache_read",
            "tokens_cache_write",
            "time_created",
            "time_updated",
            "project_id",
            "parent_id",
            "directory",
            "version",
        ),
        "session_message": (
            "id",
            "session_id",
            "type",
            "seq",
            "time_created",
            "time_updated",
            "data",
        ),
        "project": ("id", "worktree", "name"),
    },
    SchemaFamily.UNKNOWN: {},
}


@dataclass(frozen=True)
class SchemaIssue:
    kind: str
    table: str
    columns: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    """Load the generated upstream manifest. Missing file is non-fatal."""
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"families": {}}


def manifest_family(family: SchemaFamily) -> dict[str, Any]:
    return load_manifest().get("families", {}).get(family.value, {})


def _table_names(conn: sqlite3.Connection) -> frozenset[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return frozenset(str(row[0]) for row in rows)


def _table_columns(conn: sqlite3.Connection, table: str) -> frozenset[str]:
    escaped = table.replace('"', '""')
    rows = conn.execute(f'PRAGMA table_info("{escaped}")').fetchall()
    return frozenset(str(row[1]) for row in rows)


def _read_migrations(conn: sqlite3.Connection, tables: frozenset[str]) -> tuple[str, ...]:
    if "migration" in tables:
        try:
            rows = conn.execute("SELECT id FROM migration ORDER BY id").fetchall()
            return tuple(str(row[0]) for row in rows)
        except sqlite3.Error:
            pass

    if "__drizzle_migrations" in tables:
        try:
            columns = _table_columns(conn, "__drizzle_migrations")
            if "name" in columns:
                rows = conn.execute(
                    "SELECT name FROM __drizzle_migrations WHERE name IS NOT NULL ORDER BY id"
                ).fetchall()
                return tuple(str(row[0]) for row in rows)
        except sqlite3.Error:
            pass

    return ()


def detect_schema(conn: sqlite3.Connection) -> SchemaInfo:
    tables = _table_names(conn)
    columns = {table: _table_columns(conn, table) for table in tables}
    migrations = _read_migrations(conn, tables)
    max_migration = migrations[-1] if migrations else None

    if "session_v2" in tables:
        family = SchemaFamily.V2
        capabilities = frozenset({"read", "search", "stats", "todos"})
    elif "session" in tables:
        family = SchemaFamily.V1
        capabilities = frozenset({"read", "write", "search", "stats", "todos"})
    else:
        family = SchemaFamily.UNKNOWN
        capabilities = frozenset()

    warnings: list[str] = []
    manifest = manifest_family(family)
    if family is SchemaFamily.UNKNOWN:
        warnings.append("No OpenCode session table found (expected `session` or `session_v2`).")
    elif not manifest:
        warnings.append("Schema manifest is missing; detection is based on table names only.")
    else:
        known_max = manifest.get("max_migration")
        if max_migration and known_max and max_migration > str(known_max):
            warnings.append(
                f"Database migration {max_migration} is newer than the tested "
                f"{family.value} manifest ({known_max})."
            )

    return SchemaInfo(
        family=family,
        tables=tables,
        columns=columns,
        migrations=migrations,
        max_migration=max_migration,
        capabilities=capabilities,
        warnings=tuple(warnings),
        manifest=manifest,
    )


def schema_issues(info: SchemaInfo) -> list[SchemaIssue]:
    """Return missing tables/columns required by the current command set."""
    issues: list[SchemaIssue] = []
    for table, required_columns in REQUIRED.get(info.family, {}).items():
        if table not in info.tables:
            issues.append(SchemaIssue("table", table))
            continue
        missing = tuple(column for column in required_columns if column not in info.columns[table])
        if missing:
            issues.append(SchemaIssue("column", table, missing))
    return issues


def describe_schema(info: SchemaInfo) -> dict[str, Any]:
    """Stable, JSON-friendly description used by the `schema` command."""
    return {
        "family": info.family.value,
        "label": info.label,
        "db_path": None,
        "tables": sorted(info.tables),
        "table_count": len(info.tables),
        "migrations": list(info.migrations),
        "migration_count": len(info.migrations),
        "max_migration": info.max_migration,
        "capabilities": sorted(info.capabilities),
        "read_only": info.read_only,
        "supported": info.supported,
        "warnings": list(info.warnings),
        "manifest": {
            "ref": info.manifest.get("ref"),
            "commit": info.manifest.get("commit"),
            "max_migration": info.manifest.get("max_migration"),
            "message_types": info.manifest.get("message_types", []),
        },
    }
