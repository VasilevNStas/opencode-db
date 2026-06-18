# opencode-db

**OpenCode database CLI manager** — browse, export, analyze, and clean up agent sessions.

```bash
pip install opencode-db
```

## Quick start

```bash
opencode-db list         # recent sessions
opencode-db stats        # database summary
opencode-db costs --total  # total token costs
opencode-db export       # export dialog to .md (interactive)
opencode-db help         # full reference
```

## Requirements

- Python 3.12+
- [OpenCode](https://opencode.ai) (must have been run at least once)
- macOS / Linux
