import json

from opencode_db.commands.cmd_export import run


def _args(**kwargs):
    base = dict(
        session_id=None,
        latest=False,
        last=None,
        since=None,
        project=None,
        all=False,
        with_subagents=False,
        no_subagents=False,
        full=False,
        force=False,
        note=None,
        format="md",
    )
    base.update(kwargs)
    return type("Args", (), base)()


def _bundle(tmp_path):
    return next(tmp_path.glob("opencode-export-*"))


def test_export_last_includes_subagents_by_default(db, tmp_path, capsys) -> None:
    args = _args(last=2, output=str(tmp_path))
    assert run(args, db) == 0
    out = capsys.readouterr().out
    assert "Roots: 2" in out or "Roots: 2" in out.replace("  ", "")

    bundle = _bundle(tmp_path)
    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["selection"]["rule"] == "last"
    assert metadata["selection"]["value"] == 2
    assert metadata["selection"]["with_subagents"] is True
    assert metadata["counts"] == {"roots": 2, "subagents": 1, "total": 3}
    ids = {item["id"] for item in metadata["sessions"]}
    assert ids == {"ses_004", "ses_001", "ses_002"}
    assert (bundle / "transcript").is_dir()
    assert list((bundle / "transcript" / "subagents").glob("*.md"))
    assert (bundle / "index.md").is_file()


def test_export_last_no_subagents(db, tmp_path) -> None:
    args = _args(last=2, no_subagents=True, output=str(tmp_path))
    assert run(args, db) == 0

    bundle = _bundle(tmp_path)
    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["counts"] == {"roots": 2, "subagents": 0, "total": 2}
    assert not (bundle / "transcript" / "subagents").exists()


def test_export_single_with_subagents_uses_bundle(db, tmp_path) -> None:
    args = _args(session_id="ses_001", with_subagents=True, output=str(tmp_path))
    assert run(args, db) == 0

    bundle = _bundle(tmp_path)
    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["selection"]["rule"] == "session"
    assert metadata["selection"]["with_subagents"] is True
    assert metadata["counts"] == {"roots": 1, "subagents": 1, "total": 2}


def test_export_project_and_json_layout(db, tmp_path) -> None:
    args = _args(project="proj_001", format="json", output=str(tmp_path))
    assert run(args, db) == 0

    bundle = _bundle(tmp_path)
    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["selection"]["rule"] == "project"
    assert metadata["counts"]["total"] == 2
    json_files = list((bundle / "transcript").glob("*.json")) + list(
        (bundle / "transcript" / "subagents").glob("*.json")
    )
    assert len(json_files) == 2
    for path in json_files:
        assert json.loads(path.read_text(encoding="utf-8"))["format"] == "opencode-db-export"


def test_export_all_and_no_matches(db, tmp_path, capsys) -> None:
    assert run(_args(all=True, output=str(tmp_path)), db) == 0
    bundle = _bundle(tmp_path)
    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["counts"]["total"] == 4

    capsys.readouterr()
    assert run(_args(project="proj_missing", output=str(tmp_path)), db) == 1
    out = capsys.readouterr().out
    assert "No sessions" in out or "не попала" in out


def test_export_bulk_validation(db, tmp_path, capsys) -> None:
    assert run(_args(last=0, output=str(tmp_path)), db) == 1
    assert "last" in capsys.readouterr().out
    assert run(_args(last=1, session_id="ses_001", output=str(tmp_path)), db) == 1
    out = capsys.readouterr().out
    assert "mode" in out or "режим" in out
    assert run(_args(since="not-a-date", output=str(tmp_path)), db) == 1
    assert "since" in capsys.readouterr().out


def test_root_selection_includes_orphans_and_excludes_children(db) -> None:
    from opencode_db.store import open_store

    db.execute(
        "INSERT INTO session (id, title, time_created, time_updated, parent_id) "
        "VALUES (?, ?, ?, ?, ?)",
        ("ses_orphan_bulk", "Orphan", 10, 10, "ses_missing"),
    )
    db.commit()
    store = open_store(db)
    roots = store.get_root_session_ids(10)
    assert "ses_orphan_bulk" in roots
    assert "ses_001" in roots
    assert "ses_002" not in roots
    assert store.get_descendant_ids("ses_001") == ["ses_002"]


def test_bulk_export_sanitizes_index_and_metadata(db, tmp_path) -> None:
    secret = "sk-proj-" + "A" * 32
    db.execute("UPDATE session SET title = ? WHERE id = ?", (f"Key {secret}", "ses_001"))
    db.commit()

    assert run(_args(last=2, sanitize=True, output=str(tmp_path)), db) == 0
    bundle = _bundle(tmp_path)
    index = (bundle / "index.md").read_text(encoding="utf-8")
    metadata = (bundle / "metadata.json").read_text(encoding="utf-8")
    assert secret not in index
    assert secret not in metadata
    assert "[REDACTED]" in index
