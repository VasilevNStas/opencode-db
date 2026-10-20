"""Команда costs: анализ расходов на токены.

Стоимость берётся напрямую из поля session.cost БД OpenCode.
"""

import argparse

from ..db import SessionError
from ..i18n import _
from ..store import open_store
from ..utils import build_help_epilog, format_cost, format_tokens

_COSTS_EXAMPLES = [
    ("", "help.costs.e0"),
    ("<session_id>", "help.costs.e1"),
    ("--total", "help.costs.e2"),
    ("--project proj_xxx", "help.costs.e3"),
    ("--json", "help.costs.e4"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "costs",
        help=_("help.cmd.costs"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("costs", _COSTS_EXAMPLES),
    )
    p.add_argument("session_id", nargs="?", help="Session ID")
    p.add_argument("--project", type=str, help="Filter by project")
    p.add_argument("--total", action="store_true", help="Total across all sessions")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--limit", type=int, default=30, help="Max rows")


def run(args, db) -> int:
    store = open_store(db)
    if args.session_id:
        return _show_session(store, args.session_id, args.json)

    if args.total:
        return _show_total(store, args.project, args.json)

    return _show_list(store, args.project, args.limit, args.json)


def _show_session(store, session_id, as_json) -> int:
    try:
        info = store.get_session_info(session_id)
    except SessionError as e:
        print(e.message)
        return 1
    title = store.get_session_title(info)
    model = store.parse_model(info)

    ti = info["tokens_input"] or 0
    to = info["tokens_output"] or 0
    tr = info["tokens_reasoning"] or 0
    cost = info["cost"] or 0

    if as_json:
        from ..formatters import print_json

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


def _show_total(store, project_id, as_json) -> int:
    row = store.get_cost_total(project_id)

    cnt = row["cnt"] or 0
    total_cost = row["c"] or 0
    total_ti = row["ti"] or 0
    total_to = row["tok_out"] or 0
    total_tr = row["tr"] or 0

    if as_json:
        from ..formatters import print_json

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


def _show_list(store, project_id, limit, as_json) -> int:
    rows = store.get_cost_list(project_id, limit)

    if as_json:
        from ..formatters import print_json

        data = []
        for r in rows:
            data.append(
                {
                    "id": r["id"],
                    "title": store.get_session_title(r),
                    "model": store.parse_model(r),
                    "tokens_total": (r["tokens_input"] or 0)
                    + (r["tokens_output"] or 0)
                    + (r["tokens_reasoning"] or 0),
                    "cost": r["cost"] or 0,
                }
            )
        print_json(data)
        return 0

    from ..formatters import print_table_simple

    table = []
    for r in rows:
        total_tokens = (
            (r["tokens_input"] or 0) + (r["tokens_output"] or 0) + (r["tokens_reasoning"] or 0)
        )
        table.append(
            [
                r["id"][:24],
                store.get_session_title(r)[:28],
                store.parse_model(r)[:20],
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
