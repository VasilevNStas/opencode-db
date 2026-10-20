import re

import pytest

from opencode_db.version import get_version


def test_get_version_returns_a_version() -> None:
    value = get_version()
    assert value == "unknown" or re.fullmatch(r"\d+\.\d+\.\d+(?:[.\-+][0-9A-Za-z.\-+]+)?", value)


def test_version_flag_prints_version(capsys) -> None:
    from opencode_db.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])

    assert exc.value.code == 0
    output = capsys.readouterr().out.strip()
    assert output == f"opencode-db {get_version()}"
