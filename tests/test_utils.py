from datetime import UTC, datetime

from utils import (
    format_cost,
    format_tokens,
    format_ts,
    format_ts_short,
    parse_time_spec,
    parse_ts,
    summarize_val,
)


class TestTimestamps:
    def test_parse_ts_converts_ms_to_datetime(self) -> None:
        dt = parse_ts(1700000000000)
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None

    def test_parse_ts_zero(self) -> None:
        dt = parse_ts(0)
        assert dt == datetime(1970, 1, 1, tzinfo=UTC)

    def test_format_ts_returns_string(self) -> None:
        result = format_ts(1700000000000)
        assert isinstance(result, str)
        assert "2023" in result or "2024" in result or "2025" in result

    def test_format_ts_with_custom_format(self) -> None:
        result = format_ts(1700000000000, "%Y")
        assert len(result) == 4
        assert result.isdigit()

    def test_format_ts_none_raises(self) -> None:
        import pytest

        with pytest.raises(TypeError):
            format_ts(None)

    def test_format_ts_short_no_spaces(self) -> None:
        result = format_ts_short(1700000000000)
        assert " " not in result


class TestSummarizeVal:
    def test_short_string_unchanged(self) -> None:
        assert summarize_val("hello", 10) == "hello"

    def test_long_string_truncated(self) -> None:
        long_str = "a" * 100
        result = summarize_val(long_str, 20)
        assert len(result) == 23
        assert result.endswith("...")

    def test_non_string_converted(self) -> None:
        assert summarize_val(42, 10) == "42"
        assert summarize_val(None, 10) == "None"

    def test_exact_length(self) -> None:
        result = summarize_val("a" * 10, 10)
        assert len(result) == 10
        assert result == "a" * 10


class TestParseTimeSpec:
    def test_30_days(self) -> None:
        result = parse_time_spec("30d")
        assert result is not None
        assert isinstance(result, datetime)

    def test_6_months(self) -> None:
        result = parse_time_spec("6m")
        assert result is not None

    def test_1_year(self) -> None:
        result = parse_time_spec("1y")
        assert result is not None

    def test_days_full_word(self) -> None:
        result = parse_time_spec("7days")
        assert result is not None

    def test_empty_string(self) -> None:
        assert parse_time_spec("") is None

    def test_none(self) -> None:
        assert parse_time_spec(None) is None

    def test_invalid_spec(self) -> None:
        assert parse_time_spec("abc") is None

    def test_case_insensitive(self) -> None:
        import time as _time

        ref = datetime.now(UTC)
        _time.sleep(0.01)
        d1 = parse_time_spec("30D")
        d2 = parse_time_spec("30d")
        assert d1 is not None and d2 is not None
        assert abs((d1 - ref).total_seconds() - (d2 - ref).total_seconds()) < 0.1


class TestFormatCost:
    def test_none(self) -> None:
        assert format_cost(None) == "—"

    def test_very_small(self) -> None:
        assert format_cost(0.001) == "$0.0010"

    def test_medium(self) -> None:
        assert format_cost(0.05) == "$0.050"

    def test_large(self) -> None:
        assert format_cost(1.5) == "$1.50"

    def test_zero(self) -> None:
        assert format_cost(0) == "$0.0000"


class TestFormatTokens:
    def test_none(self) -> None:
        assert format_tokens(None) == "—"

    def test_zero(self) -> None:
        assert format_tokens(0) == "0"

    def test_thousands(self) -> None:
        assert " " in format_tokens(1500) or "\u202f" in format_tokens(1500)

    def test_millions(self) -> None:
        result = format_tokens(1_500_000)
        assert any(c in result for c in (" ", "\u202f", ","))

    def test_float_converted(self) -> None:
        result = format_tokens(1000.5)
        assert " " in result or "\u202f" in result
