"""Конфигурация и константы opencode-db.

Здесь централизованы пути и общие настройки.
Стоимость сессий берётся напрямую из БД (session.cost), а не рассчитывается.
"""

import os

# --- Пути ---
# База данных opencode. Стандартное расположение для Linux/macOS.
OPENCODE_DB = os.environ.get("OPENCODE_DB") or os.path.expanduser(
    "~/.local/share/opencode/opencode.db"
)

# Директории, игнорируемые при сборе snapshot'а проекта
IGNORE_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".opencode"}
