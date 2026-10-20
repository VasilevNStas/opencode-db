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

from .config import resolve_db_path
from .i18n import _
from .schema import SchemaFamily, detect_schema, schema_issues


class SessionError(Exception):
    """Ошибка, связанная с сессией: не найдена, неоднозначный ID и т.п."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def verify_schema(conn) -> bool:
    """Проверяет, что БД содержит таблицы/колонки, нужные командам."""
    info = detect_schema(conn)

    if info.family is SchemaFamily.UNKNOWN:
        print(_("schema.unknown"))
        print(_("schema.check_upgrade"))
        return False

    ok = True
    for issue in schema_issues(info):
        if issue.kind == "table":
            print(_("schema.table_missing", table=issue.table))
        else:
            print(_("schema.column_missing", table=issue.table, columns=", ".join(issue.columns)))
        ok = False

    for warning in info.warnings:
        print(_("schema.warning", message=warning))

    if not ok:
        print(_("schema.check_upgrade"))

    return ok


def get_db(allow_unknown: bool = False) -> sqlite3.Connection:
    """Открывает соединение с БД opencode.

    allow_unknown нужен диагностическим командам (`schema`, `help`), которые
    должны работать даже при нераспознанной схеме.
    """
    db_path, used_fallback = resolve_db_path()
    if not os.path.isfile(db_path):
        print(_("db.not_found", path=db_path))
        print(_("db.not_found_hint"))
        sys.exit(1)
    if used_fallback:
        print(_("db.next_fallback", path=db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if not verify_schema(conn) and not allow_unknown:
        conn.close()
        sys.exit(1)
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
