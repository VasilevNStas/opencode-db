"""Команда costs: анализ расходов на токены.

Стоимость берётся напрямую из поля session.cost БД OpenCode.
"""

from db import SessionError, get_session_info, get_session_title, parse_model
from i18n import _
from utils import format_cost, format_tokens


def register(subparsers) -> None:
    p = subparsers.add_parser("costs", help=_("help.cmd.costs"))
    p.add_argument("session_id", nargs="?", help="Session ID")
    p.add_argument("--project", type=str, help="Filter by project")
    p.add_argument("--total", action="store_true", help="Total across all sessions")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--limit", type=int, default=30, help="Max rows")


def run(args, db) -> int:
    if args.session_id:
        return _show_session(db, args.session_id, args.json)

    if args.total:
        return _show_total(db, args.project, args.json)

    return _show_list(db, args.project, args.limit, args.json)


def _show_session(db, session_id, as_json) -> int:
    try:
        info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    title = get_session_title(info)
    model = parse_model(info)

    ti = info["tokens_input"] or 0
    to = info["tokens_output"] or 0
    tr = info["tokens_reasoning"] or 0
    cost = info["cost"] or 0

    if as_json:
        from formatters import print_json

        print_json(
            {
                "id": info["id"],
                "title": title,
                "model": model,
                "tokens_input": ti,
                "tokens_output": to,
                "tokens_reasoning": tr,
                "tokens_total": ti + to + tr,
                "cost": cost,
            }
        )
        return 0

    print(f"\n  {_('costs.session')}: {title}")
    print(f"  {_('costs.model')}: {model}")
    print(f"  {'─' * 50}")
    print(f"  {_('costs.input')}:        {format_tokens(ti)}")
    print(f"  {_('costs.output')}:       {format_tokens(to)}")
    print(f"  {_('costs.reasoning')}:   {format_tokens(tr)}")
    if info["tokens_cache_read"]:
        print(f"  {_('costs.cache_read')}: {format_tokens(info['tokens_cache_read'])}")
    if info["tokens_cache_write"]:
        print(f"  {_('costs.cache_write')}:  {format_tokens(info['tokens_cache_write'])}")
    print(f"  {'─' * 50}")
    print(f"  {_('costs.total')}:       {format_tokens(ti + to + tr)}")
    print(f"  {_('costs.cost')}:   {format_cost(cost)}")
    print()
    return 0


def _show_total(db, project_id, as_json) -> int:
    where = "1=1"
    params = []

    if project_id:
        where = "s.project_id = ?"
        params.append(project_id)

    row = db.execute(
        f"""
        SELECT COUNT(*) as cnt,
               SUM(tokens_input) as ti, SUM(tokens_output) as tok_out,
               SUM(tokens_reasoning) as tr, SUM(cost) as c
        FROM session WHERE {where}
    """,
        params,
    ).fetchone()

    cnt = row["cnt"] or 0
    total_cost = row["c"] or 0
    total_ti = row["ti"] or 0
    total_to = row["tok_out"] or 0
    total_tr = row["tr"] or 0

    if as_json:
        from formatters import print_json

        print_json(
            {
                "sessions": cnt,
                "tokens_input": total_ti,
                "tokens_output": total_to,
                "tokens_reasoning": total_tr,
                "tokens_total": total_ti + total_to + total_tr,
                "cost": total_cost,
            }
        )
        return 0

    scope = _("costs.scope_project") if project_id else _("costs.scope_all")
    print(f"\n  {'=' * 45}")
    print(f"  {_('costs.total_header', scope=scope)}")
    print(f"  {_('costs.sessions')}:        {cnt}")
    print(f"  {'=' * 45}")
    print(f"  {_('costs.tokens_input')}:     {format_tokens(total_ti)}")
    print(f"  {_('costs.tokens_output')}:    {format_tokens(total_to)}")
    print(f"  {_('costs.tokens_reasoning')}: {format_tokens(total_tr)}")
    print(f"  {_('costs.tokens_total')}:     {format_tokens(total_ti + total_to + total_tr)}")
    print(f"  {_('costs.cost')}:         {format_cost(total_cost)}")
    print()
    return 0


def _show_list(db, project_id, limit, as_json) -> int:
    where = "1=1"
    params = []

    if project_id:
        where = "s.project_id = ?"
        params.append(project_id)

    rows = db.execute(
        f"""
        SELECT s.id, s.title, s.model,
               s.tokens_input, s.tokens_output, s.tokens_reasoning,
               s.cost
        FROM session s
        WHERE {where}
        ORDER BY (s.tokens_input + s.tokens_output) DESC
        LIMIT ?
    """,
        (*params, limit),
    ).fetchall()

    if as_json:
        from formatters import print_json

        data = []
        for r in rows:
            data.append(
                {
                    "id": r["id"],
                    "title": get_session_title(r),
                    "model": parse_model(r),
                    "tokens_total": (r["tokens_input"] or 0)
                    + (r["tokens_output"] or 0)
                    + (r["tokens_reasoning"] or 0),
                    "cost": r["cost"] or 0,
                }
            )
        print_json(data)
        return 0

    from formatters import print_table_simple

    table = []
    for r in rows:
        total_tokens = (
            (r["tokens_input"] or 0) + (r["tokens_output"] or 0) + (r["tokens_reasoning"] or 0)
        )
        table.append(
            [
                r["id"][:24],
                get_session_title(r)[:28],
                parse_model(r)[:20],
                format_tokens(total_tokens),
                format_cost(r["cost"] or 0),
            ]
        )

    print_table_simple(
        [
            _("list.header.id"),
            _("list.header.title"),
            _("list.header.model"),
            _("costs.total"),
            _("costs.cost"),
        ],
        table,
    )

    return 0
