"""Shared store behavior for the v1 and v2 OpenCode schemas."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from ..db import SessionError, get_session_title, parse_model
from ..i18n import _
from ..schema import SchemaInfo


def parse_json_value(value: Any) -> Any:
    """Parse a JSON column, preserving the raw value when parsing fails."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


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

    def get_session_row(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            f"SELECT * FROM {self.session_table} WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    def iter_raw_messages(self, session_id: str):
        """Yield raw messages with original JSON payloads."""
        raise NotImplementedError

    def get_raw_messages(self, session_id: str) -> list[dict[str, Any]]:
        return list(self.iter_raw_messages(session_id))

    def get_compaction_digests(self, session_id: str, limit: int | None = None):
        """Return compaction summaries for a session."""
        raise NotImplementedError

    def get_max_updated(self) -> int | None:
        row = self.conn.execute(
            f"SELECT MAX(time_updated) FROM {self.session_table}"
        ).fetchone()
        return int(row[0]) if row and row[0] is not None else None

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

    def get_directories(self, check_exists: bool = True) -> list[dict[str, Any]]:
        """Aggregate directories from sessions, projects and project mappings."""
        entries: dict[str, dict[str, Any]] = {}

        def ensure(path: str, project_id: str | None, source: str) -> dict[str, Any]:
            normalized = os.path.normpath(path)
            entry = entries.setdefault(
                normalized,
                {
                    "path": normalized,
                    "sessions": 0,
                    "first_ts": None,
                    "last_ts": None,
                    "tokens_input": 0,
                    "tokens_output": 0,
                    "tokens_reasoning": 0,
                    "tokens_cache_read": 0,
                    "tokens_cache_write": 0,
                    "cost": 0.0,
                    "project_ids": set(),
                    "session_projects": {},
                    "project_sources": set(),
                    "sources": set(),
                },
            )
            entry["sources"].add(source)
            if project_id:
                entry["project_ids"].add(project_id)
                if source == "sessions":
                    entry["session_projects"][project_id] = (
                        entry["session_projects"].get(project_id, 0)
                    )
                else:
                    entry["project_sources"].add(project_id)
            return entry

        session_rows = self.conn.execute(
            f"""
            SELECT directory, project_id,
                   COUNT(*) AS sessions,
                   MIN(time_created) AS first_ts,
                   MAX(time_created) AS last_ts,
                   COALESCE(SUM(tokens_input), 0) AS tokens_input,
                   COALESCE(SUM(tokens_output), 0) AS tokens_output,
                   COALESCE(SUM(tokens_reasoning), 0) AS tokens_reasoning,
                   COALESCE(SUM(tokens_cache_read), 0) AS tokens_cache_read,
                   COALESCE(SUM(tokens_cache_write), 0) AS tokens_cache_write,
                   COALESCE(SUM(cost), 0) AS cost
            FROM {self.session_table}
            WHERE directory IS NOT NULL AND directory != ''
            GROUP BY directory, project_id
            """
        ).fetchall()
        for row in session_rows:
            entry = ensure(row["directory"], row["project_id"], "sessions")
            entry["sessions"] += int(row["sessions"])
            entry["session_projects"][row["project_id"]] = int(row["sessions"])
            for key in ("tokens_input", "tokens_output", "tokens_reasoning",
                        "tokens_cache_read", "tokens_cache_write"):
                entry[key] += int(row[key] or 0)
            entry["cost"] += float(row["cost"] or 0)
            first_ts = row["first_ts"]
            last_ts = row["last_ts"]
            if first_ts is not None:
                entry["first_ts"] = first_ts if entry["first_ts"] is None else min(entry["first_ts"], first_ts)
            if last_ts is not None:
                entry["last_ts"] = last_ts if entry["last_ts"] is None else max(entry["last_ts"], last_ts)

        project_rows = self.conn.execute(
            "SELECT id, name, worktree FROM project WHERE worktree IS NOT NULL AND worktree != ''"
        ).fetchall()
        project_meta = {row["id"]: dict(row) for row in project_rows}
        for row in project_rows:
            if row["id"] == "global" and os.path.normpath(row["worktree"]) == "/":
                continue
            ensure(row["worktree"], row["id"], "project")

        if "project_directory" in self.schema.tables:
            directory_rows = self.conn.execute(
                """
                SELECT project_id, directory
                FROM project_directory
                WHERE directory IS NOT NULL AND directory != ''
                """
            ).fetchall()
            for row in directory_rows:
                ensure(row["directory"], row["project_id"], "project_directory")

        for entry in entries.values():
            candidates = [
                project_id
                for project_id in entry["project_ids"]
                if entry["session_projects"].get(project_id, 0) > 0
            ]
            if not candidates:
                candidates = list(entry["project_ids"])
            non_global = [project_id for project_id in candidates if project_id != "global"]
            pool = non_global or candidates
            chosen = max(
                pool,
                key=lambda project_id: entry["session_projects"].get(project_id, 0),
            ) if pool else None

            entry["project_id"] = chosen
            entry["project_ids"] = sorted(entry["project_ids"])
            entry["is_global"] = chosen == "global"
            entry["sources"] = sorted(entry["sources"])
            if chosen == "global":
                entry["project_label"] = _("directories.global")
            elif chosen:
                meta = project_meta.get(chosen, {})
                label = meta.get("name")
                if not label:
                    worktree = meta.get("worktree") or ""
                    label = os.path.basename(str(worktree).rstrip("/")) or chosen[:12]
                entry["project_label"] = str(label)
            else:
                entry["project_label"] = "—"

            entry["exists"] = os.path.isdir(entry["path"]) if check_exists else None

        return list(entries.values())

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
