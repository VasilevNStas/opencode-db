"""Store implementation for the stable OpenCode v1 schema."""

from __future__ import annotations

import json
from typing import Any

from ..db import get_messages
from .base import BaseStore, parse_json_value


def _search_in_part_data(data: Any, query_lower: str) -> tuple[bool, str]:
    """Search a v1 part JSON payload and return a short snippet."""
    if not data:
        return False, ""
    try:
        parsed = json.loads(data) if isinstance(data, str) else data
    except (json.JSONDecodeError, TypeError):
        return False, ""

    text = parsed.get("text", "")
    if isinstance(text, str) and query_lower in text.lower():
        return True, text[:200]

    state = parsed.get("state", {})
    if isinstance(state, dict):
        t_input = state.get("input", {})
        t_output = state.get("output", "")
        if isinstance(t_input, dict):
            for value in t_input.values():
                if isinstance(value, str) and query_lower in value.lower():
                    return True, f"[tool] {str(value)[:200]}"
        if isinstance(t_output, str) and query_lower in t_output.lower():
            return True, f"[output] {t_output[:200]}"

    return False, ""


class V1Store(BaseStore):
    session_table = "session"
    message_join = "LEFT JOIN message m ON m.session_id = s.id"

    def get_messages(self, session_id: str):
        return get_messages(self.conn, session_id)

    def iter_raw_messages(self, session_id: str):
        rows = self.conn.execute(
            """
            SELECT m.id AS message_id,
                   m.session_id AS message_session_id,
                   m.time_created AS message_time_created,
                   m.data AS message_data,
                   p.id AS part_id,
                   p.session_id AS part_session_id,
                   p.time_created AS part_time_created,
                   p.data AS part_data
            FROM message m
            LEFT JOIN part p ON p.message_id = m.id
            WHERE m.session_id = ?
            ORDER BY m.time_created, m.id, p.id
            """,
            (session_id,),
        )
        current = None
        for row in rows:
            if current is None or current["id"] != row["message_id"]:
                if current is not None:
                    yield current
                current = {
                    "id": row["message_id"],
                    "session_id": row["message_session_id"],
                    "time_created": row["message_time_created"],
                    "data": parse_json_value(row["message_data"]),
                    "parts": [],
                }
            if row["part_id"] is None:
                continue
            current["parts"].append(
                {
                    "id": row["part_id"],
                    "message_id": row["message_id"],
                    "session_id": row["part_session_id"],
                    "time_created": row["part_time_created"],
                    "data": parse_json_value(row["part_data"]),
                }
            )
        if current is not None:
            yield current

    def get_compaction_digests(self, session_id: str, limit: int | None = None):
        rows = self.conn.execute(
            """
            SELECT id, time_created, data
            FROM message
            WHERE session_id = ?
              AND json_extract(data, '$.mode') = 'compaction'
            ORDER BY time_created
            """,
            (session_id,),
        ).fetchall()
        digests = []
        for row in rows:
            data = parse_json_value(row["data"])
            if not isinstance(data, dict):
                data = {}
            texts = []
            for part in self.conn.execute(
                "SELECT data FROM part WHERE message_id = ? ORDER BY id", (row["id"],)
            ):
                part_data = parse_json_value(part["data"])
                if isinstance(part_data, dict) and part_data.get("type") == "text":
                    text = part_data.get("text")
                    if isinstance(text, str) and text.strip():
                        texts.append(text)
            digests.append(
                {
                    "message_id": row["id"],
                    "time_created": row["time_created"],
                    "text": "\n\n".join(texts),
                    "agent": data.get("agent"),
                    "cost": data.get("cost"),
                    "tokens": data.get("tokens"),
                    "summary": bool(data.get("summary")),
                }
            )
        if limit is not None:
            digests = digests[-limit:] if limit > 0 else []
        return digests

    def get_message_count(self, session_id: str | None = None) -> int:
        if session_id:
            return int(
                self.conn.execute(
                    "SELECT COUNT(*) FROM message WHERE session_id = ?", (session_id,)
                ).fetchone()[0]
            )
        return int(self.conn.execute("SELECT COUNT(*) FROM message").fetchone()[0])

    def get_part_count(self, session_id: str | None = None) -> int:
        if session_id:
            return int(
                self.conn.execute(
                    "SELECT COUNT(*) FROM part WHERE session_id = ?", (session_id,)
                ).fetchone()[0]
            )
        return int(self.conn.execute("SELECT COUNT(*) FROM part").fetchone()[0])

    def get_session_todos(self, session_id: str):
        rows = self.conn.execute(
            """
            SELECT content, status, priority, position, time_created
            FROM todo
            WHERE session_id = ?
            ORDER BY position
            """,
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_todos_filtered(
        self,
        session_id: str | None = None,
        status: str | None = None,
        limit: int = 30,
    ):
        conditions = []
        params: list[Any] = []
        if session_id:
            conditions.append("t.session_id = ?")
            params.append(session_id)
        if status:
            conditions.append("t.status = ?")
            params.append(status)
        where = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT t.session_id, t.content, t.status, t.priority,
                   t.position, t.time_created, t.time_updated,
                   s.title AS session_title
            FROM todo t
            JOIN session s ON s.id = t.session_id
            WHERE {where}
            ORDER BY t.time_created DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def list_sessions(
        self,
        *,
        project_id: str | None = None,
        agent: str | None = None,
        model: str | None = None,
        sort: str = "date",
        limit: int = 25,
        offset: int = 0,
    ):
        conditions = []
        params: list[Any] = []
        if project_id:
            conditions.append("s.project_id = ?")
            params.append(project_id)
        if agent:
            conditions.append("s.agent = ?")
            params.append(agent)
        if model:
            conditions.append("s.model LIKE ?")
            params.append(f"%{model}%")
        where = " AND ".join(conditions) if conditions else "1=1"

        sort_map = {
            "date": "COALESCE(MAX(m.time_created), s.time_created) DESC",
            "cost": "s.cost DESC",
            "tokens": "(s.tokens_input + s.tokens_output) DESC",
            "messages": "msg_count DESC",
        }
        order = sort_map.get(sort, sort_map["date"])
        rows = self.conn.execute(
            f"""
            SELECT s.id, s.title, s.model, s.project_id, s.agent, s.directory,
                   s.cost, s.tokens_input, s.tokens_output,
                   MAX(m.time_created) AS last_time,
                   COUNT(DISTINCT m.id) AS msg_count
            FROM session s
            LEFT JOIN message m ON m.session_id = s.id
            WHERE {where}
            GROUP BY s.id
            ORDER BY {order}
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def search(
        self,
        query: str,
        *,
        session_id: str | None = None,
        limit: int = 30,
    ):
        conditions = []
        params: list[Any] = []
        if session_id:
            conditions.append("p.session_id = ?")
            params.append(session_id)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self.conn.execute(
            f"""
            SELECT p.id, p.session_id, p.message_id, p.data,
                   m.time_created,
                   json_extract(m.data, '$.role') AS role
            FROM part p
            JOIN message m ON m.id = p.message_id
            WHERE {where}
              AND p.data IS NOT NULL
            ORDER BY p.time_created DESC
            LIMIT ?
            """,
            (*params, limit * 5),
        ).fetchall()

        results = []
        query_lower = query.lower()
        for row in rows:
            found, snippet = _search_in_part_data(row["data"], query_lower)
            if not found:
                continue
            results.append(
                {
                    "session_id": row["session_id"],
                    "message_id": row["message_id"],
                    "role": row["role"],
                    "time_created": row["time_created"],
                    "snippet": snippet,
                }
            )
            if len(results) >= limit:
                break
        return results

    def stats(self) -> dict[str, Any]:
        session_count = self.conn.execute("SELECT COUNT(*) FROM session").fetchone()[0]
        message_count = self.conn.execute("SELECT COUNT(*) FROM message").fetchone()[0]
        part_count = self.conn.execute("SELECT COUNT(*) FROM part").fetchone()[0]
        project_count = self.conn.execute("SELECT COUNT(*) FROM project").fetchone()[0]
        todo_count = self.conn.execute("SELECT COUNT(*) FROM todo").fetchone()[0]

        totals = self.conn.execute(
            """
            SELECT
                COALESCE(SUM(cost), 0) AS total_cost,
                COALESCE(SUM(tokens_input), 0) AS total_ti,
                COALESCE(SUM(tokens_output), 0) AS total_to,
                COALESCE(SUM(tokens_reasoning), 0) AS total_tr,
                COALESCE(SUM(tokens_cache_read), 0) AS total_cr,
                COALESCE(SUM(tokens_cache_write), 0) AS total_cw
            FROM session
            """
        ).fetchone()
        first_last = self.conn.execute(
            "SELECT MIN(time_created) AS first_ts, MAX(time_created) AS last_ts FROM session"
        ).fetchone()
        top_models = self.conn.execute(
            """
            SELECT model, COUNT(*) AS cnt, SUM(cost) AS cost
            FROM session
            WHERE model IS NOT NULL
            GROUP BY model
            ORDER BY cnt DESC
            LIMIT 5
            """
        ).fetchall()
        agents = self.conn.execute(
            """
            SELECT agent, COUNT(*) AS cnt
            FROM session
            WHERE agent IS NOT NULL
            GROUP BY agent
            ORDER BY cnt DESC
            """
        ).fetchall()

        return {
            "sessions": session_count,
            "messages": message_count,
            "parts": part_count,
            "projects": project_count,
            "todos": todo_count,
            "totals": dict(totals),
            "first_last": dict(first_last),
            "top_models": [dict(row) for row in top_models],
            "agents": [dict(row) for row in agents],
        }
