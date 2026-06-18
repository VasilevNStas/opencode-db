"""Работа с базой данных opencode.

Предоставляет:
  - get_db() — открыть соединение с БД
  - get_session_info() — метаданные сессии
  - get_messages() — сообщения сессии с разбивкой на части
  - Вспомогательные функции для запросов
"""

import json
import os
import sqlite3
import sys

from config import OPENCODE_DB
from i18n import _


class SessionError(Exception):
    """Ошибка, связанная с сессией: не найдена, неоднозначный ID и т.п."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# Ожидаемая схема БД: таблица → список обязательных колонок
_EXPECTED_SCHEMA = {
    "session": [
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
    ],
    "message": ["id", "session_id", "time_created", "data"],
    "part": ["id", "message_id", "session_id", "time_created", "data"],
    "todo": ["session_id", "content", "status", "priority"],
    "project": ["id", "worktree", "name"],
}


def verify_schema(conn) -> bool:
    """Проверяет, что БД содержит ожидаемые таблицы и колонки."""
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    existing_tables = {r["name"] for r in tables}

    ok = True

    for table, expected_cols in _EXPECTED_SCHEMA.items():
        if table not in existing_tables:
            print(_("schema.table_missing", table=table))
            ok = False
            continue

        columns = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
        existing_cols = {c["name"] for c in columns}

        missing = [c for c in expected_cols if c not in existing_cols]
        if missing:
            print(_("schema.column_missing", table=table, columns=", ".join(missing)))
            ok = False

    if not ok:
        print(_("schema.check_upgrade"))

    return ok


def get_db() -> sqlite3.Connection:
    """Открывает соединение с БД opencode."""
    if not os.path.isfile(OPENCODE_DB):
        print(_("db.not_found", path=OPENCODE_DB))
        print(_("db.not_found_hint"))
        sys.exit(1)
    conn = sqlite3.connect(OPENCODE_DB)
    conn.row_factory = sqlite3.Row
    verify_schema(conn)
    return conn


# ======================================================================
# ЗАПРОСЫ К ТАБЛИЦЕ session
# ======================================================================


def resolve_session_id(db, session_id):
    """Разрешает ID сессии: точное совпадение или префикс."""
    if not session_id:
        return None

    row = db.execute("SELECT id FROM session WHERE id = ?", (session_id,)).fetchone()
    if row:
        return row["id"]

    rows = db.execute(
        "SELECT id FROM session WHERE id LIKE ? COLLATE NOCASE", (f"{session_id}%",)
    ).fetchall()

    if not rows:
        raise SessionError(_("session.not_found", session_id=session_id))

    if len(rows) > 1:
        msg = [_("session.multiple_match", session_id=session_id)]
        for r in rows:
            msg.append(f"    {r['id']}")
        msg.append(_("session.specify_id"))
        raise SessionError("\n".join(msg))

    return rows[0]["id"]


def get_session_info(db, session_id):
    """Достаёт метаданные сессии."""
    full_id = resolve_session_id(db, session_id)

    row = db.execute(
        """
        SELECT s.id, s.title, s.model, s.agent,
               s.time_created, s.time_updated,
               s.cost, s.tokens_input, s.tokens_output, s.tokens_reasoning,
               s.tokens_cache_read, s.tokens_cache_write,
               s.project_id, s.parent_id, s.directory, s.version,
               s.summary_additions, s.summary_deletions, s.summary_files
        FROM session s
        WHERE s.id = ?
    """,
        (full_id,),
    ).fetchone()

    if not row:
        raise SessionError(_("session.not_found", session_id=session_id))

    return row


def get_session_title(row):
    """Извлекает название сессии, подставляя 'Безымянная' если None."""
    return row["title"] or _("info.unnamed")


def parse_model(row):
    """Парсит JSON модели из строки БД."""
    model_json = row["model"]
    if not model_json:
        return "—"
    try:
        return json.loads(model_json).get("id", "—")
    except (json.JSONDecodeError, TypeError):
        return str(model_json)[:40]


# ======================================================================
# ЗАПРОСЫ К ТАБЛИЦАМ message + part
# ======================================================================


def get_messages(db, session_id):
    """Достаёт все сообщения сессии с разбивкой на части.

    Returns:
      list[dict]: {"id", "role", "agent", "time", "parts": [...]}
    """
    rows = db.execute(
        """
        SELECT m.id,
               json_extract(m.data, '$.role') as role,
               json_extract(m.data, '$.agent') as agent,
               m.time_created,
               p.data as part_data
        FROM message m
        LEFT JOIN part p ON p.message_id = m.id
        WHERE m.session_id = ?
        ORDER BY m.time_created, p.id
    """,
        (session_id,),
    ).fetchall()

    messages = []
    current = None

    for row in rows:
        msg_id = row["id"]
        part_data = row["part_data"]

        if not part_data:
            continue

        try:
            data = json.loads(part_data)
        except json.JSONDecodeError:
            continue

        part_type = data.get("type", "")

        if current and current["id"] == msg_id:
            parts = current["parts"]
        else:
            if current:
                messages.append(current)
            current = {
                "id": msg_id,
                "role": row["role"],
                "agent": row["agent"],
                "time": row["time_created"],
                "parts": [],
            }
            parts = current["parts"]

        if part_type == "text":
            text = data.get("text", "")
            if text.strip():
                parts.append({"type": "text", "text": text})

        elif part_type in ("reasoning", "thought"):
            text = data.get("text", "")
            if text.strip():
                parts.append({"type": "reasoning", "text": text})

        elif part_type in ("tool", "result"):
            state = data.get("state", {})
            parts.append(
                {
                    "type": "tool",
                    "tool": data.get("tool", state.get("tool", "")),
                    "input": state.get("input", {}),
                    "output": state.get("output", ""),
                    "status": state.get("status", ""),
                }
            )

        elif part_type == "sound":
            parts.append({"type": "sound"})

    if current:
        messages.append(current)

    return messages


# ======================================================================
# ПОДСЧЁТЫ
# ======================================================================


def get_session_count(db, project_id=None):
    """Количество сессий. Опционально — по проекту."""
    if project_id:
        return db.execute(
            "SELECT COUNT(*) FROM session WHERE project_id = ?", (project_id,)
        ).fetchone()[0]
    return db.execute("SELECT COUNT(*) FROM session").fetchone()[0]


def get_message_count(db, session_id=None):
    """Количество сообщений. Опционально — по сессии."""
    if session_id:
        return db.execute(
            "SELECT COUNT(*) FROM message WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
    return db.execute("SELECT COUNT(*) FROM message").fetchone()[0]


def get_part_count(db, session_id=None):
    """Количество частей сообщений. Опционально — по сессии."""
    if session_id:
        return db.execute(
            "SELECT COUNT(*) FROM part WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
    return db.execute("SELECT COUNT(*) FROM part").fetchone()[0]


def get_project_count(db):
    """Количество проектов в БД."""
    return db.execute("SELECT COUNT(*) FROM project").fetchone()[0]


# ======================================================================
# СВЯЗАННЫЕ ДАННЫЕ
# ======================================================================


def get_children_sessions(db, session_id):
    """Дочерние сессии (ответвившиеся от данной)."""
    return db.execute(
        """
        SELECT id, title, time_created
        FROM session
        WHERE parent_id = ?
        ORDER BY time_created
    """,
        (session_id,),
    ).fetchall()


def get_parent_session(db, session_id):
    """Родительская сессия (от которой ответвилась данная)."""
    row = db.execute(
        """
        SELECT s2.id, s2.title, s2.time_created
        FROM session s1
        JOIN session s2 ON s2.id = s1.parent_id
        WHERE s1.id = ?
    """,
        (session_id,),
    ).fetchone()
    return row


def get_session_todos(db, session_id):
    """Todo-записи для сессии."""
    return db.execute(
        """
        SELECT content, status, priority, position, time_created
        FROM todo
        WHERE session_id = ?
        ORDER BY position
    """,
        (session_id,),
    ).fetchall()


def get_project_name(db, project_id):
    """Возвращает название проекта по ID."""
    row = db.execute("SELECT name, worktree FROM project WHERE id = ?", (project_id,)).fetchone()
    if row:
        return row["name"] or os.path.basename(row["worktree"]) or project_id[:12]
    return project_id[:12]


def get_latest_session(db):
    """Находит ID самой свежей сессии (по последнему сообщению или времени создания)."""
    row = db.execute("""
        SELECT s.id FROM session s
        LEFT JOIN message m ON m.session_id = s.id
        GROUP BY s.id
        ORDER BY COALESCE(MAX(m.time_created), s.time_created) DESC
        LIMIT 1
    """).fetchone()

    if not row:
        raise SessionError(_("session.no_sessions"))

    return row["id"]


def get_recent_sessions(db, limit=15, project_id=None):
    """Возвращает список последних сессий для интерактивного выбора."""
    if project_id:
        return db.execute(
            """
            SELECT s.id, s.title, s.model, s.time_created, s.cost,
                   COUNT(DISTINCT m.id) as msg_count
            FROM session s
            LEFT JOIN message m ON m.session_id = s.id
            WHERE s.project_id = ?
            GROUP BY s.id
            ORDER BY COALESCE(MAX(m.time_created), s.time_created) DESC
            LIMIT ?
        """,
            (project_id, limit),
        ).fetchall()
    return db.execute(
        """
        SELECT s.id, s.title, s.model, s.time_created, s.cost,
               COUNT(DISTINCT m.id) as msg_count
        FROM session s
        LEFT JOIN message m ON m.session_id = s.id
        GROUP BY s.id
        ORDER BY COALESCE(MAX(m.time_created), s.time_created) DESC
        LIMIT ?
    """,
        (limit,),
    ).fetchall()
