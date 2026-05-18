"""Команда stats: общая статистика по базе данных."""

from typing import Literal

from db import parse_model
from i18n import _
from utils import format_cost, format_tokens, format_ts


def register(subparsers) -> None:
    p = subparsers.add_parser("stats", help=_("help.cmd.stats"))
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> Literal[0]:
    session_count = db.execute("SELECT COUNT(*) FROM session").fetchone()[0]
    message_count = db.execute("SELECT COUNT(*) FROM message").fetchone()[0]
    part_count = db.execute("SELECT COUNT(*) FROM part").fetchone()[0]
    project_count = db.execute("SELECT COUNT(*) FROM project").fetchone()[0]
    todo_count = db.execute("SELECT COUNT(*) FROM todo").fetchone()[0]

    totals = db.execute("""
        SELECT
            COALESCE(SUM(cost), 0) as total_cost,
            COALESCE(SUM(tokens_input), 0) as total_ti,
            COALESCE(SUM(tokens_output), 0) as total_to,
            COALESCE(SUM(tokens_reasoning), 0) as total_tr,
            COALESCE(SUM(tokens_cache_read), 0) as total_cr,
            COALESCE(SUM(tokens_cache_write), 0) as total_cw
        FROM session
    """).fetchone()

    first_last = db.execute("""
        SELECT MIN(time_created) as first_ts, MAX(time_created) as last_ts
        FROM session
    """).fetchone()

    top_models = db.execute("""
        SELECT model, COUNT(*) as cnt, SUM(cost) as cost
        FROM session
        WHERE model IS NOT NULL
        GROUP BY model
        ORDER BY cnt DESC
        LIMIT 5
    """).fetchall()

    agents = db.execute("""
        SELECT agent, COUNT(*) as cnt
        FROM session
        WHERE agent IS NOT NULL
        GROUP BY agent
        ORDER BY cnt DESC
    """).fetchall()

    if args.json:
        from formatters import print_json

        data = {
            "sessions": session_count,
            "messages": message_count,
            "parts": part_count,
            "projects": project_count,
            "todos": todo_count,
            "cost": totals["total_cost"],
            "tokens_input": totals["total_ti"],
            "tokens_output": totals["total_to"],
            "tokens_reasoning": totals["total_tr"],
            "tokens_cache_read": totals["total_cr"],
            "tokens_cache_write": totals["total_cw"],
            "tokens_total": totals["total_ti"] + totals["total_to"] + totals["total_tr"],
            "first_session": format_ts(first_last["first_ts"]) if first_last["first_ts"] else None,
            "last_session": format_ts(first_last["last_ts"]) if first_last["last_ts"] else None,
            "top_models": [
                {"model": parse_model(m), "count": m["cnt"], "cost": m["cost"]} for m in top_models
            ],
            "agents": [{"agent": a["agent"], "count": a["cnt"]} for a in agents],
        }
        print_json(data)
        return 0

    total_tokens = totals["total_ti"] + totals["total_to"] + totals["total_tr"]
    first_date = format_ts(first_last["first_ts"], "%Y-%m-%d") if first_last["first_ts"] else "—"
    last_date = format_ts(first_last["last_ts"], "%Y-%m-%d") if first_last["last_ts"] else "—"

    print(f"\n  {'=' * 50}")
    print(f"  {_('stats.header')}")
    print(f"  {'=' * 50}")
    print(f"  {_('stats.projects')}:       {project_count}")
    print(f"  {_('stats.sessions')}:         {session_count}")
    print(f"  {_('stats.messages')}:      {message_count}")
    print(f"  {_('stats.parts')}:         {part_count}")
    print(f"  {_('stats.todos')}:   {todo_count}")
    print(f"  {'─' * 50}")
    print(f"  {_('stats.first_session')}:  {first_date}")
    print(f"  {_('stats.last_session')}:      {last_date}")
    print(f"  {'─' * 50}")
    print(f"  {_('stats.tokens_input')}:     {format_tokens(totals['total_ti'])}")
    print(f"  {_('stats.tokens_output')}:    {format_tokens(totals['total_to'])}")
    print(f"  {_('stats.tokens_reasoning')}: {format_tokens(totals['total_tr'])}")
    print(f"  {_('stats.tokens_total')}:     {format_tokens(total_tokens)}")
    print(f"  {_('stats.cost')}:         {format_cost(totals['total_cost'])}")

    if top_models:
        print(f"\n  {_('stats.top_models')}:")
        for m in top_models:
            model_str = parse_model(m)
            print(f"    {m['cnt']:4d}×  {model_str:30s}  ({format_cost(m['cost'] or 0)})")

    if agents:
        print(f"\n  {_('stats.agents')}:")
        for a in agents:
            print(f"    {a['cnt']:4d}×  {a['agent']}")

    print()
    return 0
