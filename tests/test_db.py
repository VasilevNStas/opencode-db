from db import (
    get_children_sessions,
    get_latest_session,
    get_message_count,
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
