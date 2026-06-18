"""Команда info: детальная информация о сессии."""

from db import (
    SessionError,
    get_children_sessions,
    get_message_count,
    get_parent_session,
    get_part_count,
    get_project_name,
    get_session_info,
    get_session_title,
    get_session_todos,
    parse_model,
)
from i18n import _
from utils import format_cost, format_tokens, format_ts


def register(subparsers) -> None:
    p = subparsers.add_parser("info", help=_("help.cmd.info"))
    p.add_argument("session_id", help="Session ID")
    p.add_argument("--json", action="store_true", help="JSON output")


def run(args, db) -> int:
    try:
        info = get_session_info(db, args.session_id)
    except SessionError as e:
        print(e.message)
        return 1
    session_id = info["id"]
    msg_count = get_message_count(db, session_id)
    part_count = get_part_count(db, session_id)
    children = get_children_sessions(db, session_id)
    parent = get_parent_session(db, session_id)
    todos = get_session_todos(db, session_id)
    project_name = get_project_name(db, info["project_id"]) if info["project_id"] else "—"

    model = parse_model(info)
    title = get_session_title(info)
    created = format_ts(info["time_created"])
    updated = format_ts(info["time_updated"])

    if info["time_updated"] and info["time_created"]:
        duration_sec = (info["time_updated"] - info["time_created"]) / 1000
        if duration_sec < 60:
            duration = _("info.dur_sec", n=int(duration_sec))
        elif duration_sec < 3600:
            duration = _("info.dur_min", n=int(duration_sec / 60))
        else:
            hours = int(duration_sec / 3600)
            mins = int((duration_sec % 3600) / 60)
            duration = _("info.dur_hours", h=hours, m=mins)
    else:
        duration = "—"

    if args.json:
        data = {
            "id": info["id"],
            "title": title,
            "project": {"id": info["project_id"], "name": project_name},
            "model": model,
            "agent": info["agent"],
            "version": info["version"],
            "directory": info["directory"],
            "parent_id": info["parent_id"],
            "time_created": created,
            "time_updated": updated,
            "duration": duration,
            "messages": msg_count,
            "parts": part_count,
            "cost": info["cost"],
            "tokens": {
                "input": info["tokens_input"],
                "output": info["tokens_output"],
                "reasoning": info["tokens_reasoning"],
                "cache_read": info["tokens_cache_read"],
                "cache_write": info["tokens_cache_write"],
            },
            "code_changes": {
                "additions": info["summary_additions"],
                "deletions": info["summary_deletions"],
                "files": info["summary_files"],
            },
            "children": [{"id": c["id"], "title": c["title"]} for c in children]
            if children
            else [],
            "todos": [{"content": t["content"], "status": t["status"]} for t in todos]
            if todos
            else [],
        }
        if parent:
            data["parent"] = {"id": parent["id"], "title": parent["title"]}

        from formatters import print_json

        print_json(data)
        return 0

    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(f"  {_('info.id')}:        {session_id}")
    print(f"  {_('info.project')}:    {project_name} ({info['project_id'][:24]})")
    print(f"  {_('info.model')}:    {model}")
    print(f"  {_('info.agent')}:     {info['agent'] or '—'}")
    print(f"  {_('info.version')}:    {info['version'] or '—'}")
    print(f"  {_('info.created')}:   {created}")
    print(f"  {_('info.updated')}:   {updated}")
    print(f"  {_('info.duration')}:  {duration}")

    if parent:
        parent_title = parent["title"] or _("info.unnamed")
        print(f"  {_('info.parent')}:  {parent['id'][:24]} — {parent_title}")

    if children:
        print(f"  {_('info.branches')}:     {len(children)}")
        for c in children:
            c_title = c["title"] or _("info.unnamed")
            print(_("info.children_prefix", id=c["id"][:24], title=c_title))

    print(f"\n  {'─' * 56}")
    print(f"  {_('info.messages')}: {msg_count}")
    print(f"  {_('info.parts')}:    {part_count}")
    print(f"  {'─' * 56}")

    print(f"  {_('info.tokens_input')}:     {format_tokens(info['tokens_input'])}")
    print(f"  {_('info.tokens_output')}:    {format_tokens(info['tokens_output'])}")
    print(f"  {_('info.tokens_reasoning')}: {format_tokens(info['tokens_reasoning'])}")
    if info["tokens_cache_read"]:
        print(f"  {_('info.cache_read')}:     {format_tokens(info['tokens_cache_read'])}")
    if info["tokens_cache_write"]:
        print(f"  {_('info.cache_write')}:      {format_tokens(info['tokens_cache_write'])}")
    total_tokens = (info["tokens_input"] or 0) + (info["tokens_output"] or 0)
    print(f"  {_('info.tokens_total')}:    {format_tokens(total_tokens)}")
    print(f"  {_('info.cost')}:        {format_cost(info['cost'])}")

    if info["summary_files"]:
        print(f"\n  {'─' * 56}")
        print(f"  {_('info.code_changes')}:")
        print(f"    {_('info.files_changed')}:    {info['summary_files']}")
        print(f"    {_('info.lines_added')}: {info['summary_additions'] or 0}")
        print(f"    {_('info.lines_deleted')}:   {info['summary_deletions'] or 0}")

    if todos:
        print(f"\n  {'─' * 56}")
        print(f"  {_('info.todos')}:")
        status_icon = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
        for t in todos:
            icon = status_icon.get(t["status"], "📝")
            print(f"    {icon} {t['content'][:60]}")

    print()
    return 0
