import json
import os
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from opencode_db.backups import (
    BackupError,
    backup_status,
    create_backup,
    is_gzip,
    load_manifest,
    prune_backups,
    remove_backup,
    resolve_backup_source,
    verify_backup,
)
from opencode_db.commands import cmd_backup, cmd_backups
from opencode_db.commands.cmd_health import run as health_run


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _create(db, backup_dir, compress=False):
    return create_backup(db, "/tmp/opencode.db", backup_dir=str(backup_dir), compress=compress)


def test_create_backup_plain_writes_manifest(db, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    path, entry = _create(db, backup_dir)

    assert Path(path).is_file()
    assert entry.compressed is False
    assert entry.sessions == 4
    assert entry.messages == 5
    assert entry.parts == 7
    assert entry.schema == "v1"
    assert len(entry.sha256) == 64
    assert os.stat(path).st_mode & 0o777 == 0o600

    manifest = json.loads((backup_dir / "manifest.json").read_text())
    assert manifest["version"] == 1
    assert manifest["backups"][0]["file"] == entry.file

    entries = load_manifest(str(backup_dir))
    assert entries == [entry]


def test_create_backup_gzip_and_read(db, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    path, entry = _create(db, backup_dir, compress=True)

    assert path.endswith(".db.gz")
    assert is_gzip(path)
    assert entry.compressed is True
    assert entry.size < entry.raw_size

    source = resolve_backup_source(entry.file, str(backup_dir))
    assert source.temporary is True
    assert Path(source.db_path).is_file()
    conn = sqlite3.connect(source.db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM session").fetchone()[0] == 4
    finally:
        conn.close()
    db_path = source.db_path
    source.cleanup()
    for suffix in ("", "-wal", "-shm", "-journal"):
        assert not Path(db_path + suffix).exists()


def test_verify_detects_tampering(db, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    path, entry = _create(db, backup_dir, compress=True)

    assert verify_backup(entry, str(backup_dir)) == (True, "ok")
    with open(path, "ab") as handle:
        handle.write(b"tampered")

    ok, message = verify_backup(entry, str(backup_dir))
    assert ok is False
    assert "sha256" in message
    with pytest.raises(BackupError, match="sha256"):
        resolve_backup_source(entry.file, str(backup_dir))


def test_remove_and_prune(db, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    first, first_entry = _create(db, backup_dir)
    second, second_entry = _create(db, backup_dir)
    third, third_entry = _create(db, backup_dir)

    removed = prune_backups(2, str(backup_dir))
    assert [item.file for item in removed] == [first_entry.file]
    assert not Path(first).exists()
    assert Path(second).exists()
    assert Path(third).exists()
    assert {item.file for item in load_manifest(str(backup_dir))} == {
        second_entry.file,
        third_entry.file,
    }

    remove_backup(second_entry, str(backup_dir))
    assert not Path(second).exists()
    assert [item.file for item in load_manifest(str(backup_dir))] == [third_entry.file]


def test_prune_rejects_zero(db, tmp_path) -> None:
    with pytest.raises(BackupError, match="at least 1"):
        prune_backups(0, str(tmp_path / "backups"))


def test_backup_status_aligned_and_out_of_sync(db, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    _, entry = _create(db, backup_dir)
    status = backup_status(db, str(backup_dir))
    assert status["status"] == "aligned"
    assert status["file"] == entry.file

    db.execute(
        "INSERT INTO session (id, title, time_created, time_updated) VALUES (?, ?, ?, ?)",
        ("ses_new", "New", 1, 2),
    )
    db.commit()
    assert backup_status(db, str(backup_dir))["status"] == "out_of_sync"


def test_backup_command_dry_run_and_create(db, tmp_path, capsys) -> None:
    output = tmp_path / "out"
    args = _ns(output=str(output), no_compress=True, dry_run=True)
    assert cmd_backup.run(args, db) == 0
    assert not output.exists()
    out = capsys.readouterr().out
    assert "Dry run" in out or "ничего не записано" in out

    args = _ns(output=str(output), no_compress=True, dry_run=False)
    assert cmd_backup.run(args, db) == 0
    assert len(list(output.glob("*.db"))) == 1


def test_backups_list_view_verify_remove(db, tmp_path, capsys) -> None:
    backup_dir = tmp_path / "backups"
    path, entry = _create(db, backup_dir, compress=True)

    assert cmd_backups.run(_ns(backups_action="list", json=True), db) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["file"] == entry.file

    assert cmd_backups.run(_ns(backups_action="view", file=entry.file, json=True), db) == 0
    viewed = json.loads(capsys.readouterr().out)
    assert viewed["sha256_ok"] is True
    assert viewed["aligned"] is True

    assert cmd_backups.run(_ns(backups_action="verify", file=entry.file), db) == 0
    assert "OK" in capsys.readouterr().out

    assert cmd_backups.run(_ns(backups_action="remove", file=entry.file, yes=True), db) == 0
    assert not Path(path).exists()
    assert load_manifest(str(backup_dir)) == []


def test_backups_view_missing(db, capsys) -> None:
    assert cmd_backups.run(_ns(backups_action="view", file="nope.db", json=True), db) == 1
    assert "nope.db" in capsys.readouterr().out


def test_health_reports_aligned_backup(db, tmp_path, capsys) -> None:
    backup_dir = tmp_path / "backups"
    _create(db, backup_dir)
    path = tmp_path / "live.db"

    with (
        patch("opencode_db.commands.cmd_health.resolve_db_path", return_value=(str(path), False)),
        patch(
            "opencode_db.commands.cmd_health.detect_db_users",
            return_value=SimpleNamespace(available=True, in_use=False, pids=(), method="lsof"),
        ),
    ):
        health_run(_ns(json=True), db)

    data = json.loads(capsys.readouterr().out)
    assert data["backup"]["status"] == "aligned"


def test_health_reports_out_of_sync_backup(db, tmp_path, capsys) -> None:
    backup_dir = tmp_path / "backups"
    _create(db, backup_dir)
    db.execute(
        "INSERT INTO session (id, title, time_created, time_updated) VALUES (?, ?, ?, ?)",
        ("ses_new", "New", 1, 2),
    )
    db.commit()
    path = tmp_path / "live.db"

    with (
        patch("opencode_db.commands.cmd_health.resolve_db_path", return_value=(str(path), False)),
        patch(
            "opencode_db.commands.cmd_health.detect_db_users",
            return_value=SimpleNamespace(available=True, in_use=False, pids=(), method="lsof"),
        ),
    ):
        health_run(_ns(json=True), db)

    data = json.loads(capsys.readouterr().out)
    assert data["backup"]["status"] == "out_of_sync"


def _file_backup(db_file, tmp_path):
    conn = sqlite3.connect(db_file)
    try:
        return create_backup(
            conn,
            db_file,
            backup_dir=str(tmp_path / "backups"),
            compress=True,
        )
    finally:
        conn.close()


def test_cli_from_backup_reads_and_restores_env(db_file, tmp_path, capsys, monkeypatch) -> None:
    from opencode_db.cli import main

    _, entry = _file_backup(db_file, tmp_path)
    monkeypatch.delenv("OPENCODE_DB", raising=False)
    monkeypatch.delenv("OPENCODE_DB_READ_ONLY", raising=False)
    monkeypatch.delenv("OPENCODE_DB_BACKUP_PATH", raising=False)

    code = main(["--from-backup", entry.file, "--lang", "en", "stats", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["sessions"] == 4

    assert os.environ.get("OPENCODE_DB") is None
    assert os.environ.get("OPENCODE_DB_READ_ONLY") is None
    assert os.environ.get("OPENCODE_DB_BACKUP_PATH") is None


def test_cli_from_backup_refuses_writes(db_file, tmp_path, capsys) -> None:
    from opencode_db.cli import main

    _, entry = _file_backup(db_file, tmp_path)
    commands = {
        "delete": ["ses_001", "--force"],
        "prune": ["--older-than", "30d", "--force"],
        "vacuum": ["--force"],
    }
    for command, extra in commands.items():
        code = main(["--from-backup", entry.file, "--lang", "en", command, *extra])
        assert code == 1
        assert "cannot write" in capsys.readouterr().out


def test_corrupt_manifest_is_reported(db, tmp_path, capsys) -> None:
    backup_dir = tmp_path / "corrupt"
    backup_dir.mkdir()
    (backup_dir / "manifest.json").write_text("{not json")
    assert cmd_backups.run(
        _ns(backups_action="list", json=False, dir=str(backup_dir)), db
    ) == 1
    assert "manifest" in capsys.readouterr().out


def test_backups_dir_option(db, tmp_path, capsys) -> None:
    backup_dir = tmp_path / "custom"
    _, entry = _create(db, backup_dir)
    assert cmd_backups.run(
        _ns(backups_action="list", json=True, dir=str(backup_dir)), db
    ) == 0
    assert json.loads(capsys.readouterr().out)[0]["file"] == entry.file


def test_prune_command_rejects_zero(db, tmp_path, capsys) -> None:
    backup_dir = tmp_path / "backups"
    _create(db, backup_dir)
    assert cmd_backups.run(
        _ns(backups_action="prune", keep=0, yes=True, dir=str(backup_dir)), db
    ) == 1
    assert "keep" in capsys.readouterr().out


def test_from_backup_cleans_wal_sidecars(db_file, tmp_path) -> None:
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.commit()
    try:
        _, entry = create_backup(
            conn,
            db_file,
            backup_dir=str(tmp_path / "backups"),
            compress=True,
        )
    finally:
        conn.close()

    source = resolve_backup_source(entry.file, str(tmp_path / "backups"))
    check = sqlite3.connect(source.db_path)
    try:
        assert check.execute("SELECT COUNT(*) FROM session").fetchone()[0] == 4
    finally:
        check.close()
    db_path = source.db_path
    source.cleanup()
    for suffix in ("", "-wal", "-shm", "-journal"):
        assert not Path(db_path + suffix).exists()


def test_backups_list_works_without_live_db(db, tmp_path, capsys) -> None:
    from opencode_db.cli import main

    backup_dir = tmp_path / "backups"
    _, entry = _create(db, backup_dir)
    code = main(["--db-path", str(tmp_path / "missing.db"), "backups", "list", "--dir", str(backup_dir)])
    assert code == 0
    assert entry.file in capsys.readouterr().out
