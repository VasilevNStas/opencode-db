"""Конфигурация и константы opencode-db.

Здесь централизованы пути и общие настройки.
Стоимость сессий берётся напрямую из БД (session.cost), а не рассчитывается.
"""

import os

# --- Пути ---
# База данных opencode. Стандартное расположение для Linux/macOS.
DEFAULT_DB = os.path.expanduser("~/.local/share/opencode/opencode.db")


def get_db_path() -> str:
    """Текущий путь к БД с учётом OPENCODE_DB/--db-path."""
    return os.environ.get("OPENCODE_DB") or DEFAULT_DB


def resolve_db_path() -> tuple[str, bool]:
    """Вернуть (path, used_preview_fallback).

    Явный путь всегда имеет приоритет. Если стандартная БД отсутствует,
    пробуем preview-базу OpenCode 2.x — opencode-next.db.
    """
    explicit = os.environ.get("OPENCODE_DB")
    if explicit:
        return explicit, False
    if os.path.isfile(DEFAULT_DB):
        return DEFAULT_DB, False
    preview = os.path.join(os.path.dirname(DEFAULT_DB), "opencode-next.db")
    if os.path.isfile(preview):
        return preview, True
    return DEFAULT_DB, False


# Backwards-compatible constant for callers that only display the default path.
OPENCODE_DB = get_db_path()

# Директории, игнорируемые при сборе snapshot'а проекта
IGNORE_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".opencode"}
