"""Команда delete: удаление сессии или массовая очистка."""

import argparse
import os
import sqlite3
from datetime import datetime

from ..config import resolve_db_path
from ..db import (
    SessionError,
    get_message_count,
    get_part_count,
    get_recent_sessions,
    get_session_info,
    get_session_title,
    parse_model,
)
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, confirm, format_cost, format_ts, parse_date, parse_time_spec

_DELETE_EXAMPLES = [
    ("<session_id>", "help.delete.e0"),
    ("<session_id> --dry-run", "help.delete.e1"),
    ("<session_id> --force", "help.delete.e2"),
    ("--older-than 90d", "help.delete.e3"),
    ("--keep-last 30", "help.delete.e4"),
    ("--before 2026-05-20", "help.delete.e5"),
    ("--interactive", "help.delete.e6"),
    ("--missing-directories", "help.delete.e7"),
    ("--missing-directories --execute", "help.delete.e8"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "delete",
        help=_("help.cmd.delete"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("delete", _DELETE_EXAMPLES),
    )
    p.add_argument("session_id", nargs="?", help="Session ID (optional with --interactive)")
    p.add_argument("--older-than", type=str, help="Delete sessions older than (30d, 6m, 1y)")
    p.add_argument("--before", type=str, help="Delete sessions before date (YYYY-MM-DD)")
    p.add_argument("--after", type=str, help="Delete sessions after date (YYYY-MM-DD)")
    p.add_argument("--keep-last", type=int, help="Keep N most recent sessions")
    p.add_argument("--project", type=str, help="Limit to project")
    p.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    p.add_argument("--interactive", action="store_true", help="Choose sessions from a list")
    p.add_argument(
        "--missing-directories",
        action="store_true",
        help="Sessions whose directory no longer exists (preview by default)",
    )
    p.add_argument("--execute", action="store_true", help="Execute missing-directory cleanup")
    p.add_argument("--backup", action="store_true", help="Create a DB backup before deletion")
    p.add_argument("--no-backup", action="store_true", help="Skip the DB backup")


def _delete_single(db, session_id, dry_run, force) -> int:
    """Удаление одной сессии по ID."""
    try:
        info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    sid = info["id"]
    title = get_session_title(info)
    model = parse_model(info)
    msg_count = get_message_count(db, sid)
    part_count = get_part_count(db, sid)
    created = format_ts(info["time_created"])

    print(f"\n{'=' * 50}")
    print(f"  {_('delete.header')}")
    print(f"{'=' * 50}")
    print(f"  {_('delete.id')}:         {sid}")
    print(f"  {_('delete.title')}:   {title}")
    print(f"  {_('delete.model')}:     {model}")
    print(f"  {_('delete.created')}:    {created}")
    print(f"  {_('delete.messages')}:  {msg_count}")
    print(f"  {_('delete.parts')}:     {part_count}")
    print(f"  {_('delete.cost')}:  {format_cost(info['cost'])}")

    if dry_run:
        print(f"\n{_('delete.dry_run')}")
        print(f"  {_('delete.dry_run_hint')}")
        return 0

    if not force and not confirm(_("delete.confirm", id=sid[:24])):
        print(_("canceled"))
        return 0

    db.execute("DELETE FROM session WHERE id = ?", (sid,))
    db.commit()

    print(f"\n{_('delete.done', id=sid[:24])}")
    print(_("delete.done_detail", msg=msg_count, parts=part_count))
    return 0


def _build_mass_conditions(args):
    """Строит условия WHERE для массового удаления."""
    conditions = []
    params = []
    project = _a(args, "project")
    older_than = _a(args, "older_than")
    before = _a(args, "before")
    after = _a(args, "after")

    if project:
        conditions.append("s.project_id = ?")
        params.append(project)

    if older_than:
        cutoff = parse_time_spec(older_than)
        if cutoff is None:
            return None, None, _("delete.bad_spec", spec=older_than)
        conditions.append("s.time_created < ?")
        params.append(int(cutoff.timestamp() * 1000))

    if before:
        dt = parse_date(before)
        if dt is None:
            return None, None, _("delete.bad_date", date=before)
        conditions.append("s.time_created < ?")
        params.append(int(dt.timestamp() * 1000))

    if after:
        dt = parse_date(after)
        if dt is None:
            return None, None, _("delete.bad_date", date=after)
        conditions.append("s.time_created > ?")
        params.append(int(dt.timestamp() * 1000))

    return conditions, params, None


def _collect_mass_targets(db, conditions, params, keep_last):
    """Собирает список сессий для массового удаления."""
    exclude_ids = set()
    if keep_last:
        inner_where = " AND ".join(conditions) if conditions else "1=1"
        keep_rows = db.execute(
            f"""
            SELECT s.id FROM session s
            WHERE {inner_where}
            ORDER BY s.time_created DESC
            LIMIT ?
        """,
            (*params, keep_last),
        ).fetchall()
        exclude_ids = {r["id"] for r in keep_rows}

    where = " AND ".join(conditions) if conditions else "1=1"

    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        rows = db.execute(
            f"""
            SELECT s.id, s.title, s.model, s.time_created, s.cost
            FROM session s
            WHERE {where}
              AND s.id NOT IN ({placeholders})
            ORDER BY s.time_created DESC
        """,
            (*params, *exclude_ids),
        ).fetchall()
    else:
        rows = db.execute(
            f"""
            SELECT s.id, s.title, s.model, s.time_created, s.cost
            FROM session s
            WHERE {where}
            ORDER BY s.time_created DESC
        """,
            params,
        ).fetchall()

    return rows


def _delete_mass(db, args) -> int:
    """Массовое удаление сессий."""
    keep_last = _a(args, "keep_last")
    dry_run = _a(args, "dry_run", False)
    force = _a(args, "force", False)

    conditions, params, err = _build_mass_conditions(args)
    if err:
        print(err)
        return 1

    if not conditions and not keep_last:
        print(_("delete.filter_required"))
        return 1

    target_rows = _collect_mass_targets(db, conditions, params, keep_last)

    if not target_rows:
        print(_("delete.none"))
        return 0

    total_cost = sum(r["cost"] or 0 for r in target_rows)
    total_tokens = sum(
        db.execute(
            "SELECT COALESCE(SUM(tokens_input + tokens_output), 0) FROM session WHERE id = ?",
            (r["id"],),
        ).fetchone()[0]
        for r in target_rows
    )

    print(f"\n  {'=' * 55}")
    print(f"  {_('delete.mass_header', n=len(target_rows))}")
    print(f"  {'=' * 55}")

    for r in target_rows[:20]:
        created = format_ts(r["time_created"])
        print(f"    • {r['id'][:24]}  {created}  {r['title'] or '—'}")

    if len(target_rows) > 20:
        print(f"    … и ещё {len(target_rows) - 20}")

    print(f"\n  {_('delete.cost_total', cost=f'${total_cost:.4f}')}")
    print(f"  {_('delete.tokens_total', n=str(total_tokens))}")

    if dry_run:
        print(f"\n{_('delete.dry_run')}")
        return 0

    if not force and not confirm(_("delete.mass_confirm", n=len(target_rows))):
        print(_("canceled"))
        return 0

    ids = [r["id"] for r in target_rows]
    placeholders = ",".join("?" for _ in ids)

    db.execute(f"DELETE FROM part WHERE session_id IN ({placeholders})", ids)
    db.execute(f"DELETE FROM message WHERE session_id IN ({placeholders})", ids)
    db.execute(f"DELETE FROM todo WHERE session_id IN ({placeholders})", ids)
    db.execute(f"DELETE FROM session WHERE id IN ({placeholders})", ids)
    db.commit()

    print(f"\n{_('delete.done_mass', n=len(ids))}")
    return 0


def _delete_interactive(db, args) -> int:
    """Интерактивное удаление — выбор из списка последних сессий."""
    sessions = get_recent_sessions(db, limit=20)

    if not sessions:
        print(_("delete.no_sessions"))
        return 1

    print(f"\n  {_('delete.interactive_header')}")
    print(f"  {'─' * 55}")
    for i, s in enumerate(sessions, 1):
        title = get_session_title(s)
        project = s.get("project_id", "") or ""
        print(f"  {i:2d}) {s['id'][:24]}  {title[:40]:40s}  {project[:20]}")

    print()
    choices = input(_("delete.interactive_prompt")).strip()

    if not choices:
        print(_("canceled"))
        return 0

    selected = _parse_choices(choices, len(sessions))
    if not selected:
        return 1

    target_rows = [sessions[i - 1] for i in selected]
    total_cost = sum(r["cost"] or 0 for r in target_rows)

    print(f"\n  {'=' * 55}")
    print(f"  {_('delete.mass_header', n=len(target_rows))}")
    print(f"  {'=' * 55}")
    for r in target_rows:
        created = format_ts(r["time_created"])
        print(f"    • {r['id'][:24]}  {created}  {r['title'] or '—'}")

    dry_run = _a(args, "dry_run", False)
    force = _a(args, "force", False)
    print(f"\n  {_('delete.cost_total', cost=f'${total_cost:.4f}')}")

    if dry_run:
        print(f"\n{_('delete.dry_run')}")
        return 0

    if not force and not confirm(_("delete.mass_confirm", n=len(target_rows))):
        print(_("canceled"))
        return 0

    ids = [r["id"] for r in target_rows]
    placeholders = ",".join("?" for _ in ids)

    db.execute(f"DELETE FROM part WHERE session_id IN ({placeholders})", ids)
    db.execute(f"DELETE FROM message WHERE session_id IN ({placeholders})", ids)
    db.execute(f"DELETE FROM todo WHERE session_id IN ({placeholders})", ids)
    db.execute(f"DELETE FROM session WHERE id IN ({placeholders})", ids)
    db.commit()

    print(f"\n{_('delete.done_mass', n=len(ids))}")
    return 0


def _parse_choices(text: str, max_n: int) -> list[int]:
    """Парсит ввод пользователя вида '1,3-5,7' в список индексов."""
    result = set()
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                for i in range(int(a), int(b) + 1):
                    if 1 <= i <= max_n:
                        result.add(i)
            except ValueError:
                continue
        else:
            try:
                i = int(part)
                if 1 <= i <= max_n:
                    result.add(i)
            except ValueError:
                continue
    return sorted(result)


_SESSION_SCOPED_TABLES = (
    "part",
    "message",
    "todo",
    "session_message",
    "session_input",
    "session_context_epoch",
    "session_share",
)
_EVENT_SCOPED_TABLES = ("event", "event_sequence")


def _missing_directory_targets(db, project_id=None):
    where = "WHERE directory IS NOT NULL AND directory != ''"
    params = []
    if project_id:
        where += " AND project_id = ?"
        params.append(project_id)
    rows = db.execute(
        f"SELECT id, title, directory, time_created, cost FROM session {where}",
        params,
    ).fetchall()
    return [dict(row) for row in rows if not os.path.isdir(row["directory"])]


def _delete_in_chunks(db, table, column, ids):
    deleted = 0
    for start in range(0, len(ids), 500):
        chunk = ids[start : start + 500]
        placeholders = ",".join("?" for _ in chunk)
        cur = db.execute(f"DELETE FROM {table} WHERE {column} IN ({placeholders})", chunk)
        deleted += max(cur.rowcount, 0)
    return deleted


def _delete_session_rows(db, ids, tables):
    db.execute("PRAGMA foreign_keys=ON")
    deleted = 0
    for table in _EVENT_SCOPED_TABLES:
        if table in tables:
            deleted += _delete_in_chunks(db, table, "aggregate_id", ids)
    for table in _SESSION_SCOPED_TABLES:
        if table in tables:
            deleted += _delete_in_chunks(db, table, "session_id", ids)
    deleted += _delete_in_chunks(db, "session", "id", ids)
    return deleted


def _backup_database(db, db_path):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = f"{db_path}.bak.{stamp}"
    suffix = 1
    while os.path.exists(target):
        target = f"{db_path}.bak.{stamp}-{suffix}"
        suffix += 1
    dest = sqlite3.connect(target)
    try:
        db.backup(dest)
    finally:
        dest.close()
    return target


def _delete_missing_dirs(db, args) -> int:
    incompatible = any(
        _a(args, name)
        for name in ("older_than", "before", "after", "keep_last", "interactive", "session_id")
    )
    if incompatible:
        print(_("delete.missing_incompatible"))
        return 1

    backup = _a(args, "backup", False)
    no_backup = _a(args, "no_backup", False)
    if backup and no_backup:
        print(_("delete.missing_both_backup"))
        return 1

    project_id = _a(args, "project")
    targets = _missing_directory_targets(db, project_id)
    if not targets:
        print(_("delete.missing_none"))
        return 0

    db_path = resolve_db_path()[0]
    groups = {}
    for target in targets:
        groups.setdefault(target["directory"], []).append(target)
    total_cost = sum(target["cost"] or 0 for target in targets)
    times = [target["time_created"] for target in targets if target["time_created"]]
    first_ts = min(times) if times else None
    last_ts = max(times) if times else None

    print(f"\n  {'=' * 60}")
    print(f"  {_('delete.missing_header')}")
    print(f"  {'=' * 60}")
    print(_("delete.missing_db", path=db_path))
    print(_("delete.missing_summary", sessions=len(targets), dirs=len(groups), cost=format_cost(total_cost)))
    first_label = format_ts(first_ts) if first_ts else "—"
    last_label = format_ts(last_ts) if last_ts else "—"
    print(f"  {first_label} — {last_label}")
    for path in sorted(groups):
        print(_("delete.missing_dir_line", path=path, n=len(groups[path])))

    if not _a(args, "execute", False) or _a(args, "dry_run", False):
        print(f"\n{_('delete.missing_preview')}")
        return 0

    if not backup and not no_backup:
        print(_("delete.missing_backup_choice"))
        return 1
    if no_backup:
        print(_("delete.missing_no_backup_warning"))

    phrase = f"DELETE {len(targets)} SESSIONS"
    try:
        answer = input(_("delete.missing_phrase_prompt", phrase=phrase))
    except EOFError:
        print(_("canceled"))
        return 0
    if answer.strip() != phrase:
        print(_("delete.missing_phrase_mismatch"))
        return 0

    if not confirm(_("delete.missing_final_confirm", n=len(targets))):
        print(_("canceled"))
        return 0

    if backup:
        try:
            backup_path = _backup_database(db, db_path)
        except Exception as exc:
            print(_("delete.missing_backup_failed", error=exc))
            return 1
        print(_("delete.missing_backup_done", path=backup_path))

    fresh = _missing_directory_targets(db, project_id)
    fresh_ids = {target["id"] for target in fresh}
    target_ids = {target["id"] for target in targets}
    if fresh_ids != target_ids:
        print(_("delete.missing_changed"))
        return 1

    try:
        deleted = _delete_session_rows(db, sorted(target_ids), set(open_store(db).schema.tables))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(_("delete.missing_error", error=exc))
        return 1

    print(_("delete.missing_done", n=len(target_ids), rows=deleted))
    return 0


def _a(args, name: str, default=None):
    """getattr с дефолтом — для совместимости Namespace из разных парсеров."""
    return getattr(args, name, default)


def run(args, db) -> int:
    store = open_store(db)
    if store.schema.read_only:
        print(_("schema.unsupported_write"))
        return 1
    if _a(args, "execute", False) and not _a(args, "missing_directories", False):
        print(_("delete.missing_execute_requires"))
        return 1
    if _a(args, "missing_directories", False):
        return _delete_missing_dirs(db, args)
    if _a(args, "interactive", False):
        return _delete_interactive(db, args)

    if _a(args, "session_id"):
        session_id = _a(args, "session_id")
        dry_run = _a(args, "dry_run", False)
        force = _a(args, "force", False)
        return _delete_single(db, session_id, dry_run, force)

    older_than = _a(args, "older_than")
    before = _a(args, "before")
    after = _a(args, "after")
    keep_last = _a(args, "keep_last")
    project = _a(args, "project")
    if older_than or before or after or keep_last or project:
        return _delete_mass(db, args)

    print(_("delete.usage"))
    return 1
