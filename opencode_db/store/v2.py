"""Store implementation for the preview OpenCode v2 schema."""

from __future__ import annotations

import json
from typing import Any

from .base import BaseStore

CONVERSATION_TYPES = ("user", "assistant")
SEARCHABLE_TYPES = ("user", "assistant", "synthetic", "system", "skill", "shell", "compaction")


def _load_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _message_time(data: dict[str, Any], fallback: int | None) -> int | None:
    time = data.get("time")
    if isinstance(time, dict):
        created = time.get("created")
        if isinstance(created, int):
            return created
    return fallback


def _tool_output(state: dict[str, Any]) -> str:
    if state.get("status") == "error":
        error = state.get("error")
        if isinstance(error, dict):
            return str(error.get("message", ""))
        return str(error or "")
    output = state.get("output")
    if isinstance(output, str):
        return output
    content = state.get("content")
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                chunks.append(item["text"])
        return "\n".join(chunks)
    return ""


def _parts_for_message(data: dict[str, Any]) -> list[dict[str, Any]]:
    message_type = data.get("type")
    parts: list[dict[str, Any]] = []

    if message_type == "user":
        text = data.get("text")
        if isinstance(text, str) and text.strip():
            parts.append({"type": "text", "text": text})
        files = data.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("filename") or "file"
                    parts.append({"type": "text", "text": f"[file] {name}"})
        return parts

    if message_type == "assistant":
        content = data.get("content")
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type == "text":
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append({"type": "text", "text": text})
                elif item_type == "reasoning":
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append({"type": "reasoning", "text": text})
                elif item_type == "tool":
                    state_value = item.get("state")
                    state: dict[str, Any] = state_value if isinstance(state_value, dict) else {}
                    tool_input = state.get("input")
                    if not isinstance(tool_input, dict):
                        tool_input = {}
                    parts.append(
                        {
                            "type": "tool",
                            "tool": item.get("name", ""),
                            "input": tool_input,
                            "output": _tool_output(state),
                            "status": state.get("status", ""),
                        }
                    )
        return parts

    if message_type in ("synthetic", "system", "skill"):
        text = data.get("text")
        if isinstance(text, str) and text.strip():
            parts.append({"type": "text", "text": text})
        return parts

    if message_type == "shell":
        command = data.get("command", "")
        output = data.get("output", "")
        parts.append(
            {
                "type": "tool",
                "tool": "shell",
                "input": {"command": command} if command else {},
                "output": str(output or ""),
                "status": data.get("status", ""),
            }
        )
        return parts

    if message_type == "compaction":
        text = data.get("summary")
        if isinstance(text, str) and text.strip():
            parts.append({"type": "text", "text": text})
        return parts

    return parts


def _search_in_message(data: dict[str, Any], query_lower: str) -> tuple[bool, str]:
    for part in _parts_for_message(data):
        text = part.get("text")
        if isinstance(text, str) and query_lower in text.lower():
            return True, text[:200]
        tool_input = part.get("input")
        if isinstance(tool_input, dict):
            for value in tool_input.values():
                if isinstance(value, str) and query_lower in value.lower():
                    return True, f"[tool] {value[:200]}"
        output = part.get("output")
        if isinstance(output, str) and query_lower in output.lower():
            return True, f"[output] {output[:200]}"
    return False, ""


def _parse_todos(data: dict[str, Any]) -> list[dict[str, Any]]:
    content = data.get("content")
    if not isinstance(content, list):
        return []
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "tool":
            continue
        if item.get("name") != "todowrite":
            continue
        state = item.get("state")
        if not isinstance(state, dict) or state.get("status") != "completed":
            continue
        tool_input = state.get("input")
        todos = tool_input.get("todos") if isinstance(tool_input, dict) else None
        if not isinstance(todos, list):
            continue
        result = []
        for index, todo in enumerate(todos):
            if not isinstance(todo, dict) or not isinstance(todo.get("content"), str):
                continue
            result.append(
                {
                    "content": todo["content"],
                    "status": todo.get("status", "pending"),
                    "priority": None,
                    "position": index,
                    "time_created": None,
                }
            )
        return result
    return []


class V2Store(BaseStore):
    session_table = "session_v2"
    message_join = (
        "LEFT JOIN session_message m ON m.session_id = s.id AND m.type IN ('user', 'assistant')"
    )

    def _rows(self, session_id: str | None = None):
        if session_id:
            return self.conn.execute(
                "SELECT * FROM session_message WHERE session_id = ? ORDER BY seq",
                (session_id,),
            ).fetchall()
        return self.conn.execute("SELECT * FROM session_message ORDER BY seq").fetchall()

    def get_messages(self, session_id: str):
        session = self.conn.execute(
            "SELECT agent FROM session_v2 WHERE id = ?", (session_id,)
        ).fetchone()
        session_agent = session["agent"] if session else None
        messages = []
        for row in self._rows(session_id):
            data = _load_json(row["data"])
            parts = _parts_for_message(data)
            if not parts:
                continue
            message_type = data.get("type")
            role = "user" if message_type == "user" else "assistant"
            agent = data.get("agent") if role == "assistant" else None
            messages.append(
                {
                    "id": row["id"],
                    "role": role,
                    "agent": agent or (session_agent if role == "assistant" else None),
                    "time": _message_time(data, row["time_created"]),
                    "parts": parts,
                }
            )
        return messages

    def _count_parts(self, session_id: str | None = None) -> int:
        return sum(
            len(_parts_for_message(_load_json(row["data"]))) for row in self._rows(session_id)
        )

    def get_message_count(self, session_id: str | None = None) -> int:
        where = (
            "WHERE session_id = ? AND type IN ('user', 'assistant')"
            if session_id
            else ("WHERE type IN ('user', 'assistant')")
        )
        params = (session_id,) if session_id else ()
        return int(
            self.conn.execute(f"SELECT COUNT(*) FROM session_message {where}", params).fetchone()[0]
        )

    def get_part_count(self, session_id: str | None = None) -> int:
        return self._count_parts(session_id)

    def _todo_rows(self, session_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, session_id, time_created, data
            FROM session_message
            WHERE session_id = ? AND type = 'assistant' AND data LIKE '%todowrite%'
            ORDER BY seq DESC
            """,
            (session_id,),
        ).fetchall()
        for row in rows:
            data = _load_json(row["data"])
            todos = _parse_todos(data)
            if not todos:
                continue
            for todo in todos:
                todo["time_created"] = _message_time(data, row["time_created"])
            return todos
        return []

    def get_session_todos(self, session_id: str):
        return self._todo_rows(session_id)

    def get_todos_filtered(
        self,
        session_id: str | None = None,
        status: str | None = None,
        limit: int = 30,
    ):
        if session_id:
            sessions = [session_id]
        else:
            rows = self.conn.execute(
                """
                SELECT DISTINCT session_id
                FROM session_message
                WHERE type = 'assistant' AND data LIKE '%todowrite%'
                """
            ).fetchall()
            sessions = [row[0] for row in rows]

        titles = {}
        if sessions:
            placeholders = ",".join("?" for _ in sessions)
            for row in self.conn.execute(
                f"SELECT id, title FROM session_v2 WHERE id IN ({placeholders})", sessions
            ):
                titles[row["id"]] = row["title"]

        results = []
        for sid in sessions:
            for todo in self._todo_rows(sid):
                if status and todo["status"] != status:
                    continue
                item = dict(todo)
                item["session_id"] = sid
                item["session_title"] = titles.get(sid)
                item["time_updated"] = todo["time_created"]
                results.append(item)
        results.sort(key=lambda item: item.get("time_created") or 0, reverse=True)
        return results[:limit]

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
            FROM session_v2 s
            LEFT JOIN session_message m ON m.session_id = s.id
                AND m.type IN ('user', 'assistant')
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
        conditions = [f"type IN ({','.join('?' for _ in SEARCHABLE_TYPES)})"]
        params: list[Any] = list(SEARCHABLE_TYPES)
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        where = " AND ".join(conditions)
        rows = self.conn.execute(
            f"""
            SELECT id, session_id, type, time_created, data
            FROM session_message
            WHERE {where}
            ORDER BY time_created DESC
            LIMIT ?
            """,
            (*params, limit * 5),
        ).fetchall()

        query_lower = query.lower()
        results = []
        for row in rows:
            data = _load_json(row["data"])
            found, snippet = _search_in_message(data, query_lower)
            if not found:
                continue
            results.append(
                {
                    "session_id": row["session_id"],
                    "message_id": row["id"],
                    "role": "user" if row["type"] == "user" else "assistant",
                    "time_created": _message_time(data, row["time_created"]),
                    "snippet": snippet,
                }
            )
            if len(results) >= limit:
                break
        return results

    def _all_todos(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT DISTINCT session_id
            FROM session_message
            WHERE type = 'assistant' AND data LIKE '%todowrite%'
            """
        ).fetchall()
        result = []
        for row in rows:
            result.extend(self._todo_rows(row[0]))
        return result

    def stats(self) -> dict[str, Any]:
        session_count = self.conn.execute("SELECT COUNT(*) FROM session_v2").fetchone()[0]
        message_count = self.conn.execute(
            "SELECT COUNT(*) FROM session_message WHERE type IN ('user', 'assistant')"
        ).fetchone()[0]
        part_count = self._count_parts()
        project_count = self.conn.execute("SELECT COUNT(*) FROM project").fetchone()[0]
        todo_count = len(self._all_todos())

        totals = self.conn.execute(
            """
            SELECT
                COALESCE(SUM(cost), 0) AS total_cost,
                COALESCE(SUM(tokens_input), 0) AS total_ti,
                COALESCE(SUM(tokens_output), 0) AS total_to,
                COALESCE(SUM(tokens_reasoning), 0) AS total_tr,
                COALESCE(SUM(tokens_cache_read), 0) AS total_cr,
                COALESCE(SUM(tokens_cache_write), 0) AS total_cw
            FROM session_v2
            """
        ).fetchone()
        first_last = self.conn.execute(
            "SELECT MIN(time_created) AS first_ts, MAX(time_created) AS last_ts FROM session_v2"
        ).fetchone()
        top_models = self.conn.execute(
            """
            SELECT model, COUNT(*) AS cnt, SUM(cost) AS cost
            FROM session_v2
            WHERE model IS NOT NULL
            GROUP BY model
            ORDER BY cnt DESC
            LIMIT 5
            """
        ).fetchall()
        agents = self.conn.execute(
            """
            SELECT agent, COUNT(*) AS cnt
            FROM session_v2
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
