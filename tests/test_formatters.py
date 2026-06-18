from formatters import format_part_to_md


class TestFormatPartToMd:
    def test_text_part(self):
        result = format_part_to_md({"type": "text", "text": "Hello world"})
        assert result == "Hello world"

    def test_text_part_strips_whitespace(self):
        result = format_part_to_md({"type": "text", "text": "  hello  "})
        assert result == "hello"

    def test_text_part_empty_returns_empty(self):
        result = format_part_to_md({"type": "text", "text": ""})
        assert result == ""

    def test_text_part_missing_text(self):
        result = format_part_to_md({"type": "text"})
        assert result == ""

    def test_reasoning_part(self):
        result = format_part_to_md({"type": "reasoning", "text": "Let me think..."})
        assert "Let me think..." in result
        assert "reasoning" in result.lower() or "💭" in result

    def test_reasoning_empty_returns_empty(self):
        result = format_part_to_md({"type": "reasoning", "text": "   "})
        assert result == ""

    def test_sound_part(self):
        result = format_part_to_md({"type": "sound"})
        assert result != ""

    def test_tool_read_part(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "read",
                "input": {"filePath": "/home/user/file.py"},
                "output": "content",
                "status": "completed",
            }
        )
        assert "read" in result
        assert "file.py" in result

    def test_tool_write_part(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "write",
                "input": {"filePath": "/home/user/new.py"},
                "output": "",
                "status": "completed",
            }
        )
        assert "write" in result

    def test_tool_edit_part(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "edit",
                "input": {"filePath": "/home/user/file.py"},
                "output": "",
                "status": "completed",
            }
        )
        assert "edit" in result

    def test_tool_glob_part(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "glob",
                "input": {"pattern": "**/*.py", "path": "/home/user"},
                "output": "",
                "status": "completed",
            }
        )
        assert "glob" in result
        assert "**/*.py" in result

    def test_tool_grep_part(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "grep",
                "input": {"pattern": "def hello"},
                "output": "def hello():\n    pass",
                "status": "completed",
            }
        )
        assert "grep" in result
        assert "def hello" in result

    def test_tool_custom_with_input_output(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "bash",
                "input": {"command": "ls -la"},
                "output": "total 42\n-rw-r--r-- 1 user staff 1234 Jan 1 00:00 file.py",
                "status": "completed",
            }
        )
        assert "bash" in result
        assert "ls -la" in result
        assert "total 42" in result

    def test_tool_error_status(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "bash",
                "input": {"command": "rm -rf /"},
                "output": "permission denied",
                "status": "error",
            }
        )
        assert "❌" in result

    def test_tool_running_status(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "bash",
                "input": {"command": "sleep 10"},
                "output": "",
                "status": "running",
            }
        )
        assert "⏳" in result

    def test_tool_no_output(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "bash",
                "input": {"command": "echo hi"},
                "output": "",
                "status": "completed",
            }
        )
        assert "echo hi" in result

    def test_full_mode_does_not_truncate_path(self):
        long_path = "/a/" + "very/" * 50 + "file.py"
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "read",
                "input": {"filePath": long_path},
                "output": "",
                "status": "completed",
            },
            full=True,
        )
        assert long_path in result
        assert "..." not in result

    def test_full_mode_shows_full_output(self):
        result = format_part_to_md(
            {
                "type": "tool",
                "tool": "bash",
                "input": {"command": "cat bigfile.txt"},
                "output": "line\n" * 500,
                "status": "completed",
            },
            full=True,
        )
        assert "line" in result
