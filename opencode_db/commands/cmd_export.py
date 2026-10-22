"""Команда export: экспорт диалога в Markdown или lossless JSON.

Режимы выбора сессии:
  - export <session_id>          — по ID (полный или префикс)
  - export --latest              — самая свежая сессия
  - export (без аргументов)      — интерактивный выбор из списка
"""

import argparse
import json
import os
import re
import shutil
from datetime import UTC, datetime

from ..db import SessionError
from ..formatters import collect_snapshot, format_part_to_md, update_log
from ..i18n import _
from ..sanitize import redact, sanitize_obj
from ..store import open_store
from ..utils import build_help_epilog, format_cost, format_ts, parse_date
from ..version import get_version

_EXPORT_EXAMPLES = [
    ("<session_id>", "help.export.e0"),
    ("--latest", "help.export.e1"),
    ("", "help.export.e2"),
    ("--full", "help.export.e3"),
    ("--force", "help.export.e4"),
    ('--note "text"', "help.export.e5"),
    ("--format json", "help.export.e6"),
    ("--last 5", "help.export.e7"),
    ("--since 2026-01-01", "help.export.e8"),
    ("--project proj_xxx", "help.export.e9"),
    ("--all", "help.export.e10"),
    ("--with-subagents", "help.export.e11"),
    ("--no-subagents", "help.export.e12"),
    ("--sanitize", "help.export.e13"),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "export",
        help=_("help.cmd.export"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=build_help_epilog("export", _EXPORT_EXAMPLES),
    )
    p.add_argument(
        "session_id",
        nargs="?",
        help="Session ID (optional — interactive mode if omitted)",
    )
    p.add_argument("--latest", "-l", action="store_true", help="Export the most recent session")
    selection = p.add_mutually_exclusive_group()
    selection.add_argument("--last", type=int, help="Export the N most recent root sessions")
    selection.add_argument("--since", type=str, help="Export sessions created since YYYY-MM-DD")
    selection.add_argument("--project", type=str, help="Export all sessions in a project")
    selection.add_argument("--all", action="store_true", help="Export all sessions")
    cascade = p.add_mutually_exclusive_group()
    cascade.add_argument("--with-subagents", action="store_true", help="Include child sessions")
    cascade.add_argument("--no-subagents", action="store_true", help="Do not include child sessions")
    p.add_argument(
        "--full",
        "-F",
        action="store_true",
        help="Full output (do not truncate tool outputs)",
    )
    p.add_argument("--force", "-f", action="store_true", help="Overwrite existing file")
    p.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Export format (md or lossless json)",
    )
    p.add_argument(
        "--sanitize",
        action="store_true",
        help="Best-effort redaction of high-confidence secrets",
    )
    p.add_argument("--note", "-n", type=str, help="Description for log.md")
    p.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output directory (default: current)",
    )


def _export_by_id(store, session_id, output_dir, force, note, full, fmt) -> int:
    try:
        session_info = store.get_session_info(session_id)
    except SessionError as e:
        print(e.message)
        return 1
    return _do_export(store, session_info, output_dir, force, note, full, fmt)


def _export_latest(store, output_dir, force, note, full, fmt) -> int:
    try:
        session_id = store.get_latest_session()
        session_info = store.get_session_info(session_id)
    except SessionError as e:
        print(e.message)
        return 1
    title = store.get_session_title(session_info)
    print(_("session.latest", title=title))
    return _do_export(store, session_info, output_dir, force, note, full, fmt)


def _export_interactive(store, output_dir, force, note, full, fmt, sanitize=False) -> int:
    sessions = store.get_recent_sessions()

    if not sessions:
        print(_("export.no_sessions"))
        return 1

    print(f"\n  {'─' * 60}")
    print(f"  {_('export.interactive_header')}")
    print(f"  {'─' * 60}")

    for i, s in enumerate(sessions, 1):
        title = store.get_session_title(s)
        created = format_ts(s["time_created"], "%Y-%m-%d %H:%M")
        cost = format_cost(s["cost"])
        print(f"  {i:2d}. {s['id'][:24]}  {created}  {title[:40]:40s}  {cost}")

    print(f"  {'─' * 60}")

    while True:
        try:
            choice = input("  " + _("export.interactive_prompt")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1

        if not choice:
            print(_("export.interactive_abort"))
            return 1

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                break
        except ValueError:
            pass

        print(f"  {_('export.interactive_error', n=len(sessions))}")

    session_id = sessions[idx]["id"]
    title = store.get_session_title(sessions[idx])
    print(_("export.interactive_exporting", title=title))
    try:
        session_info = store.get_session_info(session_id)
    except SessionError as e:
        print(e.message)
        return 1
    return _do_export(store, session_info, output_dir, force, note, full, fmt, sanitize=sanitize)


def _export_filename(session_info, output_dir: str, extension: str) -> str:
    date_str = format_ts(session_info["time_created"], "%Y-%m-%d")
    short_id = str(session_info["id"])[:12]
    return os.path.join(output_dir, f"opencode-{date_str}-{short_id}.{extension}")


def _do_export(
    store,
    session_info,
    output_dir,
    force,
    note,
    full=False,
    fmt="md",
    filename_override=None,
    quiet=False,
    update_obsidian=True,
    sanitize=False,
) -> int:
    """Внутренняя функция: экспорт диалога."""
    if fmt == "json":
        return _do_export_json(
            store,
            session_info,
            output_dir,
            force,
            filename_override=filename_override,
            quiet=quiet,
            sanitize=sanitize,
        )

    title = store.get_session_title(session_info)
    model = store.parse_model(session_info)

    messages = store.get_messages(session_info["id"])
    filename = filename_override or _export_filename(session_info, output_dir, "md")

    if os.path.isfile(filename) and not force:
        print(_("export.exists", path=filename))
        print(_("export.exists_hint"))
        return 1

    date_display = format_ts(session_info["time_created"])

    md_header = f"""# {_("md.header.title")}: {title}

- **{_("md.header.date")}**: {date_display}
- **{_("md.header.model")}**: {model}
- **{_("md.header.session_id")}**: `{session_info["id"][:24]}`
- **{_("md.header.messages")}**: {len(messages)}

---
"""

    md_body = []
    for msg in messages:
        if not msg.get("parts"):
            continue

        ts = format_ts(msg["time"], "%H:%M:%S")

        if msg["role"] == "user":
            md_body.append(f"## {_('export.role_user', ts=ts)}")
        else:
            agent_tag = _("export.agent_tag", agent=msg["agent"]) if msg.get("agent") else ""
            md_body.append(f"## {_('export.role_assistant', ts=ts, agent=agent_tag)}")

        md_body.append("")

        if msg.get("mode") == "compaction" and not any(
            part.get("type") == "compaction" for part in msg["parts"]
        ):
            md_body.append(f"> **🗜️ {_('md.compaction')}**")
            md_body.append("")

        for part in msg["parts"]:
            formatted = format_part_to_md(part, full=full)
            if formatted:
                md_body.append(formatted)
                md_body.append("")

        md_body.append("---")
        md_body.append("")

    content = md_header + "\n".join(md_body)
    if sanitize:
        content = redact(content)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    if not quiet:
        print(_("export.saved", path=filename))
        print(_("export.messages", n=len(messages)))

    obsidian_dir = os.getcwd()
    if not update_obsidian:
        return 0
    if os.path.isdir(os.path.join(obsidian_dir, ".obsidian")):
        snapshot = collect_snapshot(obsidian_dir)
        now_str = format_ts(session_info["time_created"], "%Y-%m-%d %H:%M")
        update_log(obsidian_dir, title, note, filename, snapshot, now_str)
    else:
        print(_("not_obsidian"))

    return 0


def _do_export_json(
    store,
    session_info,
    output_dir,
    force,
    filename_override=None,
    quiet=False,
    sanitize=False,
) -> int:
    filename = filename_override or _export_filename(session_info, output_dir, "json")
    if os.path.isfile(filename) and not force:
        print(_("export.exists", path=filename))
        print(_("export.exists_hint"))
        return 1

    session_row = store.get_session_row(session_info["id"]) or {}
    header = {
        "format": "opencode-db-export",
        "schema_version": 1,
        "tool_version": get_version(),
        "db_schema": store.schema.family.value,
        "exported_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "session": session_row,
    }
    if sanitize:
        header = sanitize_obj(header)

    count = 0
    try:
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write("{\n")
            for key, value in header.items():
                handle.write(f'  "{key}": {json.dumps(value, ensure_ascii=False, default=str)},\n')
            handle.write('  "messages": [\n')
            first = True
            for message in store.iter_raw_messages(session_info["id"]):
                if sanitize:
                    message = sanitize_obj(message)
                data = message.get("data")
                if isinstance(data, dict):
                    message.setdefault("type", data.get("type") or data.get("role") or "unknown")
                    message.setdefault(
                        "role",
                        data.get("role")
                        or ("user" if data.get("type") == "user" else "assistant"),
                    )
                if first:
                    first = False
                else:
                    handle.write(",\n")
                handle.write("    ")
                json.dump(message, handle, ensure_ascii=False, default=str)
                count += 1
            handle.write("\n  ]\n}\n")
    except Exception:
        if os.path.isfile(filename):
            os.remove(filename)
        raise

    if not quiet:
        print(_("export.saved", path=filename))
        print(_("export.messages", n=count))
    return 0


def _slug_title(title: str, limit: int = 40) -> str:
    slug = re.sub(r"[^\w.-]+", "-", title, flags=re.UNICODE).strip("-._")
    return (slug or "session")[:limit]


def _bulk_requested(args) -> bool:
    return bool(
        args.last is not None
        or args.since
        or args.project
        or args.all
    )


def _selection_error(args) -> str | None:
    if args.session_id and _bulk_requested(args):
        return _("export.selection_conflict")
    if args.latest and _bulk_requested(args):
        return _("export.selection_conflict")
    if args.last is not None and args.last < 1:
        return _("export.invalid_last")
    if args.since and parse_date(args.since) is None:
        return _("export.invalid_since")
    if (
        not (args.session_id or args.latest or _bulk_requested(args))
        and (args.with_subagents or args.no_subagents)
    ):
        return _("export.selection_required")
    return None


def _bundle_dir(output_dir: str) -> str:
    base = datetime.now(UTC).strftime("opencode-export-%Y%m%d-%H%M%S")
    path = os.path.join(output_dir, base)
    counter = 1
    while os.path.exists(path):
        path = os.path.join(output_dir, f"{base}-{counter}")
        counter += 1
    return path


def _write_bundle_index(
    bundle: str,
    records,
    rule: str,
    value,
    fmt: str,
    sanitize: bool = False,
) -> None:
    if sanitize:
        rule = redact(str(rule))
        value = redact(str(value))
        records = sanitize_obj(records)
    lines = [
        f"# {_('export.bundle_title')}",
        "",
        f"- {_('export.bundle_rule')}: `{rule}`",
        f"- {_('export.bundle_value')}: `{value}`",
        f"- {_('export.bundle_format')}: `{fmt}`",
        f"- {_('export.bundle_total')}: {len(records)}",
        "",
        f"## {_('export.bundle_sessions')}",
        "",
    ]
    for record in records:
        title = str(record["title"]).replace("[", "\\[").replace("]", "\\]")
        indent = "" if record["role"] == "root" else "  "
        lines.append(
            f"{indent}- [{title}]({record['file']}) — `{record['id'][:12]}` "
            f"({record['messages']} {_('export.bundle_msgs')})"
        )
    with open(os.path.join(bundle, "index.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _run_bulk(
    store,
    args,
    output_dir: str,
    full: bool,
    fmt: str,
    roots: list[str],
    rule: str,
    value,
    with_subagents: bool,
    sanitize: bool = False,
) -> int:
    selected = []
    seen = set()
    for root in roots:
        if root not in seen:
            selected.append(root)
            seen.add(root)
        if not with_subagents:
            continue
        children = []
        for child in store.get_descendant_ids(root):
            if child in seen:
                continue
            brief = store.get_session_brief(child)
            if brief:
                children.append((brief.get("time_created") or 0, child))
        for _ts, child in sorted(children):
            if child not in seen:
                selected.append(child)
                seen.add(child)

    if not selected:
        print(_("export.no_matches"))
        return 1

    selected_set = set(selected)
    records = []
    for session_id in selected:
        brief = store.get_session_brief(session_id)
        if not brief:
            continue
        parent_id = brief.get("parent_id")
        role = "subagent" if parent_id in selected_set else "root"
        records.append(
            {
                "id": session_id,
                "title": brief.get("title") or _("info.unnamed"),
                "parent_id": parent_id,
                "role": role,
                "time_created": brief.get("time_created"),
                "messages": store.get_message_count(session_id),
                "file": "",
            }
        )

    if not records:
        print(_("export.no_matches"))
        return 1

    bundle = _bundle_dir(output_dir)
    try:
        os.makedirs(os.path.join(bundle, "transcript"), exist_ok=True)
        counters = {"root": 0, "subagent": 0}
        for record in records:
            counters[record["role"]] += 1
            folder = "transcript" if record["role"] == "root" else "transcript/subagents"
            os.makedirs(os.path.join(bundle, *folder.split("/")), exist_ok=True)
            filename = (
                f"{counters[record['role']]:02d}-"
                f"{_slug_title(record['title'])}-{record['id'][:12]}.{fmt}"
            )
            relative = f"{folder}/{filename}"
            record["file"] = relative
            session_info = store.get_session_info(record["id"])
            code = _do_export(
                store,
                session_info,
                os.path.join(bundle, *folder.split("/")),
                True,
                None,
                full,
                fmt,
                filename_override=os.path.join(bundle, *relative.split("/")),
                quiet=True,
                update_obsidian=False,
                sanitize=sanitize,
            )
            if code != 0:
                raise RuntimeError(f"export failed for {record['id']}")

        metadata = {
            "format": "opencode-db-export-bundle",
            "schema_version": 1,
            "tool_version": get_version(),
            "db_schema": store.schema.family.value,
            "exported_at": datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "selection": {
                "rule": rule,
                "value": value,
                "with_subagents": with_subagents,
                "format": fmt,
            },
            "counts": {
                "roots": sum(1 for record in records if record["role"] == "root"),
                "subagents": sum(1 for record in records if record["role"] == "subagent"),
                "total": len(records),
            },
            "sessions": records,
        }
        if sanitize:
            metadata = sanitize_obj(metadata)
        with open(os.path.join(bundle, "metadata.json"), "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
        _write_bundle_index(bundle, records, rule, value, fmt, sanitize=sanitize)
    except Exception:
        shutil.rmtree(bundle, ignore_errors=True)
        raise

    print(_("export.bundle_saved", path=bundle))
    print(
        _(
            "export.bundle_counts",
            roots=metadata["counts"]["roots"],
            subagents=metadata["counts"]["subagents"],
            total=metadata["counts"]["total"],
        )
    )
    return 0


def run(args, db) -> int:
    for name, default in (
        ("last", None),
        ("since", None),
        ("project", None),
        ("all", False),
        ("with_subagents", False),
        ("no_subagents", False),
    ):
        if not hasattr(args, name):
            setattr(args, name, default)
    output_dir = args.output or os.getcwd()
    full = args.full
    fmt = getattr(args, "format", "md")
    sanitize = getattr(args, "sanitize", False)

    error = _selection_error(args)
    if error:
        print(error)
        return 1

    store = open_store(db)
    if args.session_id:
        try:
            session_info = store.get_session_info(args.session_id)
        except SessionError as exc:
            print(exc.message)
            return 1
        if args.with_subagents:
            return _run_bulk(
                store,
                args,
                output_dir,
                full,
                fmt,
                [session_info["id"]],
                "session",
                session_info["id"],
                True,
                sanitize=sanitize,
            )
        return _do_export(
            store,
            session_info,
            output_dir,
            args.force,
            args.note,
            full,
            fmt,
            sanitize=sanitize,
        )

    if args.latest:
        try:
            session_info = store.get_session_info(store.get_latest_session())
        except SessionError as exc:
            print(exc.message)
            return 1
        print(_("session.latest", title=store.get_session_title(session_info)))
        if args.with_subagents:
            return _run_bulk(
                store,
                args,
                output_dir,
                full,
                fmt,
                [session_info["id"]],
                "latest",
                session_info["id"],
                True,
                sanitize=sanitize,
            )
        return _do_export(
            store,
            session_info,
            output_dir,
            args.force,
            args.note,
            full,
            fmt,
            sanitize=sanitize,
        )

    if _bulk_requested(args):
        if args.last is not None:
            return _run_bulk(
                store,
                args,
                output_dir,
                full,
                fmt,
                store.get_root_session_ids(args.last),
                "last",
                args.last,
                not args.no_subagents,
                sanitize=sanitize,
            )
        if args.since:
            since = parse_date(args.since)
            assert since is not None
            return _run_bulk(
                store,
                args,
                output_dir,
                full,
                fmt,
                store.get_session_ids_since(int(since.timestamp() * 1000)),
                "since",
                args.since,
                args.with_subagents,
                sanitize=sanitize,
            )
        if args.project:
            return _run_bulk(
                store,
                args,
                output_dir,
                full,
                fmt,
                store.get_session_ids_by_project(args.project),
                "project",
                args.project,
                args.with_subagents,
                sanitize=sanitize,
            )
        if args.all:
            return _run_bulk(
                store,
                args,
                output_dir,
                full,
                fmt,
                store.get_all_session_ids(),
                "all",
                True,
                args.with_subagents,
                sanitize=sanitize,
            )

    return _export_interactive(
        store, output_dir, args.force, args.note, full, fmt, sanitize=sanitize
    )
