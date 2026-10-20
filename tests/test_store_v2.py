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
