from opencode_db.runtime import MIN_PYTHON, check_python_version, format_version_error


class TestRuntime:
    def test_supported_versions_pass(self) -> None:
        assert check_python_version((3, 12, 0)) is None
        assert check_python_version((3, 13, 5)) is None
        assert check_python_version((4, 0, 0)) is None

    def test_old_version_returns_error(self) -> None:
        message = check_python_version((3, 9, 6))
        assert message is not None
        assert "3.12+" in message
        assert "3.9.6" in message

    def test_error_contains_remediation(self) -> None:
        message = format_version_error((3, 9, 6), "/usr/bin/python3")
        assert MIN_PYTHON == (3, 12)
        assert "/usr/bin/python3" in message
        assert "uv python install" in message
        assert "uv run" in message
