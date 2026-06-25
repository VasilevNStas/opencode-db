"""Конвертация Markdown в ANSI-форматированный текст для терминала.

Режимы:
  - rich (опционально): через `pip install opencode-db[rich]`
  - fallback: stdlib (re) + ANSI escape codes, zero external deps
"""

from __future__ import annotations

import re

HAS_RICH: bool = False
_RICH_CONSOLE = None
try:
    from rich.console import Console

    _RICH_CONSOLE = Console(force_terminal=True, color_system="truecolor")
    HAS_RICH = True
except ImportError:
    pass


def render(text: str, styles: dict[str, str] | None = None, *, plain: bool = False) -> str:
    """Конвертирует Markdown-текст в ANSI-форматированный вывод.

    При наличии rich использует его Markdown-рендерер (полное качество),
    иначе — встроенный конвертер (базовые конструкции).

    Args:
      text: исходный Markdown-текст
      styles: dict с ANSI-кодами (только для fallback)
      plain: True — вернуть как есть (без форматирования)

    Returns:
      str с ANSI-escape последовательностями
    """
    if not text:
        return ""

    if plain:
        return text

    if HAS_RICH and _RICH_CONSOLE is not None:
        return _render_rich(text)

    return _render_fallback(text, styles or {})


# ======================================================================
# RENDERER: rich
# ======================================================================


def _render_rich(text: str) -> str:
    from rich.markdown import Markdown

    with _RICH_CONSOLE.capture() as capture:
        _RICH_CONSOLE.print(Markdown(text))
    result = capture.get()
    return result.rstrip("\n")


# ======================================================================
# RENDERER: fallback (stdlib)
# ======================================================================


def _render_fallback(text: str, sty: dict[str, str]) -> str:
    r = sty.get("R", "")
    bold = sty.get("B", "")
    dim = sty.get("D", "")
    cyan = sty.get("C", "")
    yellow = sty.get("Y", "")
    gray = sty.get("M", "")
    green = sty.get("G", "")

    result = text

    # fenced code blocks
    result = re.sub(
        r"```(\w*)\n(.*?)```",
        lambda m: _fb_code_block(m.group(1), m.group(2), sty),
        result,
        flags=re.DOTALL,
    )

    # inline code
    result = re.sub(r"`([^`]+)`", rf"{yellow}\1{r}", result)

    # bold **...**
    result = re.sub(r"\*\*(.+?)\*\*", rf"{bold}\1{r}", result)

    # italic *...*
    result = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", rf"{dim}\1{r}", result)

    # headings
    result = re.sub(
        r"^#{1,3} (.+)$",
        rf"{bold}{cyan}\1{r}",
        result,
        flags=re.MULTILINE,
    )

    # blockquotes
    result = re.sub(
        r"^> (.+)$",
        lambda m: _fb_blockquote(m.group(1), sty),
        result,
        flags=re.MULTILINE,
    )

    # horizontal rules
    result = re.sub(
        r"^---+$",
        f"{gray}{'─' * 60}{r}",
        result,
        flags=re.MULTILINE,
    )

    # unordered lists
    result = re.sub(r"^(\s*)[-*] ", r"\1• ", result, flags=re.MULTILINE)

    # ordered lists
    result = re.sub(
        r"^(\s*)(\d+)\. ",
        lambda m: f"{m.group(1)}{green}{m.group(2)}.{r} ",
        result,
        flags=re.MULTILINE,
    )

    # links [text](url)
    result = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f"{m.group(1)} ({gray}{m.group(2)}{r})",
        result,
    )

    # tables: convert to box-drawing
    result = re.sub(
        r"^(\|.+)$(?:\n\|.+)+\n\|.+(?:\n\|.+)*",
        lambda m: _fb_table(m.group(0), sty),
        result,
        flags=re.MULTILINE,
    )

    return result


def _fb_code_block(lang: str, body: str, sty: dict[str, str]) -> str:
    r = sty.get("R", "")
    gray = sty.get("M", "")
    yellow = sty.get("Y", "")
    lang_tag = f" {lang}" if lang else ""
    header = f"{gray}┌─{lang_tag}{r}"
    footer = f"{gray}└──{r}"
    lines = body.strip().split("\n")
    indented = "\n".join(f"{yellow}{line}{r}" for line in lines)
    return f"{header}\n{indented}\n{footer}"


def _fb_blockquote(line: str, sty: dict[str, str]) -> str:
    gray = sty.get("M", "")
    r = sty.get("R", "")
    return f"{gray}│ {line}{r}"


def _fb_table(text: str, sty: dict[str, str]) -> str:
    """Converts a Markdown table to box-drawing format."""
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    if len(lines) < 3:
        return text

    # skip separator row (|--|--|)
    data_rows = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|[-| ]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        data_rows.append(cells)

    if len(data_rows) < 2:
        return text

    ncols = max(len(r) for r in data_rows)
    pad = 1

    widths: list[int] = []
    for ci in range(ncols):
        max_w = max(len(r[ci]) if ci < len(r) else 0 for r in data_rows)
        widths.append(max_w + pad * 2)

    tl, tm, tr = "┌", "┬", "┐"
    ml, mm, mr = "├", "┼", "┤"
    bl, bm, br = "└", "┴", "┘"
    ve = "│"
    r = sty.get("R", "")
    gray = sty.get("M", "")

    top = tl + tm.join("─" * w for w in widths) + tr
    sep = ml + mm.join("─" * w for w in widths) + mr
    bot = bl + bm.join("─" * w for w in widths) + br

    header_cells = [
        (data_rows[0][ci] if ci < len(data_rows[0]) else "").center(widths[ci])[: widths[ci]]
        for ci in range(ncols)
    ]
    header_line = f"{gray}{ve}{ve.join(header_cells)}{ve}{r}"

    result = [f"{gray}{top}{r}", header_line, f"{gray}{sep}{r}"]

    for row in data_rows[1:]:
        cells = [
            (row[ci] if ci < len(row) else "").ljust(widths[ci])[: widths[ci]]
            for ci in range(ncols)
        ]
        result.append(f"{ve}{ve.join(cells)}{ve}")

    result.append(f"{gray}{bot}{r}")
    return "\n".join(result)
