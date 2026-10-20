"""Version lookup for the installed package and source checkouts."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path


@lru_cache(maxsize=1)
def get_version() -> str:
    """Return the installed package version, with a source-tree fallback."""
    try:
        return package_version("opencode-db")
    except PackageNotFoundError:
        pass

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return str(data["project"]["version"])
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
        return "unknown"
