"""Управляемые backup-снимки и чтение БД из snapshot'а.

Модуль отвечает за manifest, gzip, sha256, проверку целостности и
retention. Автоматические sidecar-копии ``*.bak.*`` из ``delete``/``vacuum``
здесь не участвуют: это отдельный механизм.
"""

from __future__ import annotations

import contextlib
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import get_backup_dir
from .maintenance import backup_to, check_integrity
from .schema import detect_schema
from .store import open_store
from .version import get_version

MANIFEST_VERSION = 1
MANIFEST_NAME = "manifest.json"
CHUNK = 1024 * 1024
SIDECARS = ("", "-wal", "-shm", "-journal")


def remove_sidecars(path: str | Path) -> None:
    for suffix in SIDECARS[1:]:
        with contextlib.suppress(OSError):
            os.remove(f"{path}{suffix}")


def remove_database_files(path: str | Path) -> None:
    remove_sidecars(path)
    with contextlib.suppress(OSError):
        os.remove(path)


class BackupError(RuntimeError):
    """Ошибка backup-операции."""


@dataclass(frozen=True)
class BackupEntry:
    file: str
    created_at: str
    sha256: str
    size: int
    raw_size: int
    compressed: bool
    schema: str
    sessions: int
    messages: int
    parts: int
    max_updated: int | None
    source: str
    tool_version: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BackupEntry:
        return cls(
            file=str(data["file"]),
            created_at=str(data.get("created_at", "")),
            sha256=str(data.get("sha256", "")),
            size=int(data.get("size", 0)),
            raw_size=int(data.get("raw_size", 0)),
            compressed=bool(data.get("compressed", False)),
            schema=str(data.get("schema", "unknown")),
            sessions=int(data.get("sessions", 0)),
            messages=int(data.get("messages", 0)),
            parts=int(data.get("parts", 0)),
            max_updated=(
                int(data["max_updated"]) if data.get("max_updated") is not None else None
            ),
            source=str(data.get("source", "")),
            tool_version=str(data.get("tool_version", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackupSource:
    original_path: Path
    db_path: str
    temporary: bool = False

    def cleanup(self) -> None:
        if self.temporary:
            remove_database_files(self.db_path)


def manifest_path(backup_dir: str | None = None) -> Path:
    return Path(backup_dir or get_backup_dir()).expanduser() / MANIFEST_NAME


def ensure_backup_dir(backup_dir: str | None = None) -> Path:
    path = Path(backup_dir or get_backup_dir()).expanduser()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def load_manifest(backup_dir: str | None = None) -> list[BackupEntry]:
    path = manifest_path(backup_dir)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BackupError(f"invalid manifest {path}: expected an object")
    raw_entries = data.get("backups", [])
    if not isinstance(raw_entries, list):
        raise BackupError(f"invalid manifest {path}: 'backups' must be a list")
    try:
        return [BackupEntry.from_dict(item) for item in raw_entries]
    except (KeyError, TypeError, ValueError) as exc:
        raise BackupError(f"invalid manifest entry in {path}: {exc}") from exc


def save_manifest(entries: list[BackupEntry], backup_dir: str | None = None) -> None:
    path = manifest_path(backup_dir)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = {
        "version": MANIFEST_VERSION,
        "backups": [entry.to_dict() for entry in entries],
    }
    fd, tmp_name = tempfile.mkstemp(prefix=".manifest-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.remove(tmp_name)
        raise


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_gzip(path: str | Path) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def summary_for_connection(
    conn: sqlite3.Connection,
    include_parts: bool = True,
) -> dict[str, Any]:
    info = detect_schema(conn)
    store = open_store(conn, info)
    return {
        "schema": info.family.value,
        "sessions": store.get_session_count(),
        "messages": store.get_message_count(),
        "parts": store.get_part_count() if include_parts else None,
        "max_updated": store.get_max_updated(),
    }


def _unique_target(directory: Path, stem: str, suffix: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    base = f"{stem}-{stamp}"
    target = directory / f"{base}{suffix}"
    counter = 1
    while target.exists():
        target = directory / f"{base}-{counter}{suffix}"
        counter += 1
    return target


def create_backup(
    conn: sqlite3.Connection,
    db_path: str,
    backup_dir: str | None = None,
    compress: bool = True,
) -> tuple[str, BackupEntry]:
    """Создать snapshot, записать manifest и вернуть (path, entry)."""
    directory = ensure_backup_dir(backup_dir)
    stem = Path(db_path).stem or "opencode"
    suffix = ".db.gz" if compress else ".db"
    target = _unique_target(directory, stem, suffix)

    fd, raw_name = tempfile.mkstemp(prefix=".backup-", suffix=".tmp.db", dir=directory)
    os.close(fd)
    with contextlib.suppress(OSError):
        os.remove(raw_name)

    try:
        backup_to(conn, raw_name, verify=True)
        raw_size = os.path.getsize(raw_name)

        summary: dict[str, Any]
        snapshot = sqlite3.connect(raw_name)
        snapshot.row_factory = sqlite3.Row
        try:
            summary = summary_for_connection(snapshot)
        except Exception:
            summary = {
                "schema": "unknown",
                "sessions": 0,
                "messages": 0,
                "parts": 0,
                "max_updated": None,
            }
        finally:
            snapshot.close()
        remove_sidecars(raw_name)

        if compress:
            with open(raw_name, "rb") as source, gzip.open(target, "wb") as destination:
                shutil.copyfileobj(source, destination, CHUNK)
            os.remove(raw_name)
        else:
            os.replace(raw_name, target)
        os.chmod(target, 0o600)

        entry = BackupEntry(
            file=target.name,
            created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            sha256=file_sha256(target),
            size=os.path.getsize(target),
            raw_size=raw_size,
            compressed=compress,
            schema=str(summary["schema"]),
            sessions=int(summary["sessions"]),
            messages=int(summary["messages"]),
            parts=int(summary["parts"]),
            max_updated=summary["max_updated"],
            source=os.path.abspath(db_path),
            tool_version=get_version(),
        )
        entries = load_manifest(directory)
        entries.append(entry)
        save_manifest(entries, directory)
        return str(target), entry
    except Exception:
        remove_database_files(raw_name)
        with contextlib.suppress(OSError):
            os.remove(target)
        raise


def find_entry(ref: str, entries: list[BackupEntry]) -> BackupEntry | None:
    name = Path(ref).name
    for entry in entries:
        if entry.file == ref or entry.file == name:
            return entry
    return None


def entry_path(entry: BackupEntry, backup_dir: str | None = None) -> Path:
    if Path(entry.file).name != entry.file:
        raise BackupError(f"unsafe backup filename: {entry.file}")
    return Path(backup_dir or get_backup_dir()).expanduser() / entry.file


def verify_backup(entry: BackupEntry, backup_dir: str | None = None) -> tuple[bool, str]:
    path = entry_path(entry, backup_dir)
    if not path.is_file():
        return False, f"missing file: {path}"
    try:
        actual = file_sha256(path)
    except OSError as exc:
        return False, str(exc)
    if actual != entry.sha256:
        return False, "sha256 mismatch"
    if not entry.compressed and path.stat().st_size != entry.raw_size:
        return False, "raw size mismatch"

    if entry.compressed:
        fd, tmp_name = tempfile.mkstemp(prefix="opencode-verify-", suffix=".db")
        os.close(fd)
        try:
            with gzip.open(path, "rb") as source, open(tmp_name, "wb") as destination:
                shutil.copyfileobj(source, destination, CHUNK)
            if os.path.getsize(tmp_name) != entry.raw_size:
                return False, "decompressed size mismatch"
            conn = sqlite3.connect(tmp_name)
            try:
                result = check_integrity(conn, full=False)
            finally:
                conn.close()
            return result.ok, result.message
        except (OSError, sqlite3.Error) as exc:
            return False, str(exc)
        finally:
            remove_database_files(tmp_name)

    uri = Path(path).as_uri() + "?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    try:
        result = check_integrity(conn, full=False)
    finally:
        conn.close()
    return result.ok, result.message


def remove_backup(entry: BackupEntry, backup_dir: str | None = None) -> Path:
    path = entry_path(entry, backup_dir)
    if path.is_file():
        path.unlink()
    entries = [item for item in load_manifest(backup_dir) if item.file != entry.file]
    save_manifest(entries, backup_dir)
    return path


def prune_backups(keep: int, backup_dir: str | None = None) -> list[BackupEntry]:
    if keep < 1:
        raise BackupError("keep must be at least 1")
    entries = load_manifest(backup_dir)
    if len(entries) <= keep:
        return []
    ordered = sorted(entries, key=lambda item: item.created_at)
    removed = ordered[:-keep]
    for entry in removed:
        path = entry_path(entry, backup_dir)
        if path.is_file():
            path.unlink()
    remaining = [item for item in entries if item not in removed]
    save_manifest(remaining, backup_dir)
    return removed


def _compare(entry: BackupEntry, live: dict[str, Any]) -> bool:
    return (
        entry.sessions == live.get("sessions")
        and entry.messages == live.get("messages")
        and entry.max_updated == live.get("max_updated")
    )


def backup_status(conn: sqlite3.Connection, backup_dir: str | None = None) -> dict[str, Any]:
    try:
        entries = load_manifest(backup_dir)
    except BackupError as exc:
        return {"status": "error", "error": str(exc)}
    if not entries:
        return {"status": "none"}
    entry = entries[-1]
    data = entry.to_dict()
    try:
        live = summary_for_connection(conn, include_parts=False)
    except Exception as exc:
        data["status"] = "unknown"
        data["error"] = str(exc)
        return data
    data["status"] = "aligned" if _compare(entry, live) else "out_of_sync"
    data["live"] = live
    return data


def resolve_backup_source(
    ref: str,
    backup_dir: str | None = None,
) -> BackupSource:
    """Найти backup, проверить sha256 и при необходимости распаковать gzip."""
    directory = Path(backup_dir or get_backup_dir()).expanduser()
    manifest_error: BackupError | None = None
    try:
        entries = load_manifest(directory)
    except BackupError as exc:
        entries = []
        manifest_error = exc

    entry = find_entry(ref, entries)
    if entry is not None:
        path = entry_path(entry, directory)
    else:
        candidate = Path(ref).expanduser()
        if candidate.is_file():
            path = candidate
        elif not candidate.is_absolute() and (directory / ref).is_file():
            path = directory / ref
        elif manifest_error is not None:
            raise manifest_error
        else:
            raise BackupError(f"backup not found: {ref}")

    if not path.is_file():
        raise BackupError(f"backup not found: {path}")

    if entry is not None:
        try:
            actual = file_sha256(path)
        except OSError as exc:
            raise BackupError(f"cannot read backup {path.name}: {exc}") from exc
        if actual != entry.sha256:
            raise BackupError(f"sha256 mismatch for {path.name}")
        if not entry.compressed and path.stat().st_size != entry.raw_size:
            raise BackupError(f"size mismatch for {path.name}")

    if not is_gzip(path):
        return BackupSource(original_path=path, db_path=str(path))

    fd, tmp_name = tempfile.mkstemp(prefix="opencode-db-from-backup-", suffix=".db")
    os.close(fd)
    try:
        with gzip.open(path, "rb") as source, open(tmp_name, "wb") as destination:
            shutil.copyfileobj(source, destination, CHUNK)
        os.chmod(tmp_name, 0o600)
        if entry is not None and os.path.getsize(tmp_name) != entry.raw_size:
            raise BackupError(f"decompressed size mismatch for {path.name}")
    except Exception:
        remove_database_files(tmp_name)
        raise
    return BackupSource(original_path=path, db_path=tmp_name, temporary=True)
