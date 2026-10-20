import json
import sqlite3
from types import SimpleNamespace

from opencode_db.schema import (
    SchemaFamily,
    detect_schema,
    load_manifest,
    schema_issues,
)


def _v2_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT,
            name TEXT
        );
        CREATE TABLE session_v2 (
            id TEXT PRIMARY KEY,
            title TEXT,
            model TEXT,
            agent TEXT,
            cost REAL,
            tokens_input INTEGER,
            tokens_output INTEGER,
            tokens_reasoning INTEGER,
            tokens_cache_read INTEGER,
            tokens_cache_write INTEGER,
            time_created INTEGER,
            time_updated INTEGER,
            project_id TEXT,
            parent_id TEXT,
            directory TEXT,
            version TEXT
        );
        CREATE TABLE session_message (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            type TEXT,
            seq INTEGER,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT
        );
        CREATE TABLE migration (
            id TEXT PRIMARY KEY,
            time_completed INTEGER
        );
        INSERT INTO migration VALUES
            ('20260804233008_loose_psylocke', 1),
            ('20261010180456_project_time_archived', 2);
        """
    )
    return conn


def test_manifest_has_both_families() -> None:
    manifest = load_manifest()
    assert manifest["families"]["v1"]["ref"] == "v1.19.3"
    assert manifest["families"]["v2"]["ref"] == "v2.0.32"
    assert len(manifest["families"]["v1"]["migrations"]) == 38
    assert len(manifest["families"]["v2"]["migrations"]) == 50


def test_detect_v1(db) -> None:
    info = detect_schema(db)
    assert info.family is SchemaFamily.V1
    assert info.supported
    assert not info.read_only
    assert schema_issues(info) == []


def test_detect_v2() -> None:
    conn = _v2_db()
    info = detect_schema(conn)
    assert info.family is SchemaFamily.V2
    assert info.supported
    assert info.read_only
    assert info.max_migration == "20261010180456_project_time_archived"
    assert schema_issues(info) == []


def test_detect_unknown() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    info = detect_schema(conn)
    assert info.family is SchemaFamily.UNKNOWN
    assert not info.supported
    assert info.warnings


def test_drizzle_fallback_reads_migration_names() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE session (id TEXT PRIMARY KEY);
        CREATE TABLE __drizzle_migrations (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        INSERT INTO __drizzle_migrations (name) VALUES
            ('20260127222353_familiar_lady_ursula'),
            ('20260622202450_simplify_session_input');
        """
    )
    info = detect_schema(conn)
    assert info.family is SchemaFamily.V1
    assert info.max_migration == "20260622202450_simplify_session_input"


def test_newer_migration_warns(db) -> None:
    db.execute("CREATE TABLE migration (id TEXT PRIMARY KEY, time_completed INTEGER)")
    db.execute("INSERT INTO migration VALUES ('20990101000000_future', 1)")
    info = detect_schema(db)
    assert any("newer than the tested" in warning for warning in info.warnings)


def test_schema_command_v2(capsys) -> None:
    from opencode_db.commands import cmd_schema

    conn = _v2_db()
    code = cmd_schema.run(SimpleNamespace(json=True), conn)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["family"] == "v2"
    assert data["read_only"] is True
    assert data["max_migration"] == "20261010180456_project_time_archived"
