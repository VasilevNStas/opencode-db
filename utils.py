"""Вспомогательные утилиты.

Функции общего назначения:
  - parse_ts() / format_ts() — работа с миллисекундными таймштампами
  - summarize_val() — обрезка длинных строк
  - parse_time_spec() — парсинг '30d', '6m', '1y'
  - confirm() — запрос подтверждения
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Literal, LiteralString

from i18n import _


def parse_ts(ts_ms) -> datetime:
    """Конвертирует Unix timestamp в миллисекундах в datetime (UTC)."""
    return datetime.fromtimestamp(ts_ms / 1000, tz=UTC)


def format_ts(ts_ms, fmt="%Y-%m-%d %H:%M:%S") -> str:
    """Форматирует timestamp в строку."""
    return parse_ts(ts_ms).strftime(fmt)


def format_ts_short(ts_ms) -> str:
    """Форматирует timestamp в компактный формат для имён файлов."""
    return format_ts(ts_ms, "%Y-%m-%d_%H.%M.%S")


def summarize_val(v, max_len=120) -> str:
    """Обрезает длинное значение для компактного отображения."""
    s = str(v)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def parse_time_spec(spec) -> None | datetime:
    """Парсит спецификацию времени ('30d', '6m', '1y') в timedelta."""
    if not spec or not isinstance(spec, str):
        return None

    spec = spec.strip().lower()
    match = re.match(r"^(\d+)\s*(d|day|days|m|mo|mon|month|months|y|year|years)$", spec)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    now = datetime.now(UTC)

    if unit == "d" or unit.startswith("day"):
        delta = timedelta(days=value)
    elif unit == "m" or unit.startswith("mon"):
        delta = timedelta(days=value * 30.44)
    elif unit == "y" or unit.startswith("year"):
        delta = timedelta(days=value * 365.25)
    else:
        return None

    return now - delta


def confirm(prompt=None, default=False) -> bool:
    """Запрашивает подтверждение y/N.

    Args:
      prompt: str, текст приглашения (если None — используется общий)
      default: bool, что возвращать при пустом вводе

    Returns:
      bool
    """
    if prompt is None:
        prompt = _("yes_no_prompt")
    suffix = _("yes_no_true") if default else _("yes_no_false")
    while True:
        try:
            answer = input(prompt + suffix).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if not answer:
            return default
        if answer in ("y", "yes", _("cli.yn_yes")):
            return True
        if answer in ("n", "no", "нет"):
            return False


def format_cost(cost_value) -> str:
    """Форматирует стоимость в долларах."""
    if cost_value is None:
        return "—"
    if cost_value < 0.01:
        return f"${cost_value:.4f}"
    if cost_value < 1:
        return f"${cost_value:.3f}"
    return f"${cost_value:.2f}"


def format_tokens(count) -> LiteralString | Literal["—"]:
    """Форматирует количество токенов с разделителями."""
    if count is None:
        return "—"
    s = str(int(count))
    result = []
    for i, ch in enumerate(reversed(s)):
        if i > 0 and i % 3 == 0:
            result.append("\u202f")
        result.append(ch)
    return "".join(reversed(result))
