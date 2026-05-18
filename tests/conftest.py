import json
import sqlite3
from datetime import UTC, datetime

import pytest

NOW_TS = int(datetime.now(UTC).timestamp() * 1000)
YESTERDAY_TS = NOW_TS - 86400000


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    _seed_data(conn)
    return conn


def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE session (
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

        CREATE TABLE message (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            time_created INTEGER,
            data TEXT
        );

        CREATE TABLE part (
            id TEXT PRIMARY KEY,
            message_id TEXT,
            session_id TEXT,
            time_created INTEGER,
            data TEXT
        );

        CREATE TABLE todo (
            session_id TEXT,
            content TEXT,
            status TEXT,
            priority TEXT,
            position INTEGER,
            time_created INTEGER,
            time_updated INTEGER
        );

        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT,
            name TEXT,
            time_created INTEGER,
            time_updated INTEGER
        );
    """)


def _seed_data(conn):
    conn.executemany(
        "INSERT INTO project (id, worktree, name, time_created, time_updated) VALUES (?, ?, ?, ?, ?)",
        [
            ("proj_001", "/home/user/proj1", "My Project", YESTERDAY_TS, NOW_TS),
            ("proj_002", "/home/user/proj2", None, YESTERDAY_TS, NOW_TS),
        ],
    )

    conn.executemany(
        "INSERT INTO session (id, title, model, agent, cost, tokens_input, tokens_output, tokens_reasoning, tokens_cache_read, tokens_cache_write, time_created, time_updated, project_id, parent_id, directory, version, summary_additions, summary_deletions, summary_files) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "ses_001",
                "First session",
                '{"id": "gpt-4"}',
                "assistant",
                0.05,
                100,
                200,
                50,
                10,
                20,
                YESTERDAY_TS,
                YESTERDAY_TS + 3600000,
                "proj_001",
                None,
                "/home/user/proj1",
                "v1",
                10,
                5,
                3,
            ),
            (
                "ses_002",
                "Second session",
                '{"id": "claude-3"}',
                None,
                0.03,
                80,
                150,
                30,
                None,
                None,
                NOW_TS,
                NOW_TS,
                "proj_001",
                "ses_001",
                "/home/user/proj1",
                None,
                0,
                0,
                0,
            ),
            (
                "ses_003",
                None,
                '{"id": "gpt-3.5-turbo"}',
                "explorer",
                0.01,
                50,
                100,
                10,
                0,
                0,
                YESTERDAY_TS,
                YESTERDAY_TS + 1800000,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            (
                "ses_004",
                "Orphan session",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                NOW_TS,
                NOW_TS,
                "proj_002",
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        ],
    )

    conn.executemany(
        "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
        [
            ("msg_001", "ses_001", YESTERDAY_TS + 1000, json.dumps({"role": "user"})),
            (
                "msg_002",
                "ses_001",
                YESTERDAY_TS + 2000,
                json.dumps({"role": "assistant", "agent": "assistant"}),
            ),
            ("msg_003", "ses_002", NOW_TS + 1000, json.dumps({"role": "user"})),
            ("msg_004", "ses_003", YESTERDAY_TS + 1000, json.dumps({"role": "user"})),
            ("msg_005", "ses_003", YESTERDAY_TS + 2000, json.dumps({"role": "assistant"})),
        ],
    )

    conn.executemany(
        "INSERT INTO part (id, message_id, session_id, time_created, data) VALUES (?, ?, ?, ?, ?)",
        [
            (
                "part_001",
                "msg_001",
                "ses_001",
                YESTERDAY_TS + 1000,
                json.dumps({"type": "text", "text": "Hello, how are you?"}),
            ),
            (
                "part_002",
                "msg_002",
                "ses_001",
                YESTERDAY_TS + 2000,
                json.dumps({"type": "text", "text": "I'm fine, thank you!"}),
            ),
            (
                "part_003",
                "msg_002",
                "ses_001",
                YESTERDAY_TS + 2000,
                json.dumps({"type": "reasoning", "text": "Let me think about this..."}),
            ),
            (
                "part_004",
                "msg_002",
                "ses_001",
                YESTERDAY_TS + 2000,
                json.dumps(
                    {
                        "type": "tool",
                        "tool": "read",
                        "state": {
                            "input": {"filePath": "/home/user/proj1/main.py"},
                            "output": "def hello():\n    print('hello')\n",
                            "status": "completed",
                            "tool": "read",
                        },
                    }
                ),
            ),
            (
                "part_005",
                "msg_003",
                "ses_002",
                NOW_TS + 1000,
                json.dumps({"type": "text", "text": "What's the weather?"}),
            ),
            (
                "part_006",
                "msg_004",
                "ses_003",
                YESTERDAY_TS + 1000,
                json.dumps({"type": "sound"}),
            ),
            (
                "part_007",
                "msg_005",
                "ses_003",
                YESTERDAY_TS + 2000,
                json.dumps(
                    {
                        "type": "tool",
                        "tool": "bash",
                        "state": {
                            "input": {"command": "ls -la"},
                            "output": "total 42\n-rw-r--r--   1 user  staff  1234 Jan 1 00:00 file.py",
                            "status": "completed",
                            "tool": "bash",
                        },
                    }
                ),
            ),
        ],
    )

    conn.executemany(
        "INSERT INTO todo (session_id, content, status, priority, position, time_created, time_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "ses_001",
                "Review code changes",
                "pending",
                "high",
                1,
                YESTERDAY_TS + 3000,
                YESTERDAY_TS + 3000,
            ),
            (
                "ses_001",
                "Write tests",
                "completed",
                "medium",
                2,
                YESTERDAY_TS + 4000,
                YESTERDAY_TS + 5000,
            ),
            ("ses_002", "Deploy to production", "pending", "high", 1, NOW_TS + 2000, NOW_TS + 2000),
        ],
    )

    conn.commit()


@pytest.fixture
def db_file(tmp_path):
    path = tmp_path / "test.db"
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    _seed_data(conn)
    conn.close()
    return str(path)


@pytest.fixture
def parser():
    from cli import build_parser

    return build_parser()
