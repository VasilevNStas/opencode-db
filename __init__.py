#!/usr/bin/env python3
"""opencode-db: управление базой данных OpenCode.

Позволяет просматривать, экспортировать, удалять сессии,
анализировать расход токенов и управлять хранилищем.

Использование:
  opencode-db --help
  opencode-db list
  opencode-db export <session_id>
  opencode-db info <session_id>
  opencode-db delete <session_id>
  opencode-db costs [session_id]
  opencode-db prune
  opencode-db search <query>
  opencode-db tree [session_id]
  opencode-db projects
  opencode-db stats
  opencode-db todos [session_id]
  opencode-db vacuum
"""

import os
import sys

# Добавляем директорию пакета в sys.path — все модули импортируются
# абсолютными именами, без относительных импортов.
PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

import cli

if __name__ == "__main__":
    sys.exit(cli.main())
