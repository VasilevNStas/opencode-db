"""Команда prune: массовая очистка старых сессий."""

# from db import get_session_info, get_session_title, parse_model, \
#     get_message_count, get_part_count
from typing import Literal

from i18n import _
from utils import confirm, format_ts, parse_time_spec


def register(subparsers) -> None:
    p = subparsers.add_parser("prune", help=_("help.cmd.prune"))
    p.add_argument("--older-than", type=str, help="Delete sessions older than (30d, 6m, 1y)")
    p.add_argument("--keep-last", type=int, help="Keep N most recent sessions")
    p.add_argument("--project", type=str, help="Limit to project")
    p.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")


def run(args, db) -> Literal[1] | Literal[0]:
    if not args.older_than and not args.keep_last and not args.project:
        print(_("prune.filter_required"))
        print(_("prune.filter_example"))
        return 1

    conditions = []
    params = []

    if args.project:
        conditions.append("s.project_id = ?")
        params.append(args.project)

    if args.older_than:
        cutoff = parse_time_spec(args.older_than)
        if cutoff is None:
            print(_("prune.bad_spec", spec=args.older_than))
            print(_("prune.bad_spec_hint"))
            return 1
        cutoff_ms = int(cutoff.timestamp() * 1000)
        conditions.append("s.time_created < ?")
        params.append(cutoff_ms)

    exclude_ids = set()
    if args.keep_last:
        inner_where = " AND ".join(conditions) if conditions else "1=1"
        keep_rows = db.execute(
            f"""
            SELECT s.id FROM session s
            WHERE {inner_where}
            ORDER BY s.time_created DESC
            LIMIT ?
        """,
            (*params, args.keep_last),
        ).fetchall()
        exclude_ids = {r["id"] for r in keep_rows}

    where = " AND ".join(conditions) if conditions else "1=1"

    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        target_rows = db.execute(
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
        target_rows = db.execute(
            f"""
            SELECT s.id, s.title, s.model, s.time_created, s.cost
            FROM session s
            WHERE {where}
            ORDER BY s.time_created DESC
        """,
            params,
        ).fetchall()

    if not target_rows:
        print(_("prune.none"))
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
    print(f"  {_('prune.header', n=len(target_rows))}")
    print(f"  {'=' * 55}")

    for r in target_rows[:20]:
        created = format_ts(r["time_created"])
        print(f"    • {r['id'][:16]}  {created}  {r['title'] or '—'}")

    if len(target_rows) > 20:
        print(f"    … и ещё {len(target_rows) - 20}")

    print(f"\n  {_('prune.cost_total', cost=f'${total_cost:.4f}')}")
    print(f"  {_('prune.tokens_total', n=str(total_tokens))}")

    if args.dry_run:
        print(f"\n{_('prune.dry_run')}")
        return 0

    if not args.force and not confirm(_("prune.confirm", n=len(target_rows))):
        print(_("canceled"))
        return 0

    ids_to_delete = [r["id"] for r in target_rows]
    placeholders = ",".join("?" for _ in ids_to_delete)

    db.execute(f"DELETE FROM part WHERE session_id IN ({placeholders})", ids_to_delete)
    db.execute(f"DELETE FROM message WHERE session_id IN ({placeholders})", ids_to_delete)
    db.execute(f"DELETE FROM todo WHERE session_id IN ({placeholders})", ids_to_delete)
    db.execute(f"DELETE FROM session WHERE id IN ({placeholders})", ids_to_delete)
    db.commit()

    print(f"\n{_('prune.done', n=len(ids_to_delete))}")
    return 0
