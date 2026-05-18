"""Команда search: поиск по тексту сообщений и частей."""

import json
from typing import Literal

from db import resolve_session_id
from i18n import _
from utils import format_ts


def register(subparsers) -> None:
    p = subparsers.add_parser("search", help=_("help.cmd.search"))
    p.add_argument("query", help="Search text")
    p.add_argument("--session", type=str, help="Limit to session")
    p.add_argument("--limit", type=int, default=30, help="Max results")
    p.add_argument("--json", action="store_true", help="JSON output")


def _search_in_part_data(
    data, query_lower
) -> tuple[Literal[False], Literal[""]] | tuple[Literal[True], str]:
    """Ищет query в part.data (JSON), проверяя текстовые поля."""
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
            for v in t_input.values():
                if isinstance(v, str) and query_lower in v.lower():
                    return True, f"[tool] {str(v)[:200]}"
        if isinstance(t_output, str) and query_lower in t_output.lower():
            return True, f"[output] {t_output[:200]}"

    return False, ""


def run(args, db) -> Literal[0]:
    query_lower = args.query.lower()

    conditions = []
    params = []

    if args.session:
        full_id = resolve_session_id(db, args.session)
        conditions.append("p.session_id = ?")
        params.append(full_id)

    where = " AND ".join(conditions) if conditions else "1=1"

    rows = db.execute(
        f"""
        SELECT p.id, p.session_id, p.message_id, p.data,
               m.time_created,
               json_extract(m.data, '$.role') as role
        FROM part p
        JOIN message m ON m.id = p.message_id
        WHERE {where}
          AND p.data IS NOT NULL
        ORDER BY p.time_created DESC
        LIMIT ?
    """,
        (*params, args.limit * 5),
    ).fetchall()

    results = []
    for r in rows:
        found, snippet = _search_in_part_data(r["data"], query_lower)
        if found:
            results.append(
                {
                    "session_id": r["session_id"][:16],
                    "message_id": r["message_id"][:12],
                    "role": r["role"],
                    "time": format_ts(r["time_created"]) if r["time_created"] else "—",
                    "snippet": snippet,
                }
            )
        if len(results) >= args.limit:
            break

    if args.json:
        from formatters import print_json

        print_json(results)
        return 0

    if not results:
        print(_("search.none", query=args.query))
        return 0

    print(_("search.header", query=args.query))
    print(f"  {'─' * 60}")

    for r in results:
        print(f"  [{r['time']}] {r['role']}  {r['session_id']}  msg:{r['message_id']}")
        print(f"    {r['snippet']}")
        print()

    print(_("search.found", n=len(results)))
    return 0
