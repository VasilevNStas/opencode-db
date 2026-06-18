"""Команда delete: удаление сессии или массовая очистка."""

import argparse

from db import (
    SessionError,
    get_message_count,
    get_part_count,
    get_recent_sessions,
    get_session_info,
    get_session_title,
    parse_model,
)
from i18n import _
from utils import build_help_epilog, confirm, format_cost, format_ts, parse_date, parse_time_spec

_DELETE_EXAMPLES = [
    ("<session_id>", "help.delete.e0"),
    ("<session_id> --dry-run", "help.delete.e1"),
    ("<session_id> --force", "help.delete.e2"),
    ("--older-than 90d", "help.delete.e3"),
    ("--keep-last 30", "help.delete.e4"),
    ("--before 2026-05-20", "help.delete.e5"),
    ("--interactive", "help.delete.e6"),
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


def _a(args, name: str, default=None):
    """getattr с дефолтом — для совместимости Namespace из разных парсеров."""
    return getattr(args, name, default)


def run(args, db) -> int:
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
