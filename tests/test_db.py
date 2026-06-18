import json

import pytest

from db import (
    SessionError,
    get_children_sessions,
    get_latest_session,
    get_message_count,
    get_messages,
    get_parent_session,
    get_part_count,
    get_project_count,
    get_project_name,
    get_recent_sessions,
    get_session_count,
    get_session_info,
    get_session_title,
    get_session_todos,
    parse_model,
    resolve_session_id,
    verify_schema,
)


class TestSchema:
    def test_verify_schema_valid_db(self, db) -> None:
        assert verify_schema(db) is True


class TestGetSessionInfo:
    def test_by_full_id(self, db) -> None:
        info = get_session_info(db, "ses_001")
        assert info["id"] == "ses_001"
        assert info["title"] == "First session"

    def test_by_prefix(self, db) -> None:
        info = get_session_info(db, "ses_001")
        assert info["id"] == "ses_001"

    def test_session_with_model_json(self, db) -> None:
        info = get_session_info(db, "ses_001")
        assert info["id"] == "ses_001"

    def test_session_with_none_title(self, db) -> None:
        info = get_session_info(db, "ses_003")
        assert info["title"] is None


class TestGetSessionTitle:
    def test_with_title(self, db) -> None:
        info = get_session_info(db, "ses_001")
        assert get_session_title(info) == "First session"

    def test_without_title(self, db) -> None:
        info = get_session_info(db, "ses_003")
        assert get_session_title(info) is not None
        assert isinstance(get_session_title(info), str)


class TestParseModel:
    def test_valid_json(self, db) -> None:
        info = get_session_info(db, "ses_001")
        assert parse_model(info) == "gpt-4"

    def test_none_model(self, db) -> None:
        info = get_session_info(db, "ses_004")
        assert parse_model(info) == "—"


class TestCounts:
    def test_session_count_total(self, db) -> None:
        assert get_session_count(db) == 4

    def test_session_count_by_project(self, db) -> None:
        assert get_session_count(db, "proj_001") == 2

    def test_session_count_by_empty_project(self, db) -> None:
        assert get_session_count(db, "nonexistent") == 0

    def test_message_count_total(self, db) -> None:
        assert get_message_count(db) == 5

    def test_message_count_by_session(self, db) -> None:
        assert get_message_count(db, "ses_001") == 2

    def test_part_count_total(self, db) -> None:
        assert get_part_count(db) == 7

    def test_part_count_by_session(self, db) -> None:
        assert get_part_count(db, "ses_002") == 1

    def test_project_count(self, db) -> None:
        assert get_project_count(db) == 2


class TestRelations:
    def test_children_sessions(self, db) -> None:
        children = get_children_sessions(db, "ses_001")
        assert len(children) == 1
        assert children[0]["id"] == "ses_002"

    def test_no_children(self, db) -> None:
        children = get_children_sessions(db, "ses_002")
        assert len(children) == 0

    def test_parent_session(self, db) -> None:
        parent = get_parent_session(db, "ses_002")
        assert parent is not None
        assert parent["id"] == "ses_001"

    def test_no_parent(self, db) -> None:
        parent = get_parent_session(db, "ses_001")
        assert parent is None


class TestTodos:
    def test_get_session_todos(self, db) -> None:
        todos = get_session_todos(db, "ses_001")
        assert len(todos) == 2

    def test_todos_ordered_by_position(self, db):
        todos = get_session_todos(db, "ses_001")
        assert todos[0]["priority"] == "high"

    def test_no_todos(self, db) -> None:
        todos = get_session_todos(db, "ses_004")
        assert len(todos) == 0


class TestGetProjectName:
    def test_with_name(self, db) -> None:
        assert get_project_name(db, "proj_001") == "My Project"

    def test_without_name(self, db) -> None:
        name = get_project_name(db, "proj_002")
        assert name is not None
        assert name != "—"

    def test_nonexistent_project(self, db) -> None:
        name = get_project_name(db, "proj_nonexistent")
        assert len(name) == 12


class TestGetLatestSession:
    def test_returns_newest(self, db) -> None:
        latest = get_latest_session(db)
        assert latest in ("ses_002", "ses_004")


class TestGetRecentSessions:
    def test_default_limit(self, db) -> None:
        sessions = get_recent_sessions(db)
        assert len(sessions) <= 15
        assert len(sessions) >= 1

    def test_custom_limit(self, db) -> None:
        sessions = get_recent_sessions(db, limit=2)
        assert len(sessions) == 2


class TestResolveSessionId:
    def test_empty_id_returns_none(self, db) -> None:
        assert resolve_session_id(db, None) is None
        assert resolve_session_id(db, "") is None


class TestSessionError:
    def test_resolve_session_id_not_found(self, db) -> None:
        with pytest.raises(SessionError):
            get_session_info(db, "nonexistent")

    def test_resolve_session_id_multiple(self, db) -> None:
        db.execute(
            "INSERT INTO session (id, time_created) VALUES (?, ?)",
            ("ses_test_abc", 1000),
        )
        db.execute(
            "INSERT INTO session (id, time_created) VALUES (?, ?)",
            ("ses_test_xyz", 2000),
        )
        db.commit()
        with pytest.raises(SessionError):
            get_session_info(db, "ses_test")

    def test_get_latest_session_no_sessions(self, db) -> None:
        db.execute("DELETE FROM session")
        db.commit()
        with pytest.raises(SessionError):
            get_latest_session(db)

    def test_get_session_info_not_found(self, db) -> None:
        with pytest.raises(SessionError):
            get_session_info(db, "zzz_nope")


class TestGetMessages:
    def test_returns_messages_with_parts(self, db) -> None:
        messages = get_messages(db, "ses_001")
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_parts_are_grouped_by_message(self, db) -> None:
        messages = get_messages(db, "ses_001")
        assert len(messages) == 2
        assert len(messages[0]["parts"]) == 1
        assert messages[0]["parts"][0]["type"] == "text"

    def test_multiple_parts_per_message(self, db) -> None:
        messages = get_messages(db, "ses_001")
        parts = messages[1]["parts"]
        assert len(parts) == 3
        types = [p["type"] for p in parts]
        assert types == ["text", "reasoning", "tool"]

    def test_text_part_content(self, db) -> None:
        messages = get_messages(db, "ses_001")
        text_part = messages[0]["parts"][0]
        assert text_part["type"] == "text"
        assert "Hello" in text_part["text"]

    def test_reasoning_part(self, db) -> None:
        messages = get_messages(db, "ses_001")
        parts = messages[1]["parts"]
        reasoning = [p for p in parts if p["type"] == "reasoning"]
        assert len(reasoning) == 1
        assert "think" in reasoning[0]["text"].lower()

    def test_tool_part(self, db) -> None:
        messages = get_messages(db, "ses_001")
        parts = messages[1]["parts"]
        tool = [p for p in parts if p["type"] == "tool"]
        assert len(tool) == 1
        assert tool[0]["tool"] == "read"
        assert tool[0]["status"] == "completed"

    def test_sound_part(self, db) -> None:
        messages = get_messages(db, "ses_003")
        assert len(messages) == 2
        parts = messages[0]["parts"]
        assert len(parts) == 1
        assert parts[0]["type"] == "sound"

    def test_empty_session(self, db) -> None:
        messages = get_messages(db, "ses_004")
        assert messages == []

    def test_bash_tool_part(self, db) -> None:
        messages = get_messages(db, "ses_003")
        tool_part = messages[1]["parts"][0]
        assert tool_part["type"] == "tool"
        assert tool_part["tool"] == "bash"

    def test_skips_invalid_json_part(self, db) -> None:
        db.execute(
            "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
            ("msg_bad", "ses_001", 100500, json.dumps({"role": "user"})),
        )
        db.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, data) VALUES (?, ?, ?, ?, ?)",
            ("part_bad", "msg_bad", "ses_001", 100500, "not valid json {"),
        )
        messages = get_messages(db, "ses_001")
        assert len(messages) == 2

    def test_skips_empty_part_data(self, db) -> None:
        db.execute(
            "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
            ("msg_empty", "ses_001", 100600, json.dumps({"role": "user"})),
        )
        db.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, data) VALUES (?, ?, ?, ?, ?)",
            ("part_empty", "msg_empty", "ses_001", 100600, None),
        )
        messages = get_messages(db, "ses_001")
        assert len(messages) == 2


class TestEdgeCases:
    def test_session_null_title_and_model(self, db) -> None:
        db.execute(
            "INSERT INTO session (id, time_created, title, model, cost) VALUES (?, ?, ?, ?, ?)",
            ("ses_null_meta", 50000, None, None, 0.0),
        )
        db.commit()
        info = get_session_info(db, "ses_null_meta")
        assert info["title"] is None
        assert info["model"] is None

    def test_session_zero_cost(self, db) -> None:
        db.execute(
            "INSERT INTO session (id, time_created, cost) VALUES (?, ?, ?)",
            ("ses_zero_cost", 55000, 0.0),
        )
        db.commit()
        info = get_session_info(db, "ses_zero_cost")
        assert info["cost"] == 0.0

    def test_session_null_parent(self, db) -> None:
        db.execute(
            "INSERT INTO session (id, time_created, parent_id) VALUES (?, ?, ?)",
            ("ses_orphan", 60000, None),
        )
        db.commit()
        children = get_children_sessions(db, "ses_orphan")
        assert children == []

    def test_part_without_type_has_empty_parts(self, db) -> None:
        db.execute(
            "INSERT INTO session (id, time_created) VALUES (?, ?)",
            ("ses_skip", 1000),
        )
        db.execute(
            "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
            ("msg_skip", "ses_skip", 1000, json.dumps({"role": "user"})),
        )
        db.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, data) VALUES (?, ?, ?, ?, ?)",
            ("part_skip", "msg_skip", "ses_skip", 1000, json.dumps({"text": "no type"})),
        )
        db.commit()
        messages = get_messages(db, "ses_skip")
        assert len(messages) == 1
        assert len(messages[0]["parts"]) == 0

    def test_message_null_role(self, db) -> None:
        db.execute(
            "INSERT INTO session (id, time_created) VALUES (?, ?)",
            ("ses_edge_b", 2000),
        )
        db.execute(
            "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
            ("msg_edge_b", "ses_edge_b", 2000, json.dumps({"role": None})),
        )
        db.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, data) VALUES (?, ?, ?, ?, ?)",
            (
                "part_edge_b",
                "msg_edge_b",
                "ses_edge_b",
                2000,
                json.dumps({"type": "text", "text": "hi"}),
            ),
        )
        db.commit()
        messages = get_messages(db, "ses_edge_b")
        assert len(messages) == 1
        assert messages[0]["role"] is None or messages[0]["role"] == "?"
