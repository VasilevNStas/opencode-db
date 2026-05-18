"""Поддержка запуска как модуля: python3 -m opencode_db.

Устанавливает sys.path и делегирует cli.main().
"""

import os
import sys

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

import cli

sys.exit(cli.main())
