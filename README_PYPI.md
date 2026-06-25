# opencode-db

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**CLI for OpenCode's local database.** OpenCode saves every agent session, conversation, token usage, and cost in a local SQLite file. This tool lets you inspect, export, analyze, and clean up that data.

```bash
pip install opencode-db
```

## Quick start

```bash
opencode-db list         # recent sessions
opencode-db view         # interactive session viewer (colored, scrollable)
opencode-db stats        # database summary
opencode-db costs --total  # total token costs
opencode-db export       # export dialog to .md (interactive)
opencode-db help         # full reference
```

## Features

- **`view`** — просмотр сессии в терминале с ANSI-цветами, Markdown-рендерингом и прокруткой через `less`
- **`list`** / **`info`** / **`search`** / **`tree`** — навигация и поиск по сессиям
- **`export`** — экспорт диалога в Markdown (с поддержкой Obsidian)
- **`delete`** / **`prune`** — удаление и массовая очистка с фильтрами
- **`costs`** / **`stats`** — аналитика токенов и расходов
- **`--db-path`** / **`OPENCODE_DB`** — кастомный путь к БД

## Optional extras

```bash
pip install opencode-db[rich]   # enhanced Markdown rendering (recommended)
pip install opencode-db         # zero external dependencies
```

## Requirements

- Python 3.12+
- [OpenCode](https://opencode.ai) (must have been run at least once)
- macOS / Linux
