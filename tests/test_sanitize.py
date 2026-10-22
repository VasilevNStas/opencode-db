import json

import pytest

from opencode_db.sanitize import redact, sanitize_obj

SECRETS = [
    "sk-proj-" + "A" * 32,
    "ghp_" + "B" * 24,
    "github_pat_" + "C" * 24,
    "xoxb-" + "D" * 12,
    "AIza" + "E" * 35,
    "AKIA" + "F" * 16,
    "eyJ" + "G" * 20 + "." + "H" * 20 + "." + "I" * 20,
    "Bearer " + "J" * 30,
    "-----BEGIN RSA PRIVATE KEY-----\nsecret\n-----END RSA PRIVATE KEY-----",
]


@pytest.mark.parametrize("secret", SECRETS)
def test_high_confidence_secret_is_redacted(secret) -> None:
    text = f"before\n{secret}\nafter"
    result = redact(text)
    assert "REDACTED" in result
    assert secret not in result
    assert "before" in result
    assert "after" in result


def test_short_examples_are_not_redacted() -> None:
    text = "sk-short ghp_short github_pat_short xoxb-short Bearer dev AKIA123 a.b.c"
    assert redact(text) == text


def test_free_text_unchanged() -> None:
    text = "Use sk- prefix, GitHub tokens start with ghp_, and Bearer is an auth scheme."
    assert redact(text) == text


def test_sanitize_obj_recurses() -> None:
    data = {
        "message": "token sk-proj-" + "A" * 32,
        "parts": [{"text": "Bearer " + "J" * 30}],
        "count": 3,
    }
    cleaned = sanitize_obj(data)
    assert "sk-proj-" not in json.dumps(cleaned)
    assert "J" * 30 not in json.dumps(cleaned)
    assert cleaned["count"] == 3


def _args(**kwargs):
    base = dict(
        session_id="ses_001",
        latest=False,
        last=None,
        since=None,
        project=None,
        all=False,
        with_subagents=False,
        no_subagents=False,
        full=False,
        force=True,
        note=None,
        format="md",
        sanitize=True,
    )
    base.update(kwargs)
    return type("Args", (), base)()


def _insert_secret(db):
    secret = "sk-proj-" + "A" * 32
    db.execute(
        "INSERT INTO message (id, session_id, time_created, data) VALUES (?, ?, ?, ?)",
        ("msg_secret", "ses_001", 10_000, json.dumps({"role": "user"})),
    )
    db.execute(
        "INSERT INTO part (id, message_id, session_id, time_created, data) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            "part_secret",
            "msg_secret",
            "ses_001",
            10_000,
            json.dumps({"type": "text", "text": f"my key {secret}"}),
        ),
    )
    db.commit()
    return secret


def test_markdown_export_sanitizes_without_db_change(db, tmp_path) -> None:
    from opencode_db.commands.cmd_export import run

    secret = _insert_secret(db)
    assert run(_args(output=str(tmp_path)), db) == 0
    content = next(tmp_path.glob("*.md")).read_text(encoding="utf-8")
    assert secret not in content
    assert "[REDACTED]" in content
    assert db.execute("SELECT COUNT(*) FROM part WHERE data LIKE ?", (f"%{secret}%",)).fetchone()[0] == 1


def test_json_export_sanitizes_without_db_change(db, tmp_path) -> None:
    from opencode_db.commands.cmd_export import run

    secret = _insert_secret(db)
    assert run(_args(format="json", output=str(tmp_path)), db) == 0
    content = next(tmp_path.glob("*.json")).read_text(encoding="utf-8")
    assert secret not in content
    assert "[REDACTED]" in content
    data = json.loads(content)
    assert any("REDACTED" in json.dumps(item) for item in data["messages"])
