# opencode-db

[![test](https://github.com/VasilevNStas/opencode-db/actions/workflows/test.yml/badge.svg)](https://github.com/VasilevNStas/opencode-db/actions/workflows/test.yml)
[![release](https://github.com/VasilevNStas/opencode-db/actions/workflows/release.yml/badge.svg)](https://github.com/VasilevNStas/opencode-db/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/opencode-db)](https://pypi.org/project/opencode-db/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**OpenCode stores everything in a local SQLite database.** Every agent session, conversation, token usage, and cost is saved automatically. `opencode-db` is the CLI tool to work with that database — list sessions, export conversations to Markdown, track token costs, prune old data, and more.

```
opencode-db help        # full reference with examples
opencode-db list        # list recent sessions
opencode-db stats       # database summary
opencode-db export      # save a dialog to .md (interactive)
opencode-db costs --total  # total token costs
```

---

## Installation

### Requirements

- Python 3.12+
- OpenCode (must have been run at least once — the database is created automatically)
- macOS / Linux

### One-command install (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/VasilevNStas/opencode-db/master/install.sh | sh
```

Downloads everything to `~/.local/share/opencode-db/` and creates `~/.local/bin/opencode-db`.

### pip / pipx install

```bash
pipx install opencode-db
# or
pip install opencode-db
```

[Zero external dependencies](https://treyhunner.com/2015/12/python-imports-and-path-manipulation/) — pure Python standard library only.

### Manual install

1. Download the latest release from GitHub or clone the repo:

```bash
git clone https://github.com/VasilevNStas/opencode-db.git ~/.local/share/opencode-db
```

2. Create a launcher at `~/.local/bin/opencode-db`:

```bash
cat > ~/.local/bin/opencode-db << 'SCRIPT'
#!/usr/bin/env python3
import sys, os
PKG_DIR = os.path.expanduser("~/.local/share/opencode-db")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
import cli
sys.exit(cli.main())
SCRIPT
chmod +x ~/.local/bin/opencode-db
```

3. Make sure `~/.local/bin` is in your `$PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

4. Verify:

```bash
opencode-db --help
```

---

## Quick start

```bash
# List recent sessions
opencode-db list

# Detailed session info (accepts partial ID)
opencode-db info ses_1c9d

# Save a dialog in Markdown
opencode-db export ses_1c9d --force

# Total token costs
opencode-db costs --total

# Database statistics
opencode-db stats
```

---

## Commands

### `list` — list sessions

Displays a table of recent sessions: ID, title, project, model, last activity, message count, and cost.

```bash
opencode-db list                         # last 25 sessions
opencode-db list --limit 10              # last 10
opencode-db list --all                   # every session
opencode-db list --sort cost             # sort by cost (descending)
opencode-db list --project proj_xxx      # filter by project
opencode-db list --agent build           # filter by agent type
opencode-db list --model deepseek        # filter by model name
opencode-db list --json                  # JSON output
```

| Flag | Description | Default |
|---|---|---|
| `--limit N` | Number of sessions to show | 25 |
| `--offset N` | How many to skip | 0 |
| `--project ID` | Filter by project | — |
| `--agent NAME` | Filter by agent type | — |
| `--model NAME` | Filter by model name | — |
| `--sort {date,cost,tokens,messages}` | Sort order | date |
| `--json` | Output as JSON | — |
| `--all` | Show all (overrides --limit) | — |

---

### `info` — detailed session information

Shows metadata, message and token statistics, cost, code changes, child sessions, and todo items.

```bash
opencode-db info ses_1c9d9fa58ffe        # by full ID
opencode-db info ses_1c9d                # by ID prefix
opencode-db info ses_1c9d --json         # JSON output
```

Example output:

```
============================================================
  Анализ export-dialog скрипта
============================================================
  ID:        ses_1c9d9fa58ffeiqsrHGVg8MPZes
  Проект:    global (global)
  Модель:    deepseek-reasoner
  Агент:     plan
  Версия:    1.15.1
  Создана:   2026-05-17 13:35:22
  Активна:   2026-05-17 14:13:23
  Длит-сть:  38 мин

  ────────────────────────────────────────────────────────
  Сообщений: 43
  Частей:    224
  ────────────────────────────────────────────────────────
  Токены ввода:     82 026
  Токены вывода:    36 837
  Токены reasoning: 17 211
  Кэш (чтение):     2 077 312
  Всего токенов:    118 863
  Стоимость:        $0.085
```

---

### `export` — export dialog to Markdown

Saves a conversation to `opencode-YYYY-MM-DD_HH.MM.SS.md` in the current directory.

**Three ways to pick a session:**

| Mode | Example | Description |
|---|---|---|
| By ID | `export ses_1c9d` | Explicit session ID (full or prefix) |
| Latest | `export --latest` | Most recent session |
| Interactive | `export` (no args) | Pick from a numbered list |

```bash
opencode-db export ses_1c9d              # export by ID
opencode-db export --latest              # export the most recent session
opencode-db export --latest --force      # overwrite if the file exists
opencode-db export --latest --full       # full output, no truncation
opencode-db export --latest -n "bug fix" # add a note to log.md
opencode-db export                       # interactive picker
opencode-db export --full                # full output (don't truncate tool outputs)
opencode-db export -o ~/backup           # save to a different directory
```

The file format is Markdown with a metadata header (date, model, ID) followed by messages in chronological order with speaker labels (user/assistant), model reasoning blocks, and tool calls with their results.

If the project directory contains `.obsidian`, a `log.md` file is automatically created or appended with a project snapshot (AGENTS.md summary, file and directory counts).

| Flag | Description | Default |
|---|---|---|
| `session_id` | Session ID (optional — interactive mode if omitted) | — |
| `--latest`, `-l` | Export the most recent session | — |
| `--full`, `-F` | Full output (do not truncate long tool outputs) | — |
| `--force`, `-f` | Overwrite the file if it exists | — |
| `--note`, `-n` | Description for log.md | — |
| `--output`, `-o` | Output directory | `os.getcwd()` |

---

### `delete` — delete sessions

Removes sessions and all related data (messages, parts, todos). Supports single deletion by ID or bulk deletion with filters.

```bash
opencode-db delete ses_1c9d                              # single session with confirmation
opencode-db delete ses_1c9d --force                      # single session, no confirmation
opencode-db delete ses_1c9d --dry-run                    # preview what would be deleted
opencode-db delete --older-than 90d                      # sessions older than 90 days
opencode-db delete --older-than 6m --dry-run             # preview sessions older than 6 months
opencode-db delete --keep-last 30                        # keep 30 most recent, delete the rest
opencode-db delete --before 2026-05-20                   # sessions before a specific date
opencode-db delete --after 2026-01-01                    # sessions after a specific date
opencode-db delete --project proj_xxx                    # sessions in a specific project
opencode-db delete --older-than 90d --keep-last 20       # combined filters
opencode-db delete --interactive                         # choose from a list interactively
```

| Flag | Description |
|---|---|
| `session_id` | Session ID (optional with `--interactive`) |
| `--older-than` | Delete sessions older than (e.g. `30d`, `6m`, `1y`) |
| `--before` | Delete sessions before date (`YYYY-MM-DD`) |
| `--after` | Delete sessions after date (`YYYY-MM-DD`) |
| `--keep-last` | Keep N most recent, delete the rest |
| `--project` | Limit to a specific project |
| `--dry-run` | Only show what would be deleted |
| `--force`, `-f` | Skip confirmation prompt |
| `--interactive` | Pick sessions from a list |

---

### `costs` — token cost analysis

Breaks down tokens and cost by session, project, or entire database.

```bash
opencode-db costs ses_1c9d               # single session
opencode-db costs --total                # all sessions combined
opencode-db costs --project proj_xxx     # filter by project
opencode-db costs                        # top sessions by cost
opencode-db costs --limit 10             # top 10
opencode-db costs ses_1c9d --json        # JSON output
```

Costs are taken directly from the database (`session.cost`), which stores the actual cost calculated by the model provider. No manual pricing table is needed.

| Flag | Description | Default |
|---|---|---|
| `session_id` | Session ID (optional) | — |
| `--project` | Filter by project | — |
| `--total` | Total across all sessions | — |
| `--limit N` | Max rows in list mode | 30 |
| `--json` | JSON output | — |

---

### `prune` — alias for `delete` (bulk cleanup)

Alias for `delete` with the same flags: `--older-than`, `--keep-last`, `--project`, `--dry-run`, `--force`.

```bash
opencode-db prune --older-than 90d         # same as opencode-db delete --older-than 90d
opencode-db prune --keep-last 20           # same as opencode-db delete --keep-last 20
```

Time spec formats: `30d` (days), `6m` (months), `1y` (years).

---

### `search` — search across messages

Searches message text and tool call parameters (case-insensitive).

```bash
opencode-db search "deployment"              # search all sessions
opencode-db search "deployment" --limit 5    # first 5 results
opencode-db search "deployment" --session ses_1c9d  # single session
opencode-db search "deployment" --json       # JSON output
```

| Flag | Description | Default |
|---|---|---|
| `query` | Search text | required |
| `--session ID` | Limit to a session | — |
| `--limit N` | Max results | 30 |
| `--json` | JSON output | — |

---

### `tree` — session tree (branching)

Shows the session hierarchy via the `parent_id` field. Useful for understanding which sessions spawned from which.

```bash
opencode-db tree                          # all root sessions with their children
opencode-db tree ses_1c9d                 # branch from a specific session
opencode-db tree --project proj_xxx       # filter by project
opencode-db tree --depth 3                # max depth of 3 levels
```

Example output:

```
  🌳 Все корневые сессии (ветвление)
  ───────────────────────────────────────────────────────
  ses_1ed78233fffe  2026-05-10  Starting a project
    └─ ses_1ed5d1a05ffe  2026-05-10  Create README and meta files (@general subagent)
    └─ ses_1ed5c6c29ffe  2026-05-10  Create Module 01 Fundamentals (@general subagent)
    └─ ses_1ed5b7adbffe  2026-05-10  Create Module 02 Anatomy (@general subagent)
    ...
```

| Flag | Description | Default |
|---|---|---|
| `session_id` | Start from this session (optional) | — |
| `--depth N` | Maximum depth | 5 |
| `--project ID` | Filter by project | — |

---

### `projects` — list projects

Shows all projects in the database with session counts, tokens, and costs.

```bash
opencode-db projects                      # project table
opencode-db projects --json               # JSON output
```

| Flag | Description |
|---|---|
| `--json` | JSON output |

---

### `stats` — database statistics

Summary of the entire database: session, message, part, project, and todo counts; total tokens and cost; first and last session dates; top models and agents.

```bash
opencode-db stats                         # summary
opencode-db stats --json                  # JSON output
```

| Flag | Description |
|---|---|
| `--json` | JSON output |

---

### `todos` — view tasks from sessions

Displays todo items created during OpenCode sessions.

```bash
opencode-db todos                         # all tasks
opencode-db todos ses_1c9d                # tasks for a specific session
opencode-db todos --status pending        # pending only
opencode-db todos --json                  # JSON output
```

| Flag | Description | Default |
|---|---|---|
| `session_id` | Session ID (optional) | — |
| `--status {pending,completed,cancelled}` | Filter by status | — |
| `--limit N` | Max entries | 30 |
| `--json` | JSON output | — |

---

### `vacuum` — database optimization

Runs `VACUUM`, `REINDEX`, and `ANALYZE` to reclaim disk space and optimize query performance. Especially useful after bulk deletions (prune, delete).

```bash
opencode-db vacuum                        # with confirmation
opencode-db vacuum --force                # without confirmation
```

| Flag | Description |
|---|---|
| `--force`, `-f` | Skip confirmation |

---

### `help` — detailed reference

Displays all commands with descriptions, flags, and usage examples. Works both in the terminal and inside OpenCode's TUI via `/bash opencode-db help`.

```bash
opencode-db help                          # full reference for all commands
opencode-db help export                   # reference for a specific command
opencode-db help --json                   # JSON reference
```

Example output:

```
  ╔══════════════════════════════════════════════════════════╗
  ║                 opencode-db — справка                    ║
  ╚══════════════════════════════════════════════════════════╝

  Использование: opencode-db <команда> [флаги]

  list          Список сессий
                  opencode-db list                               # Сессии за последнее время
                  opencode-db list --sort cost                     # Сортировка по стоимости
                  opencode-db list --json                          # Вывод в JSON

  export        Экспорт диалога в Markdown
                  opencode-db export <session_id>                  # Экспорт по ID
                  opencode-db export --latest                      # Самая свежая сессия
                  opencode-db export                               # Интерактивный выбор
                  opencode-db export --full                        # Полный вывод без обрезания

  costs         Анализ расходов на токены
                  opencode-db costs <session_id>                   # Детально по сессии
                  opencode-db costs --total                        # Сумма по всей БД

  ...
```

---

## Command reference summary

| Command | Description | Key flags |
|---|---|---|
| `list` | List sessions with filtering | `--limit`, `--sort`, `--project`, `--json`, `--all` |
| `info` | Detailed session info | `--json` |
| `export` | Export dialog to Markdown | `--latest`, `--full`, `--force`, `--note`, `--output` |
| `delete` | Delete a session | `--dry-run`, `--force` |
| `costs` | Token cost analysis | `--total`, `--project`, `--json` |
| `prune` | Bulk session cleanup | `--older-than`, `--keep-last`, `--dry-run` |
| `search` | Search message text | `--session`, `--json` |
| `tree` | Session branching tree | `--depth`, `--project` |
| `projects` | Project overview | `--json` |
| `stats` | Database statistics | `--json` |
| `todos` | View session tasks | `--status`, `--json` |
| `vacuum` | Database optimization | `--force` |
| `help` | Detailed reference | `<command>`, `--json` |

---

## Project architecture

```
~/.local/bin/opencode-db                  ← entry point (in $PATH)
│
~/.local/share/opencode-db/               ← all source code
│
├── __init__.py                           ← executable entry point
├── __main__.py                           ← python -m opencode_db
├── cli.py                                ← argparse + command dispatcher
│
├── config.py                             ← constants and paths
├── db.py                                 ← SQLite queries
├── utils.py                              ← date/token formatting, validation
├── formatters.py                         ← tables, JSON, Markdown, snapshots
├── i18n.py                               ← localization (EN/RU, 238 keys)
│
├── commands/
│   └── __init__.py                       ← command registry
│
├── cmd_list.py                           ← opencode-db list
├── cmd_info.py                           ← opencode-db info
├── cmd_export.py                         ← opencode-db export
├── cmd_delete.py                         ← opencode-db delete
├── cmd_costs.py                          ← opencode-db costs
├── cmd_prune.py                          ← opencode-db prune
├── cmd_search.py                         ← opencode-db search
├── cmd_tree.py                           ← opencode-db tree
├── cmd_projects.py                       ← opencode-db projects
├── cmd_stats.py                          ← opencode-db stats
├── cmd_todos.py                          ← opencode-db todos
├── cmd_vacuum.py                         ← opencode-db vacuum
└── cmd_help.py                           ← opencode-db help

README.md                                 ← this file (English)
README.ru.md                              ← documentation in Russian
opencode-db-commands.json                 ← OpenCode TUI custom commands config
```

### How it works

1. The launcher script at `~/.local/bin/opencode-db` (a shebang Python script) adds `~/.local/share/opencode-db/` to `sys.path` and calls `cli.main()`.
2. `cli.py` builds an `argparse` parser with subparsers from every command module and dispatches the call.
3. Each command is a separate `cmd_*.py` module exporting two functions: `register(subparsers)` and `run(args, db)`.
4. `db.py` opens a connection to OpenCode's SQLite database (`~/.local/share/opencode/opencode.db`).
5. Destructive operations (`delete`, `prune`) always require confirmation (or `--force`).

### Database schema (key tables)

```
session        — sessions: id, title, model (JSON), agent, cost, tokens_*, parent_id, summary_*
message        — messages: id, session_id, time_created, data (JSON: role, agent)
part           — message parts: id, message_id, session_id, data (JSON: type, text, state)
todo           — tasks: session_id, content, status, priority
project        — projects: id, worktree, name
```

---

## Using inside OpenCode TUI

`opencode-db` can be used directly from OpenCode's terminal interface in two ways.

### Direct execution (no AI, no tokens)

Use the built-in `/bash` tool in the OpenCode chat:

```
/bash opencode-db list
/bash opencode-db info ses_1c9d
/bash opencode-db costs --total
/bash opencode-db export --latest --force
```

This runs the command directly and shows the output — **no tokens are consumed**.

### Custom `/db` command (uses AI, consumes tokens)

Add the commands from `opencode-db-commands.json` to your project's `opencode.json`:

```json
{
  "command": {
    "db": {
      "template": "!`opencode-db {{input}} --json`\n\nPresent the data clearly.",
      "description": "OpenCode database: list, info, stats, costs, search...",
      "agent": "explore",
      "model": "deepseek/deepseek-chat"
    }
  }
}
```

Then in the TUI:

```
/db list --limit 5        → shows recent sessions
/db info ses_1c9d         → session details
/db costs --total         → total costs
/db search "bug"          → search messages
```

> ⚠️ **Warning:** the `/db` command sends the command output through the AI model. This consumes tokens (typically 500–5000 input tokens depending on the amount of data). Use `/bash opencode-db ...` when you only need to see the data without AI processing.

A ready-to-use config file is provided at:
```
~/.local/share/opencode-db/opencode-db-commands.json
```

---

## Safety

| Principle | Implementation |
|---|---|
| Confirmation required | `delete` and `prune` always prompt for confirmation |
| Dry-run mode | `--dry-run` shows results without making changes |
| Read-only by default | `list`, `info`, `costs`, `search`, `tree`, `projects`, `stats`, `todos` are read-only |
| Partial ID resolution | Ambiguous prefixes are rejected with an error message |
| No external dependencies | Pure Python standard library — zero runtime deps |

---

## Language

The CLI supports both Russian and English output.

- **Default**: Russian (matching OpenCode's interface language)
- **English**: use `--lang en` flag, e.g. `opencode-db --lang en list`

```bash
opencode-db list                  # Russian (default)
opencode-db --lang en list        # English
opencode-db --lang en help        # English help text
opencode-db --lang en stats       # English statistics
```

The `--lang` flag applies to any command. All 238 UI strings are translated. Data content (session titles, project names, etc.) remains in its original language.

The language can also be set via environment variable `OPENCODE_DB_LANG=en`.

---

## Dependencies

- **Python 3.12+** — standard library only
- **SQLite** — built-in `sqlite3` module
- **OpenCode** — must be installed and run at least once (creates the database)

No `npm`, `brew`, or any other package manager required.

---

## Troubleshooting

### "База OpenCode не найдена" (database not found)

```
❌ База OpenCode не найдена: ~/.local/share/opencode/opencode.db
```

OpenCode has not been started yet, or the database is stored in a non-standard location. Make sure:
- OpenCode is installed and has been launched at least once
- The file `~/.local/share/opencode/opencode.db` exists

### "Найдено несколько сессий с префиксом" (multiple sessions match prefix)

```
❌ Найдено несколько сессий с префиксом ses_1c9d:
    ses_1c9d9fa58ffeiqsrHGVg8MPZes
    ses_1c9d8fa58ffeabc123def456xyz
```

Use a longer prefix or the full session ID (use `list --json` to find it).

### VACUUM fails

If the database is being used by another process (e.g., OpenCode is running), VACUUM may fail. Close OpenCode and try again.

---

## Development

### Adding a new command

1. Create `cmd_xxx.py`:

```python
def register(subparsers):
    p = subparsers.add_parser("xxx", help="Description")
    p.add_argument("--flag", type=str)

def run(args, db):
    # your logic here
    return 0
```

2. Register it in `commands/__init__.py`:

```python
import cmd_xxx
COMMANDS["xxx"] = cmd_xxx
```

The command will appear in `--help` automatically.

### Running without installation

```bash
python3 ~/.local/share/opencode-db list
```

Or as a module:

```bash
python3 -m opencode_db list
```

---

## Лицензия / License

MIT — подробнее в файле [LICENSE](LICENSE)

© 2026 Vasilev Stas — код можно свободно использовать, изменять и распространять
