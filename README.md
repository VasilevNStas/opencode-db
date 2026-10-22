# opencode-db

[![test](https://github.com/VasilevNStas/opencode-db/actions/workflows/test.yml/badge.svg)](https://github.com/VasilevNStas/opencode-db/actions/workflows/test.yml)
[![release](https://github.com/VasilevNStas/opencode-db/actions/workflows/release.yml/badge.svg)](https://github.com/VasilevNStas/opencode-db/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/opencode-db)](https://pypi.org/project/opencode-db/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**OpenCode stores everything in a local SQLite database.** Every agent session, conversation, token usage, and cost is saved automatically. `opencode-db` is the CLI tool to work with that database — list sessions, export conversations to Markdown, track token costs, prune old data, and more.

[Русская версия](docs/README.ru.md)

> **Published on PyPI:** [opencode-db](https://pypi.org/project/opencode-db/) — install the ready-made package with `uv tool install opencode-db` or `pip install opencode-db`.

```
opencode-db --version     # installed version
opencode-db help        # full reference with examples
opencode-db list        # list recent sessions
opencode-db stats       # database summary
opencode-db health      # SQLite storage health (read-only)
opencode-db schema      # detect v1/v2 schema
opencode-db export      # save a dialog to .md (interactive)
opencode-db costs --total  # total token costs
```

---

## Installation

### Requirements

- Python 3.12+ — `opencode-db` refuses to start on older interpreters with a clear message (no cryptic `ImportError`)
- OpenCode (must have been run at least once — the database is created automatically)
- macOS / Linux
- [`uv`](https://docs.astral.sh/uv/) — optional, but recommended for installing and running on systems whose default `python3` is older than 3.12

### Database location

By default, `opencode-db` looks for OpenCode's database at:

```
~/.local/share/opencode/opencode.db
```

If your OpenCode stores the database at a custom path, you have two options:

**1. Environment variable** — set it once in your shell profile (`.zshrc`, `.bashrc`):

```bash
export OPENCODE_DB=/path/to/opencode.db
```

**2. Global `--db-path` flag** — for ad-hoc use or inspecting another database:

```bash
opencode-db --db-path /path/to/opencode.db list
opencode-db --db-path /path/to/opencode.db stats
```

The `--db-path` flag takes precedence over the environment variable.

### Recommended: uv

If your system `python3` is older than 3.12 (for example, macOS ships 3.9), use `uv` — it installs the tool into an isolated environment with a supported interpreter:

```bash
uv tool install opencode-db
# with enhanced Markdown rendering:
uv tool install "opencode-db[rich]"

# one-off run without installing:
uvx opencode-db stats
```

### One-command install

```bash
curl -fsSL https://raw.githubusercontent.com/VasilevNStas/opencode-db/master/install.sh | sh
```

Downloads everything to `~/.local/share/opencode-db/` and creates `~/.local/bin/opencode-db`. The installer looks for Python 3.12+ (including interpreters managed by `uv` or `pyenv`) and writes the discovered path into the launcher shebang.

### pip / pipx install

```bash
pipx install opencode-db
# or
pip install opencode-db
```

**Zero external dependencies** — runs on the Python standard library alone. Only Python 3.12+ is required; `rich` is optional for enhanced Markdown rendering.

### Manual install

1. Download the latest release from GitHub or clone the repo:

```bash
git clone https://github.com/VasilevNStas/opencode-db.git ~/.local/share/opencode-db
```

2. Create a launcher at `~/.local/bin/opencode-db`:

```bash
cat > ~/.local/bin/opencode-db << 'SCRIPT'
#!/usr/bin/env python3
import os
import sys

if sys.version_info < (3, 12):
    print(
        "opencode-db requires Python 3.12+; current: %s (%s)"
        % (".".join(map(str, sys.version_info[:3])), sys.executable),
        file=sys.stderr,
    )
    raise SystemExit(1)

PKG_DIR = os.path.expanduser("~/.local/share/opencode-db")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
from opencode_db.cli import main
sys.exit(main())
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

# Save a dialog in Markdown or lossless JSON
opencode-db export ses_1c9d --force
opencode-db export ses_1c9d --format json

# Show compaction summaries
opencode-db digest ses_1c9d --last 3

# Total token costs
opencode-db costs --total

# Database statistics
opencode-db stats

# Managed database snapshot
opencode-db backup
opencode-db backups list
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
opencode-db list --all --directory       # include directory paths
opencode-db list --root                  # root sessions only (orphans included)
opencode-db list --sub                   # child sessions only
opencode-db list --parent ses_1c9d       # children of one session
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
| `--directory` | Add a session directory column | — |
| `--root` | Only root sessions; orphaned children count as roots | — |
| `--sub` | Only sessions with an existing parent | — |
| `--parent ID` | Only children of this session (prefix allowed) | — |

---

### `directories` — launch directories

Lists every directory where OpenCode has run, including paths that no longer exist. Combines session directories with project roots and project-directory mappings.

```bash
opencode-db directories                  # grouped by path
opencode-db directories --missing        # only missing/inaccessible paths
opencode-db directories --existing       # only existing paths
opencode-db directories --project global # Global sessions by real directory
opencode-db directories --json           # full paths, counts, tokens, cost
```

`global` is a synthetic project for non-Git directories. The command never shows
`/` as a real directory; it shows the actual `session.directory` and marks the
project as `Global (no project root)`.

| Flag | Description | Default |
|---|---|---|
| `--missing` | Only paths not found on disk | — |
| `--existing` | Only paths that exist | — |
| `--project ID` | Filter by project | — |
| `--sort {date,sessions,cost,path}` | Sort order | date |
| `--limit N` | Max entries | 50 |
| `--no-check` | Skip filesystem check (`exists: null`) | — |
| `--json` | Output as JSON | — |

> `os.path.isdir()` is a point-in-time check. An offline volume or permission error can look like a missing directory.

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

### `export` — export dialog to Markdown or lossless JSON

Saves a conversation to `opencode-YYYY-MM-DD-<short_id>.md` or `.json` in the current directory. The short session ID prevents collisions when two sessions from the same day are exported.

**Three ways to pick a session:**

| Mode | Example | Description |
|---|---|---|
| By ID | `export ses_1c9d` | Explicit session ID (full or prefix) |
| Latest | `export --latest` | Most recent session |
| Interactive | `export` (no args) | Pick from a numbered list |

```bash
opencode-db export ses_1c9d                  # Markdown export
opencode-db export ses_1c9d --format json    # lossless JSON archive
opencode-db export --latest                   # most recent session
opencode-db export --latest --force           # overwrite if the file exists
opencode-db export --latest --full            # full Markdown, no truncation
opencode-db export --latest -n "bug fix"      # add a note to log.md
opencode-db export                            # interactive picker
opencode-db export -o ~/backup                # save to a different directory
```

Markdown keeps speaker labels, reasoning, tool calls and now also `patch` diffs, `file` metadata, `compaction` markers, and an explicit generic block for unknown part types. `step-start`/`step-finish` are skipped normally and included as hidden HTML comments with `--full`.

JSON is the lossless archive format:

```json
{
  "format": "opencode-db-export",
  "schema_version": 1,
  "tool_version": "0.13.0",
  "db_schema": "v1",
  "exported_at": "2026-10-22T18:00:00Z",
  "session": { "...raw session row...": "..." },
  "messages": [
    {
      "id": "msg_...",
      "type": "assistant",
      "role": "assistant",
      "data": { "...raw message JSON...": "..." },
      "parts": [{"id": "prt_...", "data": {"type": "patch", "...": "..."}}]
    }
  ]
}
```

For v1, `parts[].data` is the raw `part.data` JSON. For v2, each `session_message` row is preserved in `data`, and `parts` contains a normalized convenience view. Messages are written one at a time, so a large session does not need to fit in memory as one JSON object.

If the project directory contains `.obsidian`, Markdown export automatically creates or appends `log.md` with a project snapshot.

| Flag | Description | Default |
|---|---|---|
| `session_id` | Session ID (optional — interactive mode if omitted) | — |
| `--latest`, `-l` | Export the most recent session | — |
| `--format {md,json}` | Markdown or lossless JSON | `md` |
| `--full`, `-F` | Full Markdown output (no truncation; includes hidden step comments) | — |
| `--force`, `-f` | Overwrite the file if it exists | — |
| `--note`, `-n` | Description for log.md | — |
| `--output`, `-o` | Output directory | `os.getcwd()` |

### Bulk export

Export a set of sessions into a bundle:

```bash
opencode-db export --last 5                   # 5 newest roots + all descendants
opencode-db export --last 5 --no-subagents    # roots only
opencode-db export --since 2026-01-01         # sessions created since the date
opencode-db export --project proj_xxx         # all sessions in a project
opencode-db export --all                      # every session
opencode-db export --last 5 --format json     # lossless JSON bundle
opencode-db export ses_1c9d --with-subagents  # one root + descendants as a bundle
```

Rules:

- use only one selection rule per run (`session_id`, `--latest`, `--last`, `--since`, `--project`, or `--all`);
- `--last N` counts root sessions and includes descendants by default;
- `--since` uses `session.time_created`; use `--with-subagents` to add descendants;
- `--project` and `--all` include matching sessions; add `--with-subagents` for extra descendants;
- a session whose parent is missing is treated as a root;
- an empty selection is an error, not an empty export.

Bundle layout:

```text
opencode-export-YYYYMMDD-HHMMSS/
├── index.md                 # links to every exported session
├── metadata.json            # selection, counts, db schema, session records
└── transcript/
    ├── 01-<title>-<id>.md   # root sessions
    └── subagents/
        └── 01-<title>-<id>.md
```

`metadata.json` records the selection rule and value, root/subagent/total counts, and each session's id, title, parent, role, message count and relative file. The bundle is all-or-nothing: on a write error the partially created directory is removed.

| Flag | Description |
|---|---|
| `--last N` | Export the N newest root sessions and descendants |
| `--since YYYY-MM-DD` | Export sessions created on/after the date |
| `--project ID` | Export all sessions in a project |
| `--all` | Export every session |
| `--with-subagents` | Include child sessions (default for `--last`) |
| `--no-subagents` | Do not include child sessions |

### `digest` — compaction summaries

Shows the summaries OpenCode produced when it compacted a session. Works for v1 (`message.mode='compaction'` + text parts) and v2 (`session_message.type='compaction'`).

```bash
opencode-db digest ses_1c9d              # all compaction summaries
opencode-db digest ses_1c9d --last 3     # last three
opencode-db digest ses_1c9d --json       # machine-readable output
```

| Flag | Description | Default |
|---|---|---|
| `session_id` | Session ID (full or prefix) | required |
| `--last N` | Show only the last N digests | all |
| `--json` | JSON output | — |

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
opencode-db prune --missing-directories                  # preview sessions from missing paths
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
| `--missing-directories` | Sessions whose directory no longer exists (preview by default) |
| `--execute` | Execute missing-directory cleanup |
| `--backup` | Create a DB backup before deletion |
| `--no-backup` | Explicitly skip the DB backup |

---

### `backup` — managed database snapshots

Creates a consistent SQLite snapshot through the SQLite backup API (not `cp`), verifies it with `quick_check`, and records it in a manifest. Snapshots are gzip-compressed by default.

```bash
opencode-db backup                         # gzip snapshot in the managed directory
opencode-db backup --dry-run               # show the plan, write nothing
opencode-db backup --output ~/backups      # custom directory
opencode-db backup --no-compress           # plain .db snapshot
```

Default directory: `~/.local/share/opencode-db/backups` (override with `OPENCODE_DB_BACKUP_DIR` or `--output`).

The manifest stores the file name, UTC date, sha256, raw/stored size, schema family, session/message/part counts, `max(time_updated)`, source path and tool version.

This is separate from the automatic sidecar `opencode.db.bak.YYYYMMDD-HHMMSS` copies created by `delete` and `vacuum`.

### `backups` — inspect and manage snapshots

```bash
opencode-db backups list                   # all managed snapshots
opencode-db backups list --json
opencode-db backups list --dir ~/backups
opencode-db backups view <file>            # details + sha256 check
opencode-db backups view <file> --json
opencode-db backups verify <file>          # sha256 + quick_check
opencode-db backups remove <file>          # with confirmation
opencode-db backups prune 5                # keep the 5 newest
```

`view` checks the stored sha256. `verify` also decompresses the snapshot when needed and runs `quick_check`. `remove` and `prune` delete only files recorded in the manifest.

### `--from-backup` — read a snapshot

Every read-only command can use a managed snapshot instead of the live database:

```bash
opencode-db --from-backup <file> list
opencode-db --from-backup <file> health
opencode-db --from-backup <file> export ses_1c9d
```

The file may be a manifest alias or a direct path, plain `.db` or `.db.gz`. The sha256 is verified when the file is in the manifest; gzip snapshots are extracted to a temporary file that is removed on exit. The database is opened read-only, and `delete`, `prune` and `vacuum` are refused.

`--from-backup` and `--db-path` are mutually exclusive.

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

### Missing-directory cleanup

OpenCode stores the launch directory of every session in `session.directory`.
The TUI only shows sessions for the current project, so sessions created in a
deleted, renamed or unmounted directory can be hard to find. This mode finds
those sessions and deletes them only after several independent confirmations.

#### 1. Inspect candidates first (read-only)

```bash
opencode-db directories --missing
opencode-db directories --missing --json
opencode-db prune --missing-directories
opencode-db prune --missing-directories --project global
```

`directories --missing` is the safest first step: it does not touch the
database and shows the same paths, counts and costs.

Example preview:

```text
============================================================
  DELETE SESSIONS FROM MISSING DIRECTORIES
============================================================
  Database: ~/.local/share/opencode/opencode.db
  Sessions: 51, directories: 10, cost: $3.85
  2026-05-06 08:19:14 — 2026-09-12 16:45:41
    /Users/me/old-project — 15 sessions
    /Users/me/Documents/old-notes — 7 sessions
...
This is a preview. Add --execute to delete.
```

How “missing” is detected:

- the tool reads `session.directory` (or `session_v2.directory`);
- it calls `os.path.isdir()` on each path at command runtime;
- `False` means **not found or inaccessible** — it may be deleted, renamed,
  on an unmounted disk, on an offline network volume, or blocked by permissions;
- symlinks are followed; results are only true at the moment the command runs;
- `--no-check` on `directories` skips this check and reports `exists: null`.

Review this list carefully. A temporarily unavailable external disk can look
exactly like a deleted directory.

#### 2. Execute with the safety gates

```bash
# recommended: create a consistent SQLite backup first
opencode-db prune --missing-directories --execute --backup

# only if you already have an external backup
opencode-db prune --missing-directories --execute --no-backup
```

`delete --missing-directories ...` works the same way as `prune`.

Before anything is deleted, all of these gates must pass:

1. `--missing-directories` selects only sessions whose path is not found.
2. `--execute` is required; without it the command always stops after preview.
3. `--backup` or `--no-backup` must be chosen explicitly.
4. The command prints every path, session count, cost and date range.
5. You must type the exact phrase `DELETE <N> SESSIONS`.
6. You must answer a final `y/N` confirmation.
7. The candidate list is recomputed; if it changed, deletion is aborted.
8. All deletes run in one transaction; on error the transaction is rolled back.

`--force` does **not** bypass any of these gates. It is ignored in this mode.

#### What exactly is deleted

For each selected session:

- the `session` row;
- `message`, `part`, `todo`;
- `session_message`, `session_input`, `session_context_epoch`, `session_share`;
- `event` and `event_sequence` rows for that session.

Projects and the synthetic `global` project are **never** deleted. The tool
does not touch directories on disk — it only removes database rows.

After a successful cleanup you can reclaim disk space:

```bash
opencode-db vacuum
```

`VACUUM` can take time and temporarily needs free disk space roughly equal to
the database size.

#### Backup and recovery

With `--backup`, the tool creates a consistent SQLite copy next to the database:

```text
opencode.db.bak.20261020-111530
```

The exact path is printed before deletion. If you delete something by mistake:

1. stop OpenCode;
2. restore the backup over `opencode.db`;
3. remove stale `opencode.db-wal` / `opencode.db-shm` files if present;
4. start OpenCode again.

Without a backup, deleted sessions and their events cannot be recovered.

#### Recommended workflow

```bash
# 1. Close OpenCode to avoid concurrent writes.
opencode-db directories --missing

# 2. Preview the exact deletion.
opencode-db prune --missing-directories

# 3. Optional: only one project.
opencode-db prune --missing-directories --project global

# 4. Execute with a backup.
opencode-db prune --missing-directories --execute --backup

# 5. Reclaim disk space.
opencode-db vacuum
```

#### Limitations

- This mode is available for the v1 schema; v2 is refused until v2 writes are
  implemented.
- It cannot tell a deleted directory from an offline volume or permission error.
- It does not remove `project` rows or directories from disk.
- It cannot be combined with `--older-than`, `--before`, `--after`,
  `--keep-last`, `--interactive` or a session ID.
- There is no automatic or background cleanup.

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
opencode-db projects                      # project table with paths
opencode-db projects --json               # JSON output
opencode-db projects --missing            # projects whose path is gone
opencode-db projects --no-global          # hide the synthetic Global project
```

| Flag | Description |
|---|---|
| `--json` | JSON output |
| `--missing` | Only projects with a missing path |
| `--no-global` | Hide the synthetic Global project |

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

### `schema` — detect database schema

Shows which OpenCode schema family the database uses, the applied migration, and which operations are supported.

```bash
opencode-db schema                        # human-readable summary
opencode-db schema --json                 # JSON output
```

Supported families:

| OpenCode | Schema | Support |
|---|---|---|
| 1.19.x | v1 | read + write |
| 2.x preview | v2 | read-only |

On a v2 database, `health` and the other read-only commands work; `delete`, `prune`, and `vacuum` are refused until write support is implemented. Detection is based on tables and the migration journal, not on the OpenCode version string.

---

### `health` — SQLite storage health

Read-only report about how the SQLite file is laid out. It does not scan messages or parts and does not change the database.

```bash
opencode-db health                        # human-readable report
opencode-db health --json                 # stable JSON output
```

The report includes:

- database path and main file / WAL / SHM sizes;
- `page_size`, `page_count`, `freelist_count`;
- live data, freelist bytes and percentage;
- estimated space that `VACUUM` could reclaim;
- `auto_vacuum` and `journal_mode`;
- schema family and read-only status;
- whether `lsof`/`fuser` see another process holding the database.

A non-zero freelist means the file contains free pages left after deletes. `VACUUM` can return that space to the filesystem. If the freelist is already zero, there is usually little to reclaim.

The report also compares the newest managed backup with the live database and marks it as `aligned` or `out of sync`. `out of sync` only means the live database changed after the snapshot; it does not mean the backup is corrupt — use `backups verify` for integrity.

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

### `vacuum` — safe database optimization

Runs a guarded maintenance sequence:

1. checks that the schema is writable (v2 is refused);
2. checks whether another process is holding the database;
3. checks free disk space;
4. runs `quick_check` (or full `integrity_check` with `--full-check`);
5. checkpoints the WAL;
6. creates and verifies a backup;
7. optionally enables `auto_vacuum = INCREMENTAL`;
8. runs `VACUUM`;
9. verifies that `journal_mode` is still `wal` when it started as WAL;
10. runs `REINDEX` and `ANALYZE`;
11. runs a final integrity check and reports reclaimed space.

```bash
opencode-db vacuum                        # backup + confirmation
opencode-db vacuum --force                # skip confirmation
opencode-db vacuum --no-backup            # no backup (not recommended)
opencode-db vacuum --auto-vacuum          # enable incremental auto-vacuum
```

| Flag | Description |
|---|---|
| `--force`, `-f` | Skip the confirmation prompt only |
| `--backup` | Create a verified backup (default) |
| `--no-backup` | Do not create a backup (not recommended) |
| `--skip-lock-check` | Continue if the database may be in use |
| `--full-check` | Use full `integrity_check` instead of `quick_check` |
| `--auto-vacuum` | Enable `auto_vacuum = INCREMENTAL` permanently |

`--force` does **not** bypass lock checks, integrity checks, backup defaults or free-space checks.

#### Disk space and backup

`VACUUM` rebuilds the database and temporarily needs free space roughly equal to the database size. A backup needs about the same amount again. With the default backup enabled, expect roughly `2 × database size` of free space.

The backup is a consistent SQLite copy next to the database:

```text
opencode.db.bak.20261022-130156
```

The exact path is printed before the operation. If something goes wrong:

1. stop OpenCode;
2. restore the backup over `opencode.db`;
3. remove stale `opencode.db-wal` / `opencode.db-shm` files;
4. start OpenCode again.

Use `--no-backup` only if you already have an external backup. The command prints a warning when backup is disabled.

#### WAL and journal mode

WAL (write-ahead logging) lets OpenCode write new data to `opencode.db-wal` while readers continue to use the database. A checkpoint copies committed WAL frames back into the main file.

`VACUUM` does **not** require disabling WAL in modern SQLite. `opencode-db` checkpoints the WAL before maintenance and verifies the journal mode afterwards. If the database started in WAL mode and the mode changed, the command restores WAL. It never switches a non-WAL database to WAL.

`VACUUM` does not delete sessions, messages or chat history. It only repacks the database file and removes free pages.

#### Close OpenCode first

The process check is best-effort: it uses `lsof`, then `fuser`, excluding the current process. Close OpenCode before running vacuum. If neither tool is available, the command refuses to continue unless you pass `--skip-lock-check`.

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
| `health` | SQLite storage health | `--json` |
| `todos` | View session tasks | `--status`, `--json` |
| `vacuum` | Safe database optimization | `--force`, `--no-backup`, `--auto-vacuum` |
| `help` | Detailed reference | `<command>`, `--json` |

---

## Project architecture

```
opencode-db/
├── opencode_db/                          ← Python package (installed as opencode_db)
│   ├── __init__.py                       ← package init + Python version guard
│   ├── __main__.py                       ← python3 -m opencode_db
│   ├── cli.py                            ← argparse + command dispatcher
│   ├── config.py                         ← constants and paths
│   ├── db.py                             ← SQLite queries
│   ├── formatters.py                     ← tables, JSON, Markdown, snapshots
│   ├── i18n.py                           ← localization (EN/RU, 515 keys)
│   ├── backups.py                        ← managed snapshots, manifest, verify
│   ├── maintenance.py                    ← backup, integrity, WAL, lock checks
│   ├── markdown_to_ansi.py               ← Markdown → ANSI renderer for `view`
│   ├── runtime.py                        ← Python 3.12+ version guard
│   ├── utils.py                          ← date/token formatting, validation
│   └── commands/
│       ├── __init__.py                   ← command registry
│       ├── cmd_list.py                   ← opencode-db list
│       ├── cmd_info.py                   ← opencode-db info
│       ├── cmd_export.py                 ← opencode-db export
│       ├── cmd_delete.py                 ← opencode-db delete
│       ├── cmd_costs.py                  ← opencode-db costs
│       ├── cmd_prune.py                  ← opencode-db prune
│       ├── cmd_search.py                 ← opencode-db search
│       ├── cmd_tree.py                   ← opencode-db tree
│       ├── cmd_projects.py               ← opencode-db projects
│       ├── cmd_stats.py                  ← opencode-db stats
│       ├── cmd_backup.py                 ← opencode-db backup
│       ├── cmd_backups.py                ← opencode-db backups
│       ├── cmd_digest.py                 ← opencode-db digest
│       ├── cmd_health.py                 ← opencode-db health
│       ├── cmd_todos.py                  ← opencode-db todos
│       ├── cmd_vacuum.py                 ← opencode-db vacuum
│       ├── cmd_view.py                   ← opencode-db view
│       └── cmd_help.py                   ← opencode-db help
│
├── docs/
│   ├── README.ru.md                      ← documentation in Russian
│   └── README_PYPI.md                    ← PyPI page
├── contrib/
│   └── opencode-db-commands.json         ← OpenCode TUI custom commands config
├── tests/
├── README.md                             ← this file (English)
├── LICENSE
├── Makefile
├── pyproject.toml
└── install.sh
```

### How it works

1. The console script `opencode-db` (or `python3 -m opencode_db`) imports `opencode_db.cli` and calls `main()`.
2. `runtime.require_python()` checks the interpreter before importing `cli`/`db`; on Python < 3.12 it prints a clear message with remediation steps instead of failing with `ImportError`.
3. `cli.py` builds an `argparse` parser with subparsers from every command module and dispatches the call.
4. Each command is a separate `opencode_db/commands/cmd_*.py` module exporting two functions: `register(subparsers)` and `run(args, db)`.
5. `db.py` opens a connection to OpenCode's SQLite database (`~/.local/share/opencode/opencode.db`, with `opencode-next.db` fallback) and detects the schema family.
6. `store/` selects `V1Store` or `V2Store`; commands read through the same interface regardless of the underlying schema.
7. Destructive operations (`delete`, `prune`) always require confirmation (or `--force`); on v2 they are refused until write support lands.

### Database schema (key tables)

Stable OpenCode 1.19.x (v1):

```
session        — sessions: id, title, model (JSON), agent, cost, tokens_*, parent_id, summary_*
message        — messages: id, session_id, time_created, data (JSON: role, agent)
part           — message parts: id, message_id, session_id, data (JSON: type, text, state)
todo           — tasks: session_id, content, status, priority
project        — projects: id, worktree, name
```

Preview OpenCode 2.x (v2):

```
session_v2      — renamed session table with the same usage fields
session_message — typed JSON messages: user, assistant, synthetic, system, shell, compaction, ...
project         — projects: id, worktree, name, time_active, ...
```

v2 has no `message`, `part`, or `todo` tables. Assistant content is nested in
`session_message.data.content`, and todos are derived from the latest completed
`todowrite` tool call. Use `opencode-db schema` to inspect the detected family
before running write commands.

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

Add the commands from `contrib/opencode-db-commands.json` to your project's `opencode.json`:

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
~/.local/share/opencode-db/contrib/opencode-db-commands.json
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

The `--lang` flag applies to any command. All 515 UI strings are translated. Data content (session titles, project names, etc.) remains in its original language.

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

### VACUUM fails or refuses to start

`vacuum` now checks safety conditions before doing any work:

- **Database is open** — close OpenCode and any `sqlite3` process using the file.
  The command prints the PIDs. If you are certain the database is unused, pass
  `--skip-lock-check`.
- **Lock check unavailable** — install `lsof` or `fuser`, or pass
  `--skip-lock-check` after closing OpenCode.
- **Not enough free space** — `VACUUM` needs roughly the database size and the
  default backup needs another copy. Free space or use `--no-backup` (not
  recommended).
- **Integrity check failed** — restore the latest backup; do not run `VACUUM`
  on a corrupted file.

The command never deletes sessions or chat history. If `VACUUM` itself fails,
the database file remains intact; the backup path is printed in the output.

### `ImportError: cannot import name 'UTC' from 'datetime'`

This means `opencode-db` is running on Python older than 3.12 (for example, the system Python 3.9). Check:

```bash
python3 --version
```

Fix with `uv` (recommended):

```bash
uv python install 3.13
uv tool install opencode-db
opencode-db stats
```

Or run the repository checkout with an explicit interpreter:

```bash
uvx --from . opencode-db stats
# alternative for a persistent dev environment:
uv run --python 3.13 opencode-db stats
```

After changing the interpreter, rerun `install.sh` to regenerate the `~/.local/bin/opencode-db` launcher.

---

## Development

### Local development

Requires Python 3.12+ and `pytest`/`ruff`:

```bash
git clone https://github.com/VasilevNStas/opencode-db.git
cd opencode-db

uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[rich]"
uv pip install pytest ruff==0.17.1

make check          # check-python + ruff + 291 tests
```

`make check` fails fast with a clear message if the active interpreter is older than 3.12.

### Adding a new command

1. Create `opencode_db/commands/cmd_xxx.py`:

```python
def register(subparsers):
    p = subparsers.add_parser("xxx", help="Description")
    p.add_argument("--flag", type=str)

def run(args, db):
    # your logic here
    return 0
```

2. Register it in `opencode_db/commands/__init__.py`:

```python
import cmd_xxx
COMMANDS["xxx"] = cmd_xxx
```

The command will appear in `--help` automatically.

### Running without installation

```bash
python3 ~/.local/share/opencode-db list
```

Or from the repository root (Python 3.12+):

```bash
python3 -m opencode_db list
uvx --from . opencode-db list
```

---

## Лицензия / License

MIT — подробнее в файле [LICENSE](LICENSE)

© 2026 Vasilev Stas — код можно свободно использовать, изменять и распространять
