import os
import sqlite3
from subprocess import CompletedProcess
from types import SimpleNamespace

import pytest

from opencode_db.maintenance import (
    MaintenanceError,
    auto_vacuum_label,
    backup_database,
    check_integrity,
    checkpoint_wal,
    collect_health,
    detect_db_users,
    format_bytes,
    free_space_check,
)


def _db_file(tmp_path):
    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO demo (value) VALUES ('hello')")
    conn.commit()
    return path, conn


class TestFormatBytes:
    def test_units(self) -> None:
        assert format_bytes(0) == "0 B"
        assert format_bytes(1024) == "1 KB"
        assert format_bytes(1024 * 1024) == "1 MB"
        assert format_bytes(1024**3) == "1.0 GB"
        assert format_bytes(None) == "?"


class TestIntegrity:
    def test_ok(self, tmp_path) -> None:
        _, conn = _db_file(tmp_path)
        result = check_integrity(conn)
        assert result.ok is True
        assert result.message == "ok"
        conn.close()

    def test_broken_database(self, tmp_path) -> None:
        path = tmp_path / "broken.db"
        path.write_bytes(b"not a sqlite database")
        conn = sqlite3.connect(path)
        result = check_integrity(conn)
        assert result.ok is False
        conn.close()


class TestCheckpoint:
    def test_non_wal_is_noop(self, tmp_path) -> None:
        _, conn = _db_file(tmp_path)
        ok, message = checkpoint_wal(conn)
        assert ok is True
        assert message.startswith("journal_mode=")
        conn.close()

    def test_wal_checkpoint(self, tmp_path) -> None:
        _, conn = _db_file(tmp_path)
        mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
        assert mode == "wal"
        conn.execute("INSERT INTO demo (value) VALUES ('wal')")
        conn.commit()
        ok, message = checkpoint_wal(conn)
        assert ok is True
        assert message == "ok"
        conn.close()


class TestDetectUsers:
    def test_no_tools(self, monkeypatch) -> None:
        monkeypatch.setattr("opencode_db.maintenance.shutil.which", lambda _: None)
        users = detect_db_users("/tmp/test.db")
        assert users.available is False
        assert users.in_use is False
        assert "lsof" in (users.error or "")

    def test_lsof_filters_own_pid(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "opencode_db.maintenance.shutil.which",
            lambda name: "/usr/bin/lsof" if name == "lsof" else None,
        )
        output = f"{os.getpid()}\n12345\n"
        monkeypatch.setattr(
            "opencode_db.maintenance.subprocess.run",
            lambda *args, **kwargs: CompletedProcess(args[0], 0, output, ""),
        )
        users = detect_db_users("/tmp/test.db")
        assert users.available is True
        assert users.method == "lsof"
        assert users.pids == (12345,)

    def test_lsof_no_users(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "opencode_db.maintenance.shutil.which",
            lambda name: "/usr/bin/lsof" if name == "lsof" else None,
        )
        monkeypatch.setattr(
            "opencode_db.maintenance.subprocess.run",
            lambda *args, **kwargs: CompletedProcess(args[0], 1, "", ""),
        )
        users = detect_db_users("/tmp/test.db")
        assert users.available is True
        assert users.pids == ()

    def test_fuser_fallback(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "opencode_db.maintenance.shutil.which",
            lambda name: "/usr/bin/fuser" if name == "fuser" else None,
        )
        monkeypatch.setattr(
            "opencode_db.maintenance.subprocess.run",
            lambda *args, **kwargs: CompletedProcess(args[0], 0, "777\n", ""),
        )
        users = detect_db_users("/tmp/test.db")
        assert users.available is True
        assert users.method == "fuser"
        assert users.pids == (777,)


class TestHealth:
    def test_basic_metrics(self, tmp_path) -> None:
        path, conn = _db_file(tmp_path)
        health = collect_health(conn, str(path))
        assert health.page_size > 0
        assert health.page_count > 0
        assert health.freelist_count == 0
        assert health.live_bytes > 0
        assert health.journal_mode == "delete"
        assert auto_vacuum_label(health.auto_vacuum) == "OFF (NONE)"
        conn.close()

    def test_freelist_after_delete(self, tmp_path) -> None:
        path = tmp_path / "bloat.db"
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA page_size=1024")
        conn.execute("CREATE TABLE demo (value BLOB)")
        conn.executemany(
            "INSERT INTO demo (value) VALUES (?)",
            [(b"x" * 800,) for _ in range(200)],
        )
        conn.commit()
        conn.execute("DELETE FROM demo")
        conn.commit()
        health = collect_health(conn, str(path))
        assert health.freelist_count > 0
        assert health.freelist_bytes > 0
        assert health.freelist_pct > 0
        conn.close()

    def test_auto_vacuum_label(self) -> None:
        assert auto_vacuum_label(2) == "INCREMENTAL"
        assert auto_vacuum_label(99) == "UNKNOWN (99)"


class TestBackup:
    def test_backup_is_consistent(self, tmp_path) -> None:
        path, conn = _db_file(tmp_path)
        backup = backup_database(conn, str(path))
        assert backup.startswith(f"{path}.bak.")
        assert os.path.exists(backup)
        check = sqlite3.connect(backup)
        assert check.execute("SELECT value FROM demo").fetchone()[0] == "hello"
        check.close()
        conn.close()

    def test_backup_verification_failure(self, tmp_path, monkeypatch) -> None:
        path, conn = _db_file(tmp_path)
        monkeypatch.setattr(
            "opencode_db.maintenance.check_integrity",
            lambda *_args, **_kwargs: SimpleNamespace(ok=False, message="bad"),
        )
        with pytest.raises(MaintenanceError):
            backup_database(conn, str(path))
        assert not list(tmp_path.glob("test.db.bak.*"))
        conn.close()


class TestFreeSpace:
    def test_with_backup_multiplier(self, tmp_path, monkeypatch) -> None:
        path, conn = _db_file(tmp_path)
        conn.close()
        monkeypatch.setattr(
            "opencode_db.maintenance.shutil.disk_usage",
            lambda _: SimpleNamespace(free=10**9),
        )
        result = free_space_check(str(path), with_backup=True)
        assert result.ok is True
        assert result.required == result.database_size * 2

    def test_not_enough_space(self, tmp_path, monkeypatch) -> None:
        path, conn = _db_file(tmp_path)
        conn.close()
        monkeypatch.setattr(
            "opencode_db.maintenance.shutil.disk_usage",
            lambda _: SimpleNamespace(free=1),
        )
        result = free_space_check(str(path), with_backup=True)
        assert result.ok is False
        assert result.free == 1
