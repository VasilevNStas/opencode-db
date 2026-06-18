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
