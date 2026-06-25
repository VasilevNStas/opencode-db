"""Command view: просмотр сессии в терминале с прокруткой.

Выводит отформатированный диалог с ANSI-цветами,
автоматически использует $PAGER (less -R) для прокрутки.

Режимы выбора сессии:
  - view <session_id>          — по ID (полный или префикс)
  - view --latest              — самая свежая сессия
  - view (без аргументов)      — интерактивный выбор из списка
"""

import argparse
import os
import shutil
import subprocess
import sys

from db import (
    SessionError,
    get_latest_session,
    get_messages,
    get_project_name,
    get_recent_sessions,
    get_session_info,
    get_session_title,
    parse_model,
)
from i18n import _
from markdown_to_ansi import render as md_render
from utils import build_help_epilog, format_cost, format_tokens, format_ts

_VIEW_EXAMPLES = [
    ("<session_id>", "help.view.e0"),
    ("--latest", "help.view.e1"),
    ("", "help.view.e2"),
    ("--no-pager", "help.view.e3"),
    ("--raw", "help.view.e4"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "view",
        help=_("help.cmd.view"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("view", _VIEW_EXAMPLES),
    )
    p.add_argument(
        "session_id",
        nargs="?",
        help="Session ID (optional — interactive mode if omitted)",
    )
    p.add_argument("--latest", "-l", action="store_true", help=_("view.flag.latest"))
    p.add_argument("--no-pager", "-P", action="store_true", help=_("view.flag.no_pager"))
    p.add_argument("--raw", "-R", action="store_true", help=_("view.flag.raw"))


def run(args, db) -> int:
    if args.session_id:
        return _view_by_id(db, args.session_id, args.no_pager, args.raw)
    if args.latest:
        return _view_latest(db, args.no_pager, args.raw)
    return _view_interactive(db, args.no_pager, args.raw)


# ======================================================================
# Selection modes
# ======================================================================


def _view_by_id(db, session_id, no_pager, raw) -> int:
    try:
        info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    return _do_view(db, info, no_pager, raw)


def _view_latest(db, no_pager, raw) -> int:
    try:
        session_id = get_latest_session(db)
        info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    title = get_session_title(info)
    print(_("session.latest", title=title))
    return _do_view(db, info, no_pager, raw)


def _view_interactive(db, no_pager, raw) -> int:
    sessions = get_recent_sessions(db)
    if not sessions:
        print(_("view.no_sessions"))
        return 1

    print()
    print(f"  {'─' * 60}")
    print(f"  {_('view.interactive_header')}")
    print(f"  {'─' * 60}")

    for i, s in enumerate(sessions, 1):
        title = get_session_title(s)
        created = format_ts(s["time_created"], "%Y-%m-%d %H:%M")
        cost = format_cost(s["cost"])
        print(f"  {i:2d}. {s['id'][:24]}  {created}  {title[:40]:40s}  {cost}")

    print(f"  {'─' * 60}")

    while True:
        try:
            choice = input("  " + _("view.interactive_prompt")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1

        if not choice:
            print(_("view.interactive_abort"))
            return 1

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                break
        except ValueError:
            pass

        print(f"  {_('view.interactive_error', n=len(sessions))}")

    session_id = sessions[idx]["id"]
    title = get_session_title(sessions[idx])
    print(_("view.interactive_viewing", title=title))
    try:
        info = get_session_info(db, session_id)
    except SessionError as e:
        print(e.message)
        return 1
    return _do_view(db, info, no_pager, raw)


# ======================================================================
# Display engine
# ======================================================================


def _init_styles(raw=False):
    """Return style dict. Empty dict = no ANSI codes."""
    if raw or not sys.stdout.isatty():
        return {}
    return {
        "R": "\033[0m",
        "B": "\033[1m",
        "D": "\033[2m",
        "G": "\033[32m",
        "C": "\033[36m",
        "Y": "\033[33m",
        "M": "\033[90m",
    }


def _do_view(db, info, no_pager, raw) -> int:
    sty = _init_styles(raw)
    messages = get_messages(db, info["id"])
    text = _format_session(db, info, messages, sty)

    use_pager = not no_pager and sys.stdout.isatty() and len(text) > 1000
    if use_pager:
        _page_text(text)
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()

    return 0


def _format_session(db, info, messages, sty) -> str:
    """Build the full formatted session view string."""
    title = get_session_title(info)
    model = parse_model(info)
    created = format_ts(info["time_created"])
    msg_count = len(messages)

    duration = "—"
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

    ti = info["tokens_input"]
    to = info["tokens_output"]
    tr = info["tokens_reasoning"]
    tokens_str = f"{format_tokens(ti)} in · {format_tokens(to)} out"
    if tr:
        tokens_str += f" · {format_tokens(tr)} reason"

    cost = format_cost(info["cost"])

    project_name = None
    if info["project_id"]:
        project_name = get_project_name(db, info["project_id"])

    sep = f"{sty.get('M', '')}{'─' * 60}{sty.get('R', '')}"
    lr = sty.get("R", "")

    lines = []
    lines.append("")
    lines.append(f"{sty.get('B', '')}{sty.get('C', '')}🔍 {_('view.header')}{lr}")
    lines.append(sep)
    lines.append(f"  {_('info.id')}:       {info['id']}")
    lines.append(f"  {_('list.header.title')}: {title}")
    lines.append(f"  {_('info.model')}:   {model}")
    lines.append(f"  {_('info.agent')}:    {info['agent'] or '—'}")
    lines.append(f"  {_('info.created')}:  {created}")
    lines.append(f"  {_('info.duration')}: {duration}")
    lines.append(f"  {_('info.tokens_total')}: {tokens_str}")
    lines.append(f"  {_('info.cost')}:       {cost}")
    if project_name:
        lines.append(f"  {_('info.project')}:   {project_name}")
    lines.append(f"  {_('info.messages')}: {msg_count}")
    lines.append(sep)
    lines.append("")

    if not messages:
        lines.append(f"  {sty.get('M', '')}{_('view.no_messages')}{lr}")
        lines.append("")
        lines.append(sep)
        lines.append("")
    else:
        for msg in messages:
            role = msg.get("role", "unknown")
            ts = format_ts(msg.get("time"), "%Y-%m-%d %H:%M:%S") if msg.get("time") else ""
            agent = msg.get("agent", "")

            if role == "user":
                role_str = f"{sty.get('G', '')}👤 {_('view.role_user')} [{ts}]{lr}"
            elif role == "assistant":
                agent_tag = f" ({agent})" if agent else ""
                role_str = f"{sty.get('C', '')}🤖 {_('view.role_assistant')}{agent_tag} [{ts}]{lr}"
            else:
                role_str = f"{sty.get('Y', '')}⚙️ {role} [{ts}]{lr}"

            lines.append(sep)
            lines.append(role_str)
            lines.append(sep)

            for i, part in enumerate(msg.get("parts", [])):
                formatted = _format_part_ansi(part, sty)
                if formatted:
                    if i > 0:
                        lines.append("")
                    lines.append(formatted)

    lines.append(f"{sty.get('M', '')}─── {_('view.footer')} ───{lr}")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# Part formatting (ANSI version of format_part_to_md)
# ======================================================================


def _format_part_ansi(part, sty) -> str:
    """Форматирует часть сообщения с ANSI-цветами."""
    t = part.get("type", "")

    if t == "text":
        text = part.get("text", "").strip()
        if not text:
            return ""
        return md_render(text, sty, plain=not sty)

    if t == "reasoning":
        text = part.get("text", "").strip()
        if not text:
            return ""
        title = f"{sty.get('Y', '')}{sty.get('D', '')}💭 {_('md.reasoning')}:{sty.get('R', '')}"
        body = f"{sty.get('D', '')}{text}{sty.get('R', '')}"
        return f"{title}\n{body}"

    if t == "sound":
        return f"{sty.get('Y', '')}*🔊 {_('md.sound')}*{sty.get('R', '')}"

    if t == "tool":
        tool_name = part.get("tool", "?")
        t_input = part.get("input", {})
        t_output = part.get("output", "")
        t_status = part.get("status", "")

        icon = {"completed": "✅", "error": "❌", "running": "⏳"}.get(t_status, "🔧")
        y = sty.get("Y", "")
        r = sty.get("R", "")

        if tool_name == "read":
            fp = t_input.get("filePath", "")
            return f"{y}{icon} read:{r} `{fp}`"
        if tool_name == "write":
            fp = t_input.get("filePath", "")
            return f"{y}{icon} write:{r} `{fp}`"
        if tool_name == "edit":
            fp = t_input.get("filePath", "")
            return f"{y}{icon} edit:{r} `{fp}`"
        if tool_name == "glob":
            pat = t_input.get("pattern", "")
            pth = t_input.get("path", "")
            if pth:
                return f"{y}{icon} glob:{r} `{pat}` in `{pth}`"
            return f"{y}{icon} glob:{r} `{pat}`"
        if tool_name == "grep":
            pat = t_input.get("pattern", "")
            return f"{y}{icon} grep:{r} `{pat}`"

        lines = [f"{y}{icon} {tool_name}{r}"]
        if t_input:
            for k, v in t_input.items():
                s = str(v)
                if len(s) > 200:
                    s = s[:200] + "..."
                lines.append(f"  {k}: {s}")
        if t_output:
            out = str(t_output).strip()
            if out:
                if len(out) > 300:
                    out = out[:300] + "..."
                lines.append(f"  → {out}")
        return "\n".join(lines)

    return ""


# ======================================================================
# Pager
# ======================================================================


def _page_text(text: str) -> None:
    """Pipe text through $PAGER or less -R."""
    pager_cmd = os.environ.get("PAGER", "")
    try:
        if pager_cmd:
            subprocess.run(pager_cmd, input=text, text=True, shell=True)
        elif shutil.which("less"):
            subprocess.run(["less", "-R"], input=text, text=True)
        else:
            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()
    except OSError:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()
