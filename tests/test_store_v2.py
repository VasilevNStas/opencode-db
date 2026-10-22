import json
import sqlite3
from types import SimpleNamespace

import pytest

from opencode_db.schema import SchemaFamily
from opencode_db.store import open_store

TS = 1_790_000_000_000


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _v2_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT,
            name TEXT,
            time_created INTEGER,
            time_updated INTEGER
        );
        CREATE TABLE session_v2 (
            id TEXT PRIMARY KEY,
            title TEXT,
            model TEXT,
            agent TEXT,
            cost REAL,
            tokens_input INTEGER,
            tokens_output INTEGER,
            tokens_reasoning INTEGER,
            tokens_cache_read INTEGER,
            tokens_cache_write INTEGER,
            time_created INTEGER,
            time_updated INTEGER,
            project_id TEXT,
            parent_id TEXT,
            directory TEXT,
            version TEXT,
            summary_additions INTEGER,
            summary_deletions INTEGER,
            summary_files INTEGER
        );
        CREATE TABLE session_message (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            type TEXT,
            seq INTEGER,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT
        );
        CREATE TABLE migration (
            id TEXT PRIMARY KEY,
            time_completed INTEGER
        );
        INSERT INTO migration VALUES ('20261010180456_project_time_archived', 1);
        """
    )
    conn.execute(
        "INSERT INTO project VALUES (?, ?, ?, ?, ?)",
        ("proj_v2", "/tmp/v2", "V2 Project", TS, TS),
    )
    conn.execute(
        """
        INSERT INTO session_v2 (
            id, title, model, agent, cost, tokens_input, tokens_output,
            tokens_reasoning, tokens_cache_read, tokens_cache_write,
            time_created, time_updated, project_id, parent_id, directory,
            version, summary_additions, summary_deletions, summary_files
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ses_v2",
            "V2 Session",
            '{"id": "gpt-5"}',
            "build",
            0.25,
            1000,
            200,
            50,
            10,
            5,
            TS,
            TS + 60_000,
            "proj_v2",
            None,
            "/tmp/v2",
            "2.0.32",
            3,
            1,
            2,
        ),
    )

    messages = [
        (
            "msg_user",
            "user",
            1,
            {
                "type": "user",
                "text": "hello v2",
                "time": {"created": TS},
            },
        ),
        (
            "msg_assistant",
            "assistant",
            2,
            {
                "type": "assistant",
                "agent": "build",
                "model": {"id": "gpt-5", "providerID": "test"},
                "time": {"created": TS + 1},
                "content": [
                    {"type": "text", "text": "Hi from v2"},
                    {"type": "reasoning", "text": "thinking"},
                    {
                        "type": "tool",
                        "id": "tool_1",
                        "name": "todowrite",
                        "state": {
                            "status": "completed",
                            "input": {
                                "todos": [
                                    {"content": "V2 task", "status": "in_progress"},
                                    {"content": "Done task", "status": "completed"},
                                ]
                            },
                            "content": [{"type": "text", "text": "updated"}],
                        },
                    },
                ],
            },
        ),
        (
            "msg_switch",
            "agent-switched",
            3,
            {"type": "agent-switched", "agent": "build", "time": {"created": TS + 2}},
        ),
    ]
    for message_id, message_type, seq, data in messages:
        conn.execute(
            "INSERT INTO session_message VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                message_id,
                "ses_v2",
                message_type,
                seq,
                TS + seq,
                TS + seq,
                json.dumps(data),
            ),
        )
    return conn


@pytest.fixture
def v2db():
    return _v2_db()


def test_v2_store_reads_messages(v2db) -> None:
    store = open_store(v2db)
    assert store.schema.family is SchemaFamily.V2
    messages = store.get_messages("ses_v2")
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["parts"][0] == {"type": "text", "text": "Hi from v2"}
    assert messages[1]["parts"][1]["type"] == "reasoning"
    assert messages[1]["parts"][2]["tool"] == "todowrite"


def test_v2_store_todos(v2db) -> None:
    store = open_store(v2db)
    todos = store.get_session_todos("ses_v2")
    assert [todo["content"] for todo in todos] == ["V2 task", "Done task"]
    assert todos[0]["status"] == "in_progress"


def test_v2_list_and_stats(v2db, capsys) -> None:
    from opencode_db.commands import cmd_list, cmd_stats

    cmd_list.run(
        _ns(
            project=None,
            agent=None,
            model=None,
            sort="date",
            limit=10,
            offset=0,
            all=False,
            json=True,
        ),
        v2db,
    )
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["id"] == "ses_v2"
    assert listed[0]["messages"] == 2

    cmd_stats.run(_ns(json=True), v2db)
    stats = json.loads(capsys.readouterr().out)
    assert stats["sessions"] == 1
    assert stats["messages"] == 2
    assert stats["todos"] == 2


def test_v2_info_costs_projects_todos_search(v2db, capsys) -> None:
    from opencode_db.commands import cmd_costs, cmd_info, cmd_projects, cmd_search, cmd_todos

    cmd_info.run(_ns(session_id="ses_v2", json=True), v2db)
    info = json.loads(capsys.readouterr().out)
    assert info["title"] == "V2 Session"
    assert info["messages"] == 2
    assert info["todos"][0]["content"] == "V2 task"

    cmd_costs.run(_ns(session_id=None, project=None, total=True, json=True, limit=30), v2db)
    costs = json.loads(capsys.readouterr().out)
    assert costs["sessions"] == 1
    assert costs["cost"] == pytest.approx(0.25)

    cmd_projects.run(_ns(json=True), v2db)
    projects = json.loads(capsys.readouterr().out)
    assert projects[0]["id"] == "proj_v2"

    cmd_todos.run(_ns(session_id=None, status=None, limit=30, json=True), v2db)
    todos = json.loads(capsys.readouterr().out)
    assert len(todos) == 2

    cmd_search.run(_ns(query="hello", session=None, limit=10, json=True), v2db)
    results = json.loads(capsys.readouterr().out)
    assert results[0]["message_id"] == "msg_user"


def test_v2_view_export_tree(v2db, tmp_path, capsys) -> None:
    from opencode_db.commands import cmd_export, cmd_tree, cmd_view

    cmd_view.run(_ns(session_id="ses_v2", no_pager=True, raw=True), v2db)
    view = capsys.readouterr().out
    assert "Hi from v2" in view

    cmd_export.run(
        _ns(
            session_id="ses_v2",
            latest=False,
            output=str(tmp_path),
            force=True,
            note=None,
            full=False,
        ),
        v2db,
    )
    exported = capsys.readouterr().out
    assert "opencode-" in exported
    assert list(tmp_path.glob("opencode-*.md"))

    cmd_tree.run(_ns(session_id=None, project=None, depth=5), v2db)
    tree = capsys.readouterr().out
    assert "V2 Session" in tree


def test_v2_delete_is_refused(v2db, capsys) -> None:
    from opencode_db.commands import cmd_delete

    code = cmd_delete.run(
        _ns(session_id="ses_v2", dry_run=True, force=True, interactive=False),
        v2db,
    )
    assert code == 1
    assert "v2" in capsys.readouterr().out.lower()


def test_unknown_message_type_is_ignored(v2db) -> None:
    store = open_store(v2db)
    assert len(store.get_messages("ses_v2")) == 2


def test_v2_directories_and_global(v2db, capsys) -> None:
    from opencode_db.commands import cmd_directories

    v2db.execute(
        "INSERT INTO project VALUES (?, ?, ?, ?, ?)",
        ("global", "/", None, TS, TS),
    )
    v2db.execute(
        "INSERT INTO session_v2 (id, directory, project_id, time_created, time_updated) VALUES (?, ?, ?, ?, ?)",
        ("ses_global", "/tmp/v2-global", "global", TS, TS),
    )

    cmd_directories.run(
        _ns(
            missing=False,
            existing=False,
            project=None,
            sort="path",
            limit=50,
            no_check=True,
            json=True,
        ),
        v2db,
    )
    data = json.loads(capsys.readouterr().out)
    by_path = {item["path"]: item for item in data}
    assert "/" not in by_path
    assert by_path["/tmp/v2-global"]["is_global"] is True
    from opencode_db.i18n import _

    assert by_path["/tmp/v2-global"]["project"] == _("directories.global")
    assert by_path["/tmp/v2"]["project"] == "V2 Project"


def test_v2_directories_missing_filter(v2db, tmp_path, capsys) -> None:
    from opencode_db.commands import cmd_directories

    present = tmp_path / "present"
    present.mkdir()
    missing = tmp_path / "gone"
    v2db.execute(
        "INSERT INTO session_v2 (id, directory, project_id, time_created, time_updated) VALUES (?, ?, ?, ?, ?)",
        ("ses_present", str(present), "proj_v2", TS, TS),
    )
    v2db.execute(
        "INSERT INTO session_v2 (id, directory, project_id, time_created, time_updated) VALUES (?, ?, ?, ?, ?)",
        ("ses_missing", str(missing), "proj_v2", TS, TS),
    )

    cmd_directories.run(
        _ns(
            missing=True,
            existing=False,
            project=None,
            sort="path",
            limit=50,
            no_check=False,
            json=True,
        ),
        v2db,
    )
    data = json.loads(capsys.readouterr().out)
    paths = {item["path"] for item in data}
    assert str(missing) in paths
    assert str(present) not in paths
    assert all(item["exists"] is False for item in data)

    cmd_directories.run(
        _ns(
            missing=False,
            existing=True,
            project=None,
            sort="path",
            limit=50,
            no_check=False,
            json=True,
        ),
        v2db,
    )
    data = json.loads(capsys.readouterr().out)
    assert str(present) in {item["path"] for item in data}


def test_v2_projects_global_and_paths(v2db, capsys) -> None:
    from opencode_db.commands import cmd_projects

    v2db.execute(
        "INSERT INTO project VALUES (?, ?, ?, ?, ?)",
        ("global", "/", None, TS, TS),
    )
    cmd_projects.run(_ns(json=True, no_global=False, missing=False), v2db)
    data = json.loads(capsys.readouterr().out)
    by_id = {item["id"]: item for item in data}
    assert by_id["global"]["is_global"] is True
    assert by_id["global"]["path"] is None
    assert by_id["proj_v2"]["path"] == "/tmp/v2"
    assert by_id["proj_v2"]["name"] == "V2 Project"


def test_v2_missing_directory_cleanup_is_refused(v2db, capsys) -> None:
    from opencode_db.commands import cmd_delete

    code = cmd_delete.run(
        _ns(
            session_id=None,
            older_than=None,
            before=None,
            after=None,
            keep_last=None,
            project=None,
            dry_run=False,
            force=False,
            interactive=False,
            missing_directories=True,
            execute=True,
            backup=False,
            no_backup=True,
        ),
        v2db,
    )
    assert code == 1
    assert "v2" in capsys.readouterr().out.lower()


def test_v2_lossless_export_and_digest(v2db, tmp_path, capsys) -> None:
    from opencode_db.commands import cmd_digest, cmd_export

    v2db.execute(
        "INSERT INTO session_message VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "msg_comp",
            "ses_v2",
            "compaction",
            4,
            TS + 4,
            TS + 4,
            json.dumps(
                {
                    "type": "compaction",
                    "summary": "V2 compacted summary",
                    "agent": "compaction",
                    "tokens": {"total": 5},
                }
            ),
        ),
    )
    v2db.execute(
        "INSERT INTO session_message VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "msg_extra",
            "ses_v2",
            "assistant",
            5,
            TS + 5,
            TS + 5,
            json.dumps(
                {
                    "type": "assistant",
                    "agent": "build",
                    "time": {"created": TS + 5},
                    "content": [
                        {"type": "patch", "hash": "v2hash", "files": ["/tmp/v2.py"]},
                        {"type": "file", "filename": "v2.txt", "mime": "text/plain"},
                        {"type": "custom", "foo": "bar"},
                    ],
                }
            ),
        ),
    )
    v2db.commit()

    store = open_store(v2db)
    raw = store.get_raw_messages("ses_v2")
    assert any(message["type"] == "compaction" for message in raw)
    extra = next(message for message in raw if message["id"] == "msg_extra")
    assert extra["data"]["content"][2]["foo"] == "bar"

    args = _ns(
        session_id="ses_v2",
        latest=False,
        full=False,
        force=True,
        note=None,
        output=str(tmp_path),
        format="json",
    )
    assert cmd_export.run(args, v2db) == 0
    data = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert data["db_schema"] == "v2"
    exported = next(message for message in data["messages"] if message["id"] == "msg_extra")
    assert exported["data"]["content"][0]["hash"] == "v2hash"
    assert exported["data"]["content"][2]["foo"] == "bar"
    capsys.readouterr()

    assert cmd_digest.run(_ns(session_id="ses_v2", last=None, json=True), v2db) == 0
    digest = json.loads(capsys.readouterr().out)
    assert digest["count"] == 1
    assert digest["digests"][0]["text"] == "V2 compacted summary"
