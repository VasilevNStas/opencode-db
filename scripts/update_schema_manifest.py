#!/usr/bin/env python3
"""Generate the OpenCode schema manifest from pinned upstream refs.

The manifest is intentionally small: tables, columns, migration IDs and v2
message type tags. It is used by the runtime schema detector and by CI to spot
upstream drift. No TypeScript, Bun or third-party packages are required.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

REPO = "anomalyco/opencode"
DEFAULT_V1_REF = "v1.19.3"
DEFAULT_V2_REF = "v2.0.32"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "opencode_db" / "schema_manifest.json"

RAW_URL = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
COMMIT_URL = "https://api.github.com/repos/{repo}/commits/{ref}"

SCHEMA_PATH = "packages/core/src/database/schema.gen.ts"
MIGRATION_PATH = "packages/core/src/database/migration.gen.ts"
MESSAGE_TYPES_PATH = "packages/schema/src/session-message.ts"

_CREATE_TABLE_RE = re.compile(r"CREATE TABLE `([^`]+)` \((.*?)\);", re.DOTALL)
_MIGRATION_RE = re.compile(r"migration/([0-9]{14}_[A-Za-z0-9_-]+)")
_MESSAGE_TYPE_RE = re.compile(r'Schema\.tag\("([^"]+)"\)')


def _request(url: str) -> str:
    headers = {
        "Accept": "application/vnd.github.raw",
        "User-Agent": "opencode-db-schema-manifest",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code} while fetching {url}") from exc
    except (urllib.error.URLError, TimeoutError):
        # Some macOS/Python combinations time out during the TLS handshake while
        # curl succeeds. Keep the generator usable without adding dependencies.
        command = ["curl", "-fsSL", "--max-time", "30", url]
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            command.extend(["-H", f"Authorization: Bearer {token}"])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        raise SystemExit(f"Cannot fetch {url}: {result.stderr.strip()}") from None


def fetch_text(ref: str, path: str) -> str:
    return _request(RAW_URL.format(repo=REPO, ref=ref, path=path))


def fetch_commit(ref: str) -> str:
    try:
        data = json.loads(_request(COMMIT_URL.format(repo=REPO, ref=ref)))
    except (json.JSONDecodeError, KeyError):
        return ref
    return data.get("sha", ref)


def _split_top_level(body: str) -> list[str]:
    """Split a CREATE TABLE body by commas outside parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def extract_tables(schema_text: str) -> dict[str, list[str]]:
    """Extract table names and column names from generated SQL DDL."""
    text = schema_text.replace("\\`", "`")
    tables: dict[str, list[str]] = {}
    for match in _CREATE_TABLE_RE.finditer(text):
        name = match.group(1)
        body = match.group(2)
        columns: list[str] = []
        for item in _split_top_level(body):
            if not item.startswith("`"):
                continue
            end = item.find("`", 1)
            if end == -1:
                continue
            column = item[1:end]
            if column and column not in columns:
                columns.append(column)
        tables[name] = columns
    return dict(sorted(tables.items()))


def extract_migrations(migration_text: str) -> list[str]:
    return sorted(set(_MIGRATION_RE.findall(migration_text)))


def extract_message_types(message_text: str) -> list[str]:
    return sorted(set(_MESSAGE_TYPE_RE.findall(message_text)))


def build_family(
    ref: str,
    *,
    include_message_types: bool = False,
) -> dict[str, object]:
    schema = fetch_text(ref, SCHEMA_PATH)
    migrations = extract_migrations(fetch_text(ref, MIGRATION_PATH))
    family: dict[str, object] = {
        "ref": ref,
        "commit": fetch_commit(ref),
        "migrations": migrations,
        "max_migration": migrations[-1] if migrations else None,
        "tables": extract_tables(schema),
        "message_types": [],
    }
    if include_message_types:
        family["message_types"] = extract_message_types(fetch_text(ref, MESSAGE_TYPES_PATH))
    return family


def build_manifest(v1_ref: str, v2_ref: str) -> dict[str, object]:
    return {
        "manifest_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": {"repo": REPO, "v1_ref": v1_ref, "v2_ref": v2_ref},
        "families": {
            "v1": build_family(v1_ref),
            "v2": build_family(v2_ref, include_message_types=True),
        },
    }


def _comparable(manifest: dict[str, object]) -> dict[str, object]:
    """Ignore the timestamp when checking for drift."""
    return {key: value for key, value in manifest.items() if key != "generated_at"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-ref", default=DEFAULT_V1_REF)
    parser.add_argument("--v2-ref", default=DEFAULT_V2_REF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the committed manifest differs from upstream (ignores generated_at).",
    )
    args = parser.parse_args(argv)

    manifest = build_manifest(args.v1_ref, args.v2_ref)

    if args.check:
        if not args.output.exists():
            print(f"Schema manifest not found: {args.output}", file=sys.stderr)
            return 1
        current = json.loads(args.output.read_text(encoding="utf-8"))
        if _comparable(current) == _comparable(manifest):
            print("Schema manifest is up to date.")
            return 0
        print(
            "Schema manifest is out of date. Run scripts/update_schema_manifest.py.",
            file=sys.stderr,
        )
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
