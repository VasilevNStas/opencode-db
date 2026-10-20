# opencode-db

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/VasilevNStas/opencode-db/blob/master/LICENSE)

**CLI for OpenCode's local database.** OpenCode saves every agent session, conversation, token usage, and cost in a local SQLite file. This tool lets you inspect, export, analyze, and clean up that data.

```bash
pip install opencode-db

# recommended if your system python3 is older than 3.12:
uv tool install opencode-db
```

## Quick start

```bash
opencode-db --version    # installed version
opencode-db list         # recent sessions
opencode-db directories  # launch directories, including missing ones
opencode-db view         # interactive session viewer (colored, scrollable)
opencode-db stats        # database summary
opencode-db schema       # detect v1/v2 schema
opencode-db costs --total  # total token costs
opencode-db export       # export dialog to .md (interactive)
opencode-db help         # full reference
```

## Features

- **`view`** — просмотр сессии в терминале с ANSI-цветами, Markdown-рендерингом и прокруткой через `less`
- **`list`** / **`info`** / **`search`** / **`tree`** — навигация и поиск по сессиям
- **`directories`** (`dirs`) — все директории запусков, включая отсутствующие; `list --directory` добавляет путь к сессии
- **`export`** — экспорт диалога в Markdown (с поддержкой Obsidian)
- **`delete`** / **`prune`** — удаление и массовая очистка с фильтрами
- **`costs`** / **`stats`** — аналитика токенов и расходов
- **`schema`** — определяет v1/v2-схему OpenCode, миграции и доступные операции
- **`--db-path`** / **`OPENCODE_DB`** — кастомный путь к БД

## Optional extras

```bash
pip install opencode-db[rich]   # enhanced Markdown rendering (recommended)
pip install opencode-db         # zero external dependencies
```

## Requirements

- Python 3.12+ — the CLI checks the interpreter at startup and exits with a clear message instead of an `ImportError` on older versions
- [OpenCode](https://opencode.ai) (must have been run at least once)
- macOS / Linux

**Directory support:** `global` is a synthetic project for non-Git directories; `directories` shows the real `session.directory` and marks it as `Global (no project root)`. Missing paths are detected with `os.path.isdir()` at command runtime and can be filtered with `--missing`.

**Schema support:** OpenCode 1.19.x (v1) — read and write; OpenCode 2.x preview (v2) — read-only. Run `opencode-db schema` to check the detected schema. On v2, `delete`, `prune`, and `vacuum` are refused until write support is implemented.
