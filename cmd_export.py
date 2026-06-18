"""Команда export: экспорт диалога в Markdown.

Режимы выбора сессии:
  - export <session_id>          — по ID (полный или префикс)
  - export --latest              — самая свежая сессия
  - export (без аргументов)      — интерактивный выбор из списка
"""

import os

from db import (
    SessionError,
    get_latest_session,
    get_messages,
    get_recent_sessions,
    get_session_info,
    get_session_title,
    parse_model,
)
from formatters import collect_snapshot, format_part_to_md, update_log
from i18n import _
from utils import format_cost, format_ts, format_ts_short


def register(subparsers) -> None:
    p = subparsers.add_parser("export", help=_("help.cmd.export"))
    p.add_argument(
        "session_id",
        nargs="?",
        help="Session ID (optional — interactive mode if omitted)",
    )
    p.add_argument("--latest", "-l", action="store_true", help="Export the most recent session")
    p.add_argument(
        "--full",
        "-F",
        action="store_true",
        help="Full output (do not truncate tool outputs)",
    )
    p.add_argument("--force", "-f", action="store_true", help="Overwrite existing file")
    p.add_argument("--note", "-n", type=str, help="Description for log.md")
    p.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output directory (default: current)",
    )


def _export_by_id(db, session_id, output_dir, force, note, full) -> int:
    try:
        session_info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    return _do_export(db, session_info, output_dir, force, note, full)


def _export_latest(db, output_dir, force, note, full) -> int:
    try:
        session_id = get_latest_session(db)
        session_info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    title = get_session_title(session_info)
    print(_("session.latest", title=title))
    return _do_export(db, session_info, output_dir, force, note, full)


def _export_interactive(db, output_dir, force, note, full) -> int:
    sessions = get_recent_sessions(db)

    if not sessions:
        print(_("export.no_sessions"))
        return 1

    print(f"\n  {'─' * 60}")
    print(f"  {_('export.interactive_header')}")
    print(f"  {'─' * 60}")

    for i, s in enumerate(sessions, 1):
        title = get_session_title(s)
        created = format_ts(s["time_created"], "%Y-%m-%d %H:%M")
        cost = format_cost(s["cost"])
        print(f"  {i:2d}. {s['id'][:24]}  {created}  {title[:40]:40s}  {cost}")

    print(f"  {'─' * 60}")

    while True:
        try:
            choice = input("  " + _("export.interactive_prompt")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1

        if not choice:
            print(_("export.interactive_abort"))
            return 1

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                break
        except ValueError:
            pass

        print(f"  {_('export.interactive_error', n=len(sessions))}")

    session_id = sessions[idx]["id"]
    title = get_session_title(sessions[idx])
    print(_("export.interactive_exporting", title=title))
    try:
        session_info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    return _do_export(db, session_info, output_dir, force, note, full)


def _do_export(db, session_info, output_dir, force, note, full=False) -> int:
    """Внутренняя функция: экспорт диалога."""
    title = get_session_title(session_info)
    model = parse_model(session_info)

    messages = get_messages(db, session_info["id"])

    date_str = format_ts_short(session_info["time_created"])
    filename = os.path.join(output_dir, f"opencode-{date_str}.md")

    if os.path.isfile(filename) and not force:
        print(_("export.exists", path=filename))
        print(_("export.exists_hint"))
        return 1

    date_display = format_ts(session_info["time_created"])

    md_header = f"""# {_("md.header.title")}: {title}

- **{_("md.header.date")}**: {date_display}
- **{_("md.header.model")}**: {model}
- **{_("md.header.session_id")}**: `{session_info["id"][:24]}`
- **{_("md.header.messages")}**: {len(messages)}

---
"""

    md_body = []
    for msg in messages:
        if not msg.get("parts"):
            continue

        ts = format_ts(msg["time"], "%H:%M:%S")

        if msg["role"] == "user":
            md_body.append(f"## {_('export.role_user', ts=ts)}")
        else:
            agent_tag = _("export.agent_tag", agent=msg["agent"]) if msg.get("agent") else ""
            md_body.append(f"## {_('export.role_assistant', ts=ts, agent=agent_tag)}")

        md_body.append("")

        for part in msg["parts"]:
            formatted = format_part_to_md(part, full=full)
            if formatted:
                md_body.append(formatted)
                md_body.append("")

        md_body.append("---")
        md_body.append("")

    content = md_header + "\n".join(md_body)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(_("export.saved", path=filename))
    print(_("export.messages", n=len(messages)))

    obsidian_dir = os.getcwd()
    if os.path.isdir(os.path.join(obsidian_dir, ".obsidian")):
        snapshot = collect_snapshot(obsidian_dir)
        now_str = format_ts(session_info["time_created"], "%Y-%m-%d %H:%M")
        update_log(obsidian_dir, title, note, filename, snapshot, now_str)
    else:
        print(_("not_obsidian"))

    return 0


def run(args, db) -> int:
    output_dir = args.output or os.getcwd()
    full = args.full

    if args.session_id:
        return _export_by_id(db, args.session_id, output_dir, args.force, args.note, full)

    if args.latest:
        return _export_latest(db, output_dir, args.force, args.note, full)

    return _export_interactive(db, output_dir, args.force, args.note, full)
