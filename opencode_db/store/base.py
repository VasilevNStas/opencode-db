"""Shared store behavior for the v1 and v2 OpenCode schemas."""

from __future__ import annotations

import sqlite3
from typing import Any

from ..db import SessionError, get_session_title, parse_model
from ..i18n import _
from ..schema import SchemaInfo


class BaseStore:
    """Schema-independent queries over a session table."""

    session_table = "session"
    message_join = "LEFT JOIN message m ON m.session_id = s.id"

    def __init__(self, conn: sqlite3.Connection, schema: SchemaInfo):
        self.conn = conn
        self.schema = schema

    # ------------------------------------------------------------------
    # Generic session helpers
    # ------------------------------------------------------------------

    def resolve_session_id(self, session_id: str) -> str:
        if not session_id:
            raise SessionError(_("session.not_found", session_id=session_id))

        row = self.conn.execute(
            f"SELECT id FROM {self.session_table} WHERE id = ?", (session_id,)
        ).fetchone()
        if row:
            return str(row[0])

        rows = self.conn.execute(
            f"SELECT id FROM {self.session_table} WHERE id LIKE ? COLLATE NOCASE",
            (f"{session_id}%",),
        ).fetchall()

        if not rows:
            raise SessionError(_("session.not_found", session_id=session_id))

        if len(rows) > 1:
            msg = [_("session.multiple_match", session_id=session_id)]
            msg.extend(f"    {row[0]}" for row in rows)
            msg.append(_("session.specify_id"))
            raise SessionError("\n".join(msg))

        return str(rows[0][0])

    def get_session_info(self, session_id: str) -> dict[str, Any]:
        full_id = self.resolve_session_id(session_id)
        row = self.conn.execute(
            f"""
            SELECT s.id, s.title, s.model, s.agent,
                   s.time_created, s.time_updated,
                   s.cost, s.tokens_input, s.tokens_output, s.tokens_reasoning,
                   s.tokens_cache_read, s.tokens_cache_write,
                   s.project_id, s.parent_id, s.directory, s.version,
                   s.summary_additions, s.summary_deletions, s.summary_files
            FROM {self.session_table} s
            WHERE s.id = ?
            """,
            (full_id,),
        ).fetchone()
        if not row:
            raise SessionError(_("session.not_found", session_id=session_id))
        return dict(row)

    def get_session_title(self, row) -> str:
        return get_session_title(row)

    def parse_model(self, row) -> str:
        return parse_model(row)

    def get_children_sessions(self, session_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"""
            SELECT id, title, time_created
            FROM {self.session_table}
            WHERE parent_id = ?
            ORDER BY time_created
            """,
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_parent_session(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            f"""
            SELECT s2.id, s2.title, s2.time_created
            FROM {self.session_table} s1
            JOIN {self.session_table} s2 ON s2.id = s1.parent_id
            WHERE s1.id = ?
            """,
            (session_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_project_name(self, project_id: str) -> str:
        row = self.conn.execute(
            "SELECT name, worktree FROM project WHERE id = ?", (project_id,)
        ).fetchone()
        if row:
            name = row["name"]
            if name:
                return str(name)
            worktree = row["worktree"]
            if worktree:
                return str(worktree).rstrip("/").rsplit("/", 1)[-1] or project_id[:12]
        return project_id[:12]

    def get_session_count(self, project_id: str | None = None) -> int:
        if project_id:
            return int(
                self.conn.execute(
                    f"SELECT COUNT(*) FROM {self.session_table} WHERE project_id = ?",
                    (project_id,),
                ).fetchone()[0]
            )
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {self.session_table}").fetchone()[0])

    def get_project_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM project").fetchone()[0])

    def get_latest_session(self) -> str:
        row = self.conn.execute(
            f"""
            SELECT s.id
            FROM {self.session_table} s
            {self.message_join}
            GROUP BY s.id
            ORDER BY COALESCE(MAX(m.time_created), s.time_created) DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            raise SessionError(_("session.no_sessions"))
        return str(row[0])

    def get_recent_sessions(self, limit: int = 15, project_id: str | None = None):
        where = "WHERE s.project_id = ?" if project_id else ""
        params: list[Any] = [project_id] if project_id else []
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT s.id, s.title, s.model, s.time_created, s.cost,
                   COUNT(DISTINCT m.id) AS msg_count
            FROM {self.session_table} s
            {self.message_join}
            {where}
            GROUP BY s.id
            ORDER BY COALESCE(MAX(m.time_created), s.time_created) DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_tree_rows(self, parent_id: str | None, project_id: str | None = None):
        conditions = []
        params: list[Any] = []
        if parent_id is None:
            conditions.append("parent_id IS NULL")
        else:
            conditions.append("parent_id = ?")
            params.append(parent_id)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        where = " AND ".join(conditions)
        rows = self.conn.execute(
            f"""
            SELECT id, title, time_created, project_id
            FROM {self.session_table}
            WHERE {where}
            ORDER BY time_created
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_session_brief(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            f"SELECT id, title, time_created, project_id FROM {self.session_table} WHERE id = ?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Generic reporting queries
    # ------------------------------------------------------------------

    def get_projects(self):
        rows = self.conn.execute(
            f"""
            SELECT p.id, p.name, p.worktree, p.time_created, p.time_updated,
                   COUNT(DISTINCT s.id) AS session_count,
                   COALESCE(SUM(s.cost), 0) AS total_cost,
                   COALESCE(SUM(s.tokens_input), 0) AS total_ti,
                   COALESCE(SUM(s.tokens_output), 0) AS total_to,
                   COALESCE(SUM(s.tokens_reasoning), 0) AS total_tr
            FROM project p
            LEFT JOIN {self.session_table} s ON s.project_id = p.id
            GROUP BY p.id
            ORDER BY p.time_updated DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def get_cost_total(self, project_id: str | None = None) -> dict[str, Any]:
        where = "WHERE s.project_id = ?" if project_id else ""
        params: list[Any] = [project_id] if project_id else []
        row = self.conn.execute(
            f"""
            SELECT COUNT(*) AS cnt,
                   SUM(tokens_input) AS ti, SUM(tokens_output) AS tok_out,
                   SUM(tokens_reasoning) AS tr, SUM(cost) AS c
            FROM {self.session_table} s
            {where}
            """,
            params,
        ).fetchone()
        return dict(row)

    def get_cost_list(self, project_id: str | None = None, limit: int = 30):
        where = "WHERE s.project_id = ?" if project_id else ""
        params: list[Any] = [project_id] if project_id else []
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT s.id, s.title, s.model,
                   s.tokens_input, s.tokens_output, s.tokens_reasoning,
                   s.cost
            FROM {self.session_table} s
            {where}
            ORDER BY (s.tokens_input + s.tokens_output) DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Schema-specific API (implemented by V1Store/V2Store)
    # ------------------------------------------------------------------

    def get_messages(self, session_id: str):
        raise NotImplementedError

    def get_message_count(self, session_id: str | None = None) -> int:
        raise NotImplementedError

    def get_part_count(self, session_id: str | None = None) -> int:
        raise NotImplementedError

    def get_session_todos(self, session_id: str):
        raise NotImplementedError

    def get_todos_filtered(
        self,
        session_id: str | None = None,
        status: str | None = None,
        limit: int = 30,
    ):
        raise NotImplementedError

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
        raise NotImplementedError

    def search(self, query: str, *, session_id: str | None = None, limit: int = 30):
        raise NotImplementedError

    def stats(self) -> dict[str, Any]:
        raise NotImplementedError
