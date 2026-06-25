"""Форматирование вывода: таблицы, JSON, Markdown."""

from __future__ import annotations

import json
import os
from typing import Any

from config import IGNORE_DIRS
from i18n import _


def print_json(data: Any) -> None:
    """Выводит данные в JSON-формате."""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def print_table_simple(
    headers: list[str],
    rows: list[list],
    sep: str = "  ",
) -> None:
    """Выводит таблицу с рамкой и колонками.

    Формат:
      ┌──────┬───────────┐
      │ ID   │ Title     │
      ├──────┼───────────┤
      │ abc  │ Session 1 │
      └──────┴───────────┘
    """
    if not rows:
        print(_("empty"))
        return

    ncols = len(headers)
    pad = 1  # padding inside each cell

    # compute column widths
    widths = []
    for ci in range(ncols):
        max_w = len(headers[ci])
        for row in rows:
            max_w = max(max_w, len(str(row[ci])))
        widths.append(min(max_w + pad * 2, 80))

    tl = "┌"  # top-left
    tm = "┬"  # top-middle
    tr = "┐"  # top-right
    ml = "├"  # middle-left
    mm = "┼"  # middle-middle
    mr = "┤"  # middle-right
    bl = "└"  # bottom-left
    bm = "┴"  # bottom-middle
    br = "┘"  # bottom-right
    ve = "│"  # vertical edge

    top = tl + tm.join("─" * w for w in widths) + tr
    sep = ml + mm.join("─" * w for w in widths) + mr
    bot = bl + bm.join("─" * w for w in widths) + br

    header_cells = [h.center(widths[ci])[: widths[ci]] for ci, h in enumerate(headers)]
    header_line = ve + ve.join(header_cells) + ve

    print()
    print(top)
    print(header_line)
    print(sep)
    for row in rows:
        cells = [str(row[ci]).ljust(widths[ci])[: widths[ci]] for ci in range(ncols)]
        print(ve + ve.join(cells) + ve)
    print(bot)
    print(_("fmt.rows_count", n=len(rows)))


def summarize_val(v: Any, max_len: int = 120) -> str:
    """Обрезает длинное значение."""
    s = str(v)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def format_part_to_md(part: dict, full: bool = False) -> str:
    """Преобразует часть сообщения в строку Markdown.

    Args:
      part: dict из get_messages()
      full: если True — не обрезать длинные output'ы и input'ы

    Returns:
      str — Markdown
    """
    t = part["type"]

    if t == "text":
        return part.get("text", "").strip()

    if t == "reasoning":
        text = part.get("text", "").strip()
        title = _("md.reasoning")
        return f"**💭 {title}:**\n{text}" if text else ""

    if t == "sound":
        return _("*🔊 {msg}*", msg=_("md.sound"))

    if t == "tool":
        tool_name = part.get("tool", "?")
        t_input = part.get("input", {})
        t_output = part.get("output", "")
        t_status = part.get("status", "")

        icon = {"completed": "✅", "error": "❌", "running": "⏳"}.get(t_status, "🔧")

        if tool_name in ("read", "write", "edit", "glob", "grep"):
            if tool_name == "read":
                fp = (
                    t_input.get("filePath", "")
                    if full
                    else summarize_val(t_input.get("filePath", ""))
                )
                return f"**{icon} read:** `{fp}`"
            elif tool_name == "write":
                fp = (
                    t_input.get("filePath", "")
                    if full
                    else summarize_val(t_input.get("filePath", ""), 80)
                )
                return f"**{icon} write:** `{fp}`"
            elif tool_name == "edit":
                fp = (
                    t_input.get("filePath", "")
                    if full
                    else summarize_val(t_input.get("filePath", ""), 80)
                )
                return f"**{icon} edit:** `{fp}`"
            elif tool_name == "glob":
                pat = (
                    t_input.get("pattern", "")
                    if full
                    else summarize_val(t_input.get("pattern", ""), 80)
                )
                pth = (
                    t_input.get("path", "") if full else summarize_val(t_input.get("path", ""), 60)
                )
                return f"**{icon} glob:** `{pat}` в `{pth}`"
            elif tool_name == "grep":
                pat = (
                    t_input.get("pattern", "")
                    if full
                    else summarize_val(t_input.get("pattern", ""), 80)
                )
                return f"**{icon} grep:** `{pat}`"

        lines = [f"**{icon} {tool_name}**"]

        if t_input:
            for k, v in t_input.items():
                if full:
                    s = str(v)
                    if len(s) > 500:
                        lines.append(f"  {k}:\n\n```\n{s}\n```")
                    else:
                        lines.append(f"  {k}: {s}")
                else:
                    lines.append(f"  {k}: {summarize_val(v, 200)}")

        if t_output:
            out = str(t_output).strip()
            if not out:
                pass
            elif full:
                if len(out) > 500:
                    lines.append(f"\n  → {_('md.result')}:\n\n```\n{out}\n```")
                else:
                    lines.append(f"  → {out}")
            else:
                if len(out) > 300:
                    lines.append(f"  → {summarize_val(out, 280)}")
                else:
                    lines.append(f"  → {out}")

        return "\n".join(lines)

    return ""


def collect_snapshot(project_dir: str) -> dict[str, Any]:
    """Собирает статистику по проекту для log.md.

    Returns:
      dict: {"agents_md": str, "file_count": int, "dir_count": int}
    """
    snapshot = {}

    agents_path = os.path.join(project_dir, "AGENTS.md")
    if os.path.isfile(agents_path):
        with open(agents_path, encoding="utf-8") as f:
            content = f.read()
        lines = content.count("\n") + 1
        sections = content.count("\n## ")
        snapshot["agents_md"] = _("md.log_lines", lines=lines, sections=sections)
    else:
        snapshot["agents_md"] = _("md.log_not_found")

    all_files = 0
    all_dirs = 0
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        if os.path.relpath(root, project_dir) == ".":
            all_files += len(files)
        else:
            all_dirs += 1
            all_files += len(files)

    snapshot["file_count"] = all_files
    snapshot["dir_count"] = all_dirs
    return snapshot


def update_log(
    output_dir: str,
    title: str,
    note: str | None,
    dialog_filename: str | None,
    snapshot: dict[str, Any],
    now_str: str,
) -> None:
    """Создаёт или дополняет log.md в директории проекта."""
    log_path = os.path.join(output_dir, "log.md")
    heading = f"{title}: {note}" if note else title
    dialog_link = os.path.basename(dialog_filename) if dialog_filename else "—"

    agents_line = _("md.log_agents", v=snapshot["agents_md"])
    files_line = _("md.log_files", files=snapshot["file_count"], dirs=snapshot["dir_count"])

    entry = f"""## [{now_str}] {heading}

- **{_("md.header.title")}:** [[{dialog_link}]]
- **Snapshot:**
  - {agents_line}
  - {files_line}

---

"""

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(_("log_updated", path=log_path))
