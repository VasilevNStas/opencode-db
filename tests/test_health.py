import json
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

from opencode_db.commands.cmd_health import run


def _ns(**kwargs):
    defaults = {"json": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _v1_db(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT);
        CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT);
        CREATE TABLE todo (session_id TEXT, content TEXT);
        CREATE TABLE project (id TEXT PRIMARY KEY, name TEXT);
    """)
    conn.execute("INSERT INTO session (id, title) VALUES ('ses_1', 'Test')")
    conn.commit()
    return conn


def _v2_db(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE session_v2 (id TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE session_message (id TEXT PRIMARY KEY, session_id TEXT);
        CREATE TABLE todo (session_id TEXT, content TEXT);
        CREATE TABLE project (id TEXT PRIMARY KEY, name TEXT);
    """)
    conn.commit()
    return conn


def test_health_json_v1(tmp_path, capsys) -> None:
    path = tmp_path / "v1.db"
    conn = _v1_db(path)
    with (
        patch("opencode_db.commands.cmd_health.resolve_db_path", return_value=(str(path), False)),
        patch(
            "opencode_db.commands.cmd_health.detect_db_users",
            return_value=SimpleNamespace(available=True, in_use=False, pids=(), method="lsof"),
        ),
    ):
        run(_ns(json=True), conn)

    data = json.loads(capsys.readouterr().out)
    assert data["schema"] == "v1"
    assert data["read_only"] is False
    assert data["file_size"] > 0
    assert data["page_count"] > 0
    assert data["freelist_bytes"] == 0
    assert data["in_use"] is False
    conn.close()


def test_health_text_v2_read_only(tmp_path, capsys) -> None:
    path = tmp_path / "v2.db"
    conn = _v2_db(path)
    with (
        patch("opencode_db.commands.cmd_health.resolve_db_path", return_value=(str(path), False)),
        patch(
            "opencode_db.commands.cmd_health.detect_db_users",
            return_value=SimpleNamespace(available=False, in_use=False, pids=(), method=None),
        ),
    ):
        run(_ns(), conn)

    output = capsys.readouterr().out
    assert "v2" in output
    assert "Read-only" in output or "Только чтение" in output
    assert "lsof/fuser" in output
    conn.close()


def test_health_unknown_schema(tmp_path, capsys) -> None:
    path = tmp_path / "unknown.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE something (id INTEGER)")
    conn.commit()
    with (
        patch("opencode_db.commands.cmd_health.resolve_db_path", return_value=(str(path), False)),
        patch(
            "opencode_db.commands.cmd_health.detect_db_users",
            return_value=SimpleNamespace(available=True, in_use=True, pids=(42,), method="lsof"),
        ),
    ):
        run(_ns(), conn)

    output = capsys.readouterr().out
    assert "unknown" in output
    assert "42" in output
    conn.close()


def test_health_lock_free(tmp_path, capsys) -> None:
    path = tmp_path / "free.db"
    conn = _v1_db(path)
    with (
        patch("opencode_db.commands.cmd_health.resolve_db_path", return_value=(str(path), False)),
        patch(
            "opencode_db.commands.cmd_health.detect_db_users",
            return_value=SimpleNamespace(available=True, in_use=False, pids=(), method="lsof"),
        ),
    ):
        run(_ns(json=True), conn)

    data = json.loads(capsys.readouterr().out)
    assert data["lock_check_available"] is True
    assert data["lock_check_method"] == "lsof"
    assert data["pids"] == []
    conn.close()
