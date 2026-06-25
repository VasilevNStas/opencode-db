import argparse
from unittest.mock import patch


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _count_sessions(db) -> int:
    return db.execute("SELECT COUNT(*) FROM session").fetchone()[0]


def _count_messages(db) -> int:
    return db.execute("SELECT COUNT(*) FROM message").fetchone()[0]


def _count_parts(db) -> int:
    return db.execute("SELECT COUNT(*) FROM part").fetchone()[0]


class TestListCommand:
    def test_list_default(self, db):
        from cmd_list import run

        args = _ns(
            limit=25,
            offset=0,
            project=None,
            agent=None,
            model=None,
            sort="date",
            json=False,
            all=False,
        )
        assert run(args, db) == 0

    def test_list_json(self, db) -> None:
        from cmd_list import run

        args = _ns(
            limit=10,
            offset=0,
            project=None,
            agent=None,
            model=None,
            sort="date",
            json=True,
            all=False,
        )
        assert run(args, db) == 0

    def test_list_by_project(self, db) -> None:
        from cmd_list import run

        args = _ns(
            limit=25,
            offset=0,
            project="proj_001",
            agent=None,
            model=None,
            sort="date",
            json=False,
            all=False,
        )
        assert run(args, db) == 0

    def test_list_by_agent(self, db) -> None:
        from cmd_list import run

        args = _ns(
            limit=25,
            offset=0,
            project=None,
            agent="assistant",
            model=None,
            sort="date",
            json=False,
            all=False,
        )
        assert run(args, db) == 0

    def test_list_all(self, db) -> None:
        from cmd_list import run

        args = _ns(
            limit=25,
            offset=0,
            project=None,
            agent=None,
            model=None,
            sort="date",
            json=False,
            all=True,
        )
        assert run(args, db) == 0

    def test_list_cost_sort(self, db) -> None:
        from cmd_list import run

        args = _ns(
            limit=25,
            offset=0,
            project=None,
            agent=None,
            model=None,
            sort="cost",
            json=False,
            all=False,
        )
        assert run(args, db) == 0

    def test_list_empty_result(self, db) -> None:
        from cmd_list import run

        args = _ns(
            limit=25,
            offset=0,
            project="proj_nonexistent",
            agent=None,
            model=None,
            sort="date",
            json=False,
            all=False,
        )
        assert run(args, db) == 0


class TestInfoCommand:
    def test_info_by_id(self, db) -> None:
        from cmd_info import run

        args = _ns(session_id="ses_001", json=False)
        assert run(args, db) == 0

    def test_info_json(self, db) -> None:
        from cmd_info import run

        args = _ns(session_id="ses_001", json=True)
        assert run(args, db) == 0

    def test_info_no_todos(self, db) -> None:
        from cmd_info import run

        args = _ns(session_id="ses_004", json=False)
        assert run(args, db) == 0

    def test_info_with_parent(self, db) -> None:
        from cmd_info import run

        args = _ns(session_id="ses_002", json=True)
        assert run(args, db) == 0


class TestCostsCommand:
    def test_costs_list_default(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id=None, project=None, total=False, json=False, limit=30)
        assert run(args, db) == 0

    def test_costs_list_json(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id=None, project=None, total=False, json=True, limit=10)
        assert run(args, db) == 0

    def test_costs_by_session(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id="ses_001", total=False, project=None, json=False, limit=30)
        assert run(args, db) == 0

    def test_costs_session_json(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id="ses_001", total=False, project=None, json=True, limit=30)
        assert run(args, db) == 0

    def test_costs_total(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id=None, total=True, project=None, json=False, limit=30)
        assert run(args, db) == 0

    def test_costs_total_json(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id=None, total=True, project=None, json=True, limit=30)
        assert run(args, db) == 0

    def test_costs_by_project(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id=None, total=False, project="proj_001", json=False, limit=30)
        assert run(args, db) == 0

    def test_costs_by_session_with_cache(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id="ses_001", total=False, project=None, json=False, limit=30)
        assert run(args, db) == 0

    def test_costs_session_no_cache(self, db) -> None:
        from cmd_costs import run

        args = _ns(session_id="ses_002", total=False, project=None, json=False, limit=30)
        assert run(args, db) == 0


class TestDeleteCommand:
    def test_delete_dry_run(self, db) -> None:
        from cmd_delete import run

        args = _ns(session_id="ses_004", dry_run=True, force=False)
        assert run(args, db) == 0

    def test_delete_with_force(self, db) -> None:
        from cmd_delete import run

        args = _ns(session_id="ses_004", dry_run=False, force=True)
        result = run(args, db)
        assert result == 0
        remaining = db.execute("SELECT COUNT(*) FROM session").fetchone()[0]
        assert remaining == 3

    def test_delete_canceled(self, db) -> None:
        from cmd_delete import run

        args = _ns(session_id="ses_004", dry_run=False, force=False)
        with patch("cmd_delete.confirm", return_value=False):
            assert run(args, db) == 0


class TestHelpCommand:
    def test_help_general(self, db) -> None:
        from cmd_help import run

        args = _ns(topic=None, json=False)
        assert run(args, db) == 0

    def test_help_json(self, db) -> None:
        from cmd_help import run

        args = _ns(topic=None, json=True)
        assert run(args, db) == 0

    def test_help_topic(self, db) -> None:
        from cmd_help import run

        args = _ns(topic="list", json=False)
        assert run(args, db) == 0

    def test_help_unknown_topic(self, db) -> None:
        from cmd_help import run

        args = _ns(topic="nonexistent", json=False)
        assert run(args, db) == 1


class TestSearchCommand:
    def test_search_found(self, db) -> None:
        from cmd_search import run

        args = _ns(query="hello", session=None, limit=30, json=False)
        assert run(args, db) == 0

    def test_search_not_found(self, db) -> None:
        from cmd_search import run

        args = _ns(query="zzzzz_notfound", session=None, limit=30, json=False)
        assert run(args, db) == 0

    def test_search_json(self, db) -> None:
        from cmd_search import run

        args = _ns(query="weather", session=None, limit=30, json=True)
        assert run(args, db) == 0

    def test_search_by_session(self, db) -> None:
        from cmd_search import run

        args = _ns(query="hello", session="ses_001", limit=30, json=False)
        assert run(args, db) == 0


class TestTreeCommand:
    def test_tree_all(self, db) -> None:
        from cmd_tree import run

        args = _ns(session_id=None, project=None, depth=5)
        assert run(args, db) == 0

    def test_tree_by_session(self, db) -> None:
        from cmd_tree import run

        args = _ns(session_id="ses_001", project=None, depth=3)
        assert run(args, db) == 0

    def test_tree_by_project(self, db) -> None:
        from cmd_tree import run

        args = _ns(session_id=None, project="proj_001", depth=5)
        assert run(args, db) == 0


class TestProjectsCommand:
    def test_projects_default(self, db) -> None:
        from cmd_projects import run

        args = _ns(json=False)
        assert run(args, db) == 0

    def test_projects_json(self, db) -> None:
        from cmd_projects import run

        args = _ns(json=True)
        assert run(args, db) == 0


class TestStatsCommand:
    def test_stats_default(self, db) -> None:
        from cmd_stats import run

        args = _ns(json=False)
        assert run(args, db) == 0

    def test_stats_json(self, db) -> None:
        from cmd_stats import run

        args = _ns(json=True)
        assert run(args, db) == 0


class TestTodosCommand:
    def test_todos_all(self, db) -> None:
        from cmd_todos import run

        args = _ns(session_id=None, status=None, limit=30, json=False)
        assert run(args, db) == 0

    def test_todos_json(self, db) -> None:
        from cmd_todos import run

        args = _ns(session_id=None, status=None, limit=30, json=True)
        assert run(args, db) == 0

    def test_todos_by_session(self, db) -> None:
        from cmd_todos import run

        args = _ns(session_id="ses_001", status=None, limit=30, json=False)
        assert run(args, db) == 0

    def test_todos_by_status(self, db) -> None:
        from cmd_todos import run

        args = _ns(session_id=None, status="pending", limit=30, json=False)
        assert run(args, db) == 0

    def test_todos_none(self, db) -> None:
        from cmd_todos import run

        args = _ns(session_id="ses_004", status=None, limit=30, json=False)
        assert run(args, db) == 0


class TestVacuumCommand:
    def test_vacuum_canceled(self, db) -> None:
        from cmd_vacuum import run

        args = _ns(force=False)
        with patch("cmd_vacuum.confirm", return_value=False):
            assert run(args, db) == 0

    def test_vacuum_with_force(self, db_file) -> None:
        import sqlite3
        from unittest.mock import patch

        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row

        from cmd_vacuum import run

        args = _ns(force=True)
        with patch("cmd_vacuum.OPENCODE_DB", db_file):
            assert run(args, conn) == 0

        conn.close()


class TestExportCommand:
    def test_export_by_session(self, db, tmp_path) -> None:
        from cmd_export import run

        args = _ns(
            session_id="ses_001",
            latest=False,
            full=False,
            force=False,
            note=None,
            output=str(tmp_path),
        )
        assert run(args, db) == 0
        files = list(tmp_path.glob("*.md"))
        assert len(files) >= 1

    def test_export_latest(self, db, tmp_path) -> None:
        from cmd_export import run

        args = _ns(
            session_id=None,
            latest=True,
            full=False,
            force=False,
            note=None,
            output=str(tmp_path),
        )
        assert run(args, db) == 0
        files = list(tmp_path.glob("*.md"))
        assert len(files) >= 1

    def test_export_full(self, db, tmp_path) -> None:
        from cmd_export import run

        args = _ns(
            session_id="ses_001",
            latest=False,
            full=True,
            force=True,
            note=None,
            output=str(tmp_path),
        )
        assert run(args, db) == 0


class TestPruneCommand:
    def test_prune_filter_required(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than=None, keep_last=None, project=None, dry_run=False, force=False)
        assert run(args, db) == 1

    def test_prune_dry_run_older_than(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than="30d", keep_last=None, project=None, dry_run=True, force=True)
        assert run(args, db) == 0

    def test_prune_dry_run_keep_last(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than=None, keep_last=2, project=None, dry_run=True, force=True)
        assert run(args, db) == 0
        assert _count_sessions(db) == 4

    def test_prune_force_older_than(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than="1d", keep_last=None, project=None, dry_run=False, force=True)
        result = run(args, db)
        assert result == 0
        remaining = _count_sessions(db)
        assert remaining < 4

    def test_prune_by_project(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than=None, keep_last=None, project="proj_002", dry_run=True, force=True)
        assert run(args, db) == 0

    def test_prune_bad_spec(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than="invalid", keep_last=None, project=None, dry_run=False, force=True)
        assert run(args, db) == 1

    def test_prune_canceled(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than="30d", keep_last=None, project=None, dry_run=False, force=False)
        with patch("cmd_delete.confirm", return_value=False):
            assert run(args, db) == 0
        assert _count_sessions(db) == 4

    def test_prune_deletes_messages_and_parts(self, db) -> None:
        from cmd_prune import run

        total_msg = _count_messages(db)
        total_parts = _count_parts(db)
        assert total_msg > 0
        assert total_parts > 0

        args = _ns(older_than="1d", keep_last=None, project=None, dry_run=False, force=True)
        assert run(args, db) == 0

        assert _count_messages(db) < total_msg
        assert _count_parts(db) < total_parts

    def test_prune_keep_last_preserves_recent(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than=None, keep_last=10, project=None, dry_run=True, force=True)
        assert run(args, db) == 0

    def test_prune_none_to_delete(self, db) -> None:
        from cmd_prune import run

        args = _ns(older_than="100y", keep_last=None, project=None, dry_run=False, force=True)
        assert run(args, db) == 0
        assert _count_sessions(db) == 4


class TestViewCommand:
    def test_view_by_id(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id="ses_001", latest=False, no_pager=True, raw=True)
        assert run(args, db) == 0

    def test_view_latest(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id=None, latest=True, no_pager=True, raw=True)
        assert run(args, db) == 0

    def test_view_interactive(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id=None, latest=False, no_pager=True, raw=True)
        with patch("builtins.input", return_value="1"):
            assert run(args, db) == 0

    def test_view_interactive_abort(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id=None, latest=False, no_pager=True, raw=True)
        with patch("builtins.input", return_value=""):
            assert run(args, db) == 1

    def test_view_interactive_bad_number(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id=None, latest=False, no_pager=True, raw=True)
        with patch("builtins.input", side_effect=["99", "1"]):
            assert run(args, db) == 0

    def test_view_not_found(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id="nonexistent", latest=False, no_pager=True, raw=True)
        assert run(args, db) == 1

    def test_view_unknown_session_prefix(self, db) -> None:
        from cmd_view import run

        args = _ns(session_id="zzz", latest=False, no_pager=True, raw=True)
        assert run(args, db) == 1

    def test_view_output_contains_session_data(self, db) -> None:
        from cmd_view import _format_session, _init_styles

        info = {
            "id": "ses_001",
            "title": "First session",
            "model": '{"id": "gpt-4"}',
            "agent": "assistant",
            "cost": 0.05,
            "tokens_input": 100,
            "tokens_output": 200,
            "tokens_reasoning": 50,
            "tokens_cache_read": 10,
            "tokens_cache_write": 20,
            "time_created": 1000000,
            "time_updated": 1003600,
            "project_id": "proj_001",
            "parent_id": None,
            "directory": "/home/user/proj1",
            "version": "v1",
            "summary_additions": 10,
            "summary_deletions": 5,
            "summary_files": 3,
        }
        from db import get_messages

        messages = get_messages(db, "ses_001")
        sty = _init_styles(raw=True)
        text = _format_session(db, info, messages, sty)

        assert "ses_001" in text
        assert "First session" in text
        assert "gpt-4" in text
        assert "Hello, how are you?" in text
        assert "I'm fine, thank you!" in text

    def test_format_part_ansi_text(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi({"type": "text", "text": "Hello world"}, sty)
        assert result == "Hello world"

    def test_format_part_ansi_reasoning(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi({"type": "reasoning", "text": "Let me think..."}, sty)
        assert "Let me think..." in result

    def test_format_part_ansi_sound(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi({"type": "sound"}, sty)
        assert result

    def test_format_part_ansi_tool_read(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi(
            {
                "type": "tool",
                "tool": "read",
                "input": {"filePath": "/path/to/file.py"},
                "output": "content",
                "status": "completed",
            },
            sty,
        )
        assert "read" in result
        assert "/path/to/file.py" in result

    def test_format_part_ansi_tool_bash(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi(
            {
                "type": "tool",
                "tool": "bash",
                "input": {"command": "ls -la"},
                "output": "total 42\nfile.py",
                "status": "completed",
            },
            sty,
        )
        assert "bash" in result

    def test_format_part_ansi_empty_text(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi({"type": "text", "text": ""}, sty)
        assert result == ""

    def test_format_part_ansi_empty_reasoning(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi({"type": "reasoning", "text": ""}, sty)
        assert result == ""

    def test_format_part_ansi_unknown_type(self) -> None:
        from cmd_view import _format_part_ansi, _init_styles

        sty = _init_styles(raw=True)
        result = _format_part_ansi({"type": "unknown_type"}, sty)
        assert result == ""

    def test_init_styles_raw_disables_ansi(self) -> None:
        from cmd_view import _init_styles

        sty = _init_styles(raw=True)
        assert sty == {}

    def test_view_no_messages_session(self, db) -> None:
        from cmd_view import _format_session, _init_styles

        info = {
            "id": "ses_empty",
            "title": None,
            "model": None,
            "agent": None,
            "cost": None,
            "tokens_input": None,
            "tokens_output": None,
            "tokens_reasoning": None,
            "tokens_cache_read": None,
            "tokens_cache_write": None,
            "time_created": 1000000,
            "time_updated": 1003600,
            "project_id": None,
            "parent_id": None,
            "directory": None,
            "version": None,
            "summary_additions": 0,
            "summary_deletions": 0,
            "summary_files": 0,
        }
        sty = _init_styles(raw=True)
        text = _format_session(db, info, [], sty)
        assert "конец сессии" in text or "end of session" in text
