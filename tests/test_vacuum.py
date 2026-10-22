import sqlite3
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from opencode_db.commands.cmd_vacuum import run
from opencode_db.maintenance import DbUsers, FreeSpace, IntegrityResult


def _args(**kwargs):
    defaults = {
        "force": True,
        "backup": None,
        "no_backup": False,
        "skip_lock_check": False,
        "full_check": False,
        "auto_vacuum": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _run(db_path, conn, args, users=None, patches=()):
    users = users or DbUsers(True, method="lsof")
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "opencode_db.commands.cmd_vacuum.resolve_db_path",
                return_value=(db_path, False),
            )
        )
        stack.enter_context(
            patch("opencode_db.commands.cmd_vacuum.detect_db_users", return_value=users)
        )
        for context in patches:
            stack.enter_context(context)
        return run(args, conn)


def test_refuses_when_database_is_in_use(db_file) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(db_file, conn, _args(), users=DbUsers(True, pids=(123,), method="lsof"))
    assert result == 1
    assert not list(Path(db_file).parent.glob("test.db.bak.*"))
    conn.close()


def test_refuses_unknown_lock_state(db_file) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(db_file, conn, _args(), users=DbUsers(False, error="no tools"))
    assert result == 1
    conn.close()


def test_skip_lock_check_allows_unknown(db_file, tmp_path) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(
        db_file,
        conn,
        _args(skip_lock_check=True),
        users=DbUsers(False, error="no tools"),
    )
    assert result == 0
    assert list(tmp_path.glob("test.db.bak.*"))
    conn.close()


def test_integrity_failure_aborts(db_file) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(
        db_file,
        conn,
        _args(),
        patches=[
            patch(
                "opencode_db.commands.cmd_vacuum.check_integrity",
                return_value=IntegrityResult(False, "bad"),
            )
        ],
    )
    assert result == 1
    conn.close()


def test_not_enough_space_aborts(db_file) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(
        db_file,
        conn,
        _args(),
        patches=[
            patch(
                "opencode_db.commands.cmd_vacuum.free_space_check",
                return_value=FreeSpace(False, 1, 100, 50),
            )
        ],
    )
    assert result == 1
    conn.close()


def test_no_backup_creates_no_file(db_file, tmp_path) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(db_file, conn, _args(no_backup=True))
    assert result == 0
    assert not list(tmp_path.glob("test.db.bak.*"))
    conn.close()


def test_auto_vacuum_is_opt_in(db_file) -> None:
    conn = sqlite3.connect(db_file)
    result = _run(db_file, conn, _args(auto_vacuum=True))
    assert result == 0
    assert conn.execute("PRAGMA auto_vacuum").fetchone()[0] == 2
    conn.close()


def test_v2_is_refused(tmp_path) -> None:
    path = tmp_path / "v2.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE session_v2 (id TEXT PRIMARY KEY);
        CREATE TABLE session_message (id TEXT PRIMARY KEY, session_id TEXT);
        CREATE TABLE todo (session_id TEXT);
        CREATE TABLE project (id TEXT PRIMARY KEY);
    """)
    conn.commit()
    result = _run(str(path), conn, _args())
    assert result == 1
    conn.close()


def test_wal_mode_is_preserved(db_file) -> None:
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.commit()
    result = _run(db_file, conn, _args())
    assert result == 0
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    conn.close()


def test_help_mentions_space_backup_and_wal(capsys) -> None:
    from opencode_db.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["vacuum", "--help"])
    output = capsys.readouterr().out
    assert "VACUUM" in output
    assert "Backup" in output or "backup" in output
    assert "WAL" in output
    assert "free space" in output or "свободного места" in output
