#!/usr/bin/env python3
"""Fail when the committed schema manifest differs from pinned upstream refs."""

from update_schema_manifest import main

if __name__ == "__main__":
    raise SystemExit(main(["--check"]))
