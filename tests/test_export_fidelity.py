import json
import re

from opencode_db.formatters import format_part_to_md
from opencode_db.store import open_store


def _insert_v1_fidelity(db) -> None:
    ts = 1_790_000_000_000
    db.execute(
        "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
        (
            "msg_extra",
            "ses_001",
            ts,
            json.dumps({"role": "assistant", "agent": "build"}),
        ),
    )
    parts = [
        ("part_patch", {"type": "patch", "hash": "abc123", "files": ["/tmp/a.py"]}),
        (
            "part_file",
            {
                "type": "file",
                "mime": "text/plain",
                "filename": "notes.txt",
                "url": "file:///tmp/notes.txt",
            },
        ),
        ("part_step_start", {"type": "step-start"}),
        (
            "part_step_finish",
            {"type": "step-finish", "reason": "stop", "cost": 0.01, "tokens": {"total": 3}},
        ),
        ("part_custom", {"type": "custom", "foo": "bar"}),
    ]
    for part_id, data in parts:
        db.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, data) "
            "VALUES (?, ?, ?, ?, ?)",
            (part_id, "msg_extra", "ses_001", ts, json.dumps(data)),
        )

    db.execute(
        "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
        (
            "msg_comp",
            "ses_001",
            ts + 1,
            json.dumps(
                {
                    "role": "assistant",
                    "mode": "compaction",
                    "agent": "compaction",
                    "summary": True,
                    "cost": 0.02,
                    "tokens": {"total": 10},
                }
            ),
        ),
    )
    db.execute(
        "INSERT INTO part (id, message_id, session_id, time_created, data) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            "part_comp",
            "msg_comp",
            "ses_001",
            ts + 1,
            json.dumps({"type": "text", "text": "Compacted summary text"}),
        ),
    )
    db.commit()


def _export(db, tmp_path, fmt="json", session_id="ses_001"):
    from opencode_db.commands.cmd_export import run

    class Args:
        pass

    args = Args()
    args.session_id = session_id
    args.latest = False
    args.full = False
    args.force = True
    args.note = None
    args.output = str(tmp_path)
    args.format = fmt
    return run(args, db)


def test_v1_get_messages_preserves_new_part_types(db) -> None:
    _insert_v1_fidelity(db)
    store = open_store(db)
    messages = store.get_messages("ses_001")
    extra = next(message for message in messages if message["id"] == "msg_extra")
    types = {part["type"] for part in extra["parts"]}
    assert {"patch", "file", "step-start", "step-finish", "custom"} <= types
    custom = next(part for part in extra["parts"] if part["type"] == "custom")
    assert custom["data"]["foo"] == "bar"


def test_markdown_formats_patch_file_compaction_and_unknown(db, tmp_path) -> None:
    _insert_v1_fidelity(db)
    assert _export(db, tmp_path, fmt="md") == 0
    output = next(tmp_path.glob("*.md")).read_text(encoding="utf-8")
    assert "abc123" in output
    assert "/tmp/a.py" in output
    assert "notes.txt" in output
    assert "Compaction" in output
    assert "Compacted summary text" in output
    assert "custom" in output
    assert "```json" in output
    assert "step-start" not in output

    full = format_part_to_md({"type": "step-start"}, full=True)
    assert full == "<!-- step-start -->"


def test_v1_json_export_is_lossless(db, tmp_path) -> None:
    _insert_v1_fidelity(db)
    assert _export(db, tmp_path) == 0
    path = next(tmp_path.glob("*.json"))
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["format"] == "opencode-db-export"
    assert data["schema_version"] == 1
    assert data["db_schema"] == "v1"
    assert data["session"]["id"] == "ses_001"
    assert data["exported_at"].endswith("Z")

    extra = next(message for message in data["messages"] if message["id"] == "msg_extra")
    by_type = {part["data"]["type"]: part["data"] for part in extra["parts"]}
    assert by_type["patch"] == {"type": "patch", "hash": "abc123", "files": ["/tmp/a.py"]}
    assert by_type["custom"]["foo"] == "bar"
    assert by_type["step-finish"]["tokens"]["total"] == 3

    comp = next(message for message in data["messages"] if message["id"] == "msg_comp")
    assert comp["data"]["mode"] == "compaction"
    assert "Compacted summary text" in comp["parts"][0]["data"]["text"]


def test_export_filename_contains_date_and_short_id(db, tmp_path) -> None:
    _insert_v1_fidelity(db)
    assert _export(db, tmp_path) == 0
    path = next(tmp_path.glob("*.json"))
    assert re.match(r"opencode-\d{4}-\d{2}-\d{2}-ses_001\.json$", path.name)

    assert _export(db, tmp_path, session_id="ses_002") == 0
    names = {item.name for item in tmp_path.glob("*.json")}
    assert len(names) == 2


def test_digest_v1_json_and_last(db, capsys) -> None:
    from opencode_db.commands.cmd_digest import run

    _insert_v1_fidelity(db)

    class Args:
        session_id = "ses_001"
        last = None
        json = True

    assert run(Args(), db) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["count"] == 1
    assert data["digests"][0]["message_id"] == "msg_comp"
    assert data["digests"][0]["text"] == "Compacted summary text"
    assert data["digests"][0]["tokens"]["total"] == 10

    class LastArgs:
        session_id = "ses_001"
        last = 0
        json = True

    assert run(LastArgs(), db) == 1


def test_export_json_and_digest_are_registered() -> None:
    from opencode_db.cli import build_parser

    parser = build_parser()
    export_args = parser.parse_args(["export", "ses_001", "--format", "json"])
    assert export_args.format == "json"
    digest_args = parser.parse_args(["digest", "ses_001", "--last", "2"])
    assert digest_args.command == "digest"
    assert digest_args.last == 2
