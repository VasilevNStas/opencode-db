"""Безопасные операции обслуживания SQLite.

Содержит primitives для backup, проверки целостности, WAL checkpoint,
обнаружения процессов, держащих БД, и проверки свободного места.
"""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime


class MaintenanceError(RuntimeError):
    """Ошибка операции обслуживания."""


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    message: str
    full: bool = False


@dataclass(frozen=True)
class DbUsers:
    available: bool
    pids: tuple[int, ...] = ()
    method: str | None = None
    error: str | None = None

    @property
    def in_use(self) -> bool:
        return bool(self.pids)


@dataclass(frozen=True)
class FreeSpace:
    ok: bool
    free: int
    required: int
    database_size: int


@dataclass(frozen=True)
class DatabaseHealth:
    db_path: str
    file_size: int
    wal_size: int
    shm_size: int
    page_size: int
    page_count: int
    freelist_count: int
    freelist_bytes: int
    live_bytes: int
    freelist_pct: float
    auto_vacuum: int
    journal_mode: str


def collect_health(conn: sqlite3.Connection, db_path: str) -> DatabaseHealth:
    """Собирает быстрые метрики SQLite без сканирования таблиц."""
    page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])
    page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
    freelist_count = int(conn.execute("PRAGMA freelist_count").fetchone()[0])
    auto_vacuum = int(conn.execute("PRAGMA auto_vacuum").fetchone()[0])
    journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()

    freelist_bytes = freelist_count * page_size
    live_bytes = max(page_count - freelist_count, 0) * page_size
    freelist_pct = (freelist_count / page_count * 100) if page_count else 0.0

    return DatabaseHealth(
        db_path=db_path,
        file_size=_file_size(db_path),
        wal_size=_file_size(db_path + "-wal"),
        shm_size=_file_size(db_path + "-shm"),
        page_size=page_size,
        page_count=page_count,
        freelist_count=freelist_count,
        freelist_bytes=freelist_bytes,
        live_bytes=live_bytes,
        freelist_pct=freelist_pct,
        auto_vacuum=auto_vacuum,
        journal_mode=journal_mode,
    )


def auto_vacuum_label(mode: int) -> str:
    return {0: "OFF (NONE)", 1: "FULL", 2: "INCREMENTAL"}.get(mode, f"UNKNOWN ({mode})")


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def format_bytes(value: int | None) -> str:
    """Форматирует размер в удобочитаемую строку."""
    if value is None:
        return "?"
    value = int(value)
    if value >= 1024**3:
        return f"{value / 1024**3:.1f} GB"
    if value >= 1024**2:
        return f"{value / 1024**2:.0f} MB"
    if value >= 1024:
        return f"{value / 1024:.0f} KB"
    return f"{value} B"


def check_integrity(conn: sqlite3.Connection, full: bool = False) -> IntegrityResult:
    """Выполняет quick_check или полный integrity_check."""
    pragma = "integrity_check" if full else "quick_check"
    try:
        row = conn.execute(f"PRAGMA {pragma}").fetchone()
    except sqlite3.Error as exc:
        return IntegrityResult(False, str(exc), full)

    if row is None:
        return IntegrityResult(False, "no result", full)

    message = str(row[0])
    return IntegrityResult(message.strip().lower() == "ok", message, full)


def checkpoint_wal(conn: sqlite3.Connection) -> tuple[bool, str]:
    """Сливает WAL в основной файл. Не переключает journal_mode."""
    try:
        mode_row = conn.execute("PRAGMA journal_mode").fetchone()
    except sqlite3.Error as exc:
        return False, str(exc)

    mode = str(mode_row[0]).lower() if mode_row else ""
    if mode != "wal":
        return True, f"journal_mode={mode or 'unknown'}"

    try:
        row = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    except sqlite3.Error as exc:
        return False, str(exc)

    if row is None:
        return False, "no checkpoint result"

    busy = int(row[0])
    if busy:
        return False, "database is busy"
    return True, "ok"


def detect_db_users(db_path: str) -> DbUsers:
    """Проверяет, кто держит файл БД открытым.

    Сначала используется lsof, затем fuser. Собственный PID исключается:
    CLI открывает БД до запуска команды.
    """
    own_pid = os.getpid()

    for tool, command in (
        ("lsof", _lsof_command(db_path)),
        ("fuser", _fuser_command(db_path)),
    ):
        if command is None:
            continue
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return DbUsers(False, method=tool, error=str(exc))

        if tool == "lsof" and result.returncode not in (0, 1):
            continue
        if tool == "fuser" and result.returncode not in (0, 1):
            continue

        pids = tuple(sorted({pid for pid in _parse_pids(result.stdout) if pid != own_pid}))
        return DbUsers(True, pids=pids, method=tool)

    return DbUsers(False, error="neither lsof nor fuser is available")


def _lsof_command(db_path: str) -> list[str] | None:
    executable = shutil.which("lsof")
    if not executable:
        return None
    return [executable, "-t", db_path]


def _fuser_command(db_path: str) -> list[str] | None:
    executable = shutil.which("fuser")
    if not executable:
        return None
    return [executable, db_path]


def _parse_pids(output: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", output)]


def backup_database(
    conn: sqlite3.Connection,
    db_path: str,
    verify: bool = True,
) -> str:
    """Создаёт консистентную копию через SQLite backup API."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = f"{db_path}.bak.{stamp}"
    suffix = 1
    while os.path.exists(target):
        target = f"{db_path}.bak.{stamp}-{suffix}"
        suffix += 1

    dest = sqlite3.connect(target)
    try:
        conn.backup(dest)
    except sqlite3.Error as exc:
        dest.close()
        if os.path.exists(target):
            os.remove(target)
        raise MaintenanceError(f"backup failed: {exc}") from exc
    finally:
        if dest:
            dest.close()

    if verify:
        backup_conn = sqlite3.connect(target)
        try:
            result = check_integrity(backup_conn, full=False)
        finally:
            backup_conn.close()
        if not result.ok:
            os.remove(target)
            raise MaintenanceError(f"backup verification failed: {result.message}")

    return target


def free_space_check(db_path: str, with_backup: bool) -> FreeSpace:
    """Оценивает, хватает ли места для VACUUM и, опционально, backup."""
    database_size = _database_size(db_path)
    multiplier = 2 if with_backup else 1
    required = database_size * multiplier
    directory = os.path.dirname(os.path.abspath(db_path)) or "."
    try:
        free = shutil.disk_usage(directory).free
    except OSError:
        return FreeSpace(False, 0, required, database_size)
    return FreeSpace(free >= required, free, required, database_size)


def _database_size(db_path: str) -> int:
    total = 0
    for suffix in ("", "-wal", "-shm"):
        with contextlib.suppress(OSError):
            total += os.path.getsize(db_path + suffix)
    return total
