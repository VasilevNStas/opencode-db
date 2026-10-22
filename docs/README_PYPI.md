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
opencode-db health       # SQLite storage health (read-only)
opencode-db backup       # managed, verified snapshot
opencode-db backups list # inspect snapshots
opencode-db schema       # detect v1/v2 schema
opencode-db costs --total  # total token costs
opencode-db export       # export dialog to Markdown (interactive)
opencode-db export --format json  # lossless JSON archive
opencode-db export --last 5  # bulk bundle: roots + subagents
opencode-db digest <id>  # compaction summaries
opencode-db help         # full reference
```

## Features

- **`view`** — terminal session viewer with ANSI colors, Markdown rendering, and `less` scrolling
- **`list`** / **`info`** / **`search`** / **`tree`** — browse and search sessions
- **`directories`** (`dirs`) — every launch directory, including missing ones; `list --directory` adds the path to each session
- **`export`** — Markdown or lossless JSON; preserves `patch`, `file`, `compaction`, `step-*`, and unknown part types; unique `opencode-<date>-<short_id>` filenames
- **`export --last/--since/--project/--all`** — bulk bundles with `index.md`, `metadata.json`, root transcripts, and `subagents/`; `--with-subagents`/`--no-subagents` controls cascade
- **`digest`** — compaction summaries for v1 and v2 sessions, with `--last N` and `--json`
- **`delete`** / **`prune`** — single and bulk cleanup; `prune --missing-directories` is preview-first and guarded
- **`costs`** / **`stats`** — token and cost analytics
- **`health`** — read-only freelist, WAL, `auto_vacuum`, reclaimable-space, and backup-freshness report
- **`backup`** / **`backups`** — managed snapshots with manifest, sha256, gzip, verify, and retention; `--from-backup` opens a snapshot read-only
- **`vacuum`** — guarded optimization: lock check, verified backup, integrity check, and WAL preservation
- **`schema`** — detects the OpenCode v1/v2 schema, migrations, and capabilities
- **`--db-path`** / **`OPENCODE_DB`** — custom database path
- **`--from-backup`** — read-only access to a managed snapshot (`.db` or `.db.gz`)

## Возможности

- **`view`** — просмотр сессии в терминале с ANSI-цветами, Markdown-рендерингом и прокруткой через `less`
- **`list`** / **`info`** / **`search`** / **`tree`** — навигация и поиск по сессиям
- **`directories`** (`dirs`) — все директории запусков, включая отсутствующие; `list --directory` добавляет путь к сессии
- **`export`** — Markdown или lossless JSON; сохраняет `patch`, `file`, `compaction`, `step-*` и неизвестные типы частей; уникальные имена `opencode-<date>-<short_id>`
- **`export --last/--since/--project/--all`** — массовые bundles с `index.md`, `metadata.json`, transcript'ами root и `subagents/`; `--with-subagents`/`--no-subagents` управляет cascade
- **`digest`** — compaction-сводки для v1 и v2, с `--last N` и `--json`
- **`delete`** / **`prune`** — удаление и массовая очистка; `prune --missing-directories` работает через preview и guard'ы
- **`costs`** / **`stats`** — аналитика токенов и расходов
- **`health`** — read-only отчёт о freelist, WAL, `auto_vacuum`, reclaimable space и свежести backup
- **`backup`** / **`backups`** — управляемые снимки с manifest, sha256, gzip, verify и retention; `--from-backup` открывает снимок read-only
- **`vacuum`** — безопасная оптимизация: lock check, проверенный backup, integrity check и сохранение WAL
- **`schema`** — определяет v1/v2-схему OpenCode, миграции и доступные операции
- **`--db-path`** / **`OPENCODE_DB`** — кастомный путь к БД
- **`--from-backup`** — read-only работа с управляемым снимком (`.db` или `.db.gz`)

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

**Schema support:** OpenCode 1.19.x (v1) — read and write; OpenCode 2.x preview (v2) — read-only. Run `opencode-db schema` to check the detected schema. On v2, `health` and the read-only commands work; `delete`, `prune`, and `vacuum` are refused until write support is implemented.
