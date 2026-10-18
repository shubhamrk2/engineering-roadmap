import json

import pytest

from w03_files import ConfigError, analyze_file, load_json, read_lines, safe_int, write_report


def test_ex01_read_lines_strips_and_skips_blank(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\n\n  b  \n   \nc", encoding="utf-8")
    assert read_lines(f) == ["a", "b", "c"]


def test_ex01_read_lines_empty_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    assert read_lines(f) == []


def test_ex01_read_lines_missing_file_propagates(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_lines(tmp_path / "nope.txt")


def test_ex01_read_lines_accepts_string_path(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text("x\n", encoding="utf-8")
    assert read_lines(str(f)) == ["x"]


def test_ex02_load_json_valid(tmp_path):
    f = tmp_path / "ok.json"
    f.write_text('{"retries": 3, "sites": ["BLR-01"]}', encoding="utf-8")
    assert load_json(f) == {"retries": 3, "sites": ["BLR-01"]}


def test_ex02_load_json_missing_file_is_config_error(tmp_path):
    with pytest.raises(ConfigError) as err:
        load_json(tmp_path / "missing.json")
    assert "missing.json" in str(err.value)


def test_ex02_load_json_invalid_is_config_error(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ConfigError) as err:
        load_json(f)
    assert "bad.json" in str(err.value)


@pytest.mark.parametrize("value, default, expected", [
    ("12", None, 12),
    (" 7 ", None, 7),
    ("12x", None, None),
    ("", None, None),
    (None, None, None),
    (None, -1, -1),
    ("abc", 0, 0),
    (5, None, 5),
])
def test_ex03_safe_int(value, default, expected):
    assert safe_int(value, default) == expected


def test_ex03_safe_int_default_is_optional():
    assert safe_int("nope") is None


def test_ex04_write_report_round_trips(tmp_path):
    out = tmp_path / "r.json"
    write_report({"payments": 2, "auth": 1}, out)
    assert json.loads(out.read_text(encoding="utf-8")) == {"payments": 2, "auth": 1}


def test_ex04_write_report_sorted_and_indented(tmp_path):
    out = tmp_path / "r.json"
    write_report({"payments": 2, "auth": 1}, out)
    text = out.read_text(encoding="utf-8")
    assert text.index('"auth"') < text.index('"payments"')
    assert '\n  "auth"' in text


def test_ex04_write_report_creates_parent_folder(tmp_path):
    out = tmp_path / "deep" / "er" / "r.json"
    write_report({"a": 1}, out)
    assert out.exists()


LOG = (
    "2026-10-18 09:01:12 ERROR payments Timeout calling gateway\n"
    "2026-10-18 09:01:15 INFO  payments Retry succeeded\n"
    "\n"
    "garbage\n"
    "2026-10-18 09:02:03 ERROR auth Invalid token\n"
    "2026-10-18 09:02:09 ERROR payments Timeout calling gateway\n"
)


def test_ex05_analyze_file_returns_and_writes(tmp_path):
    src = tmp_path / "app.log"
    src.write_text(LOG, encoding="utf-8")
    out = tmp_path / "report.json"
    result = analyze_file(src, out)
    expected = {"errors": {"payments": 2, "auth": 1}, "skipped": 1}
    assert result == expected
    assert json.loads(out.read_text(encoding="utf-8")) == expected


def test_ex05_analyze_file_empty_log(tmp_path):
    src = tmp_path / "empty.log"
    src.write_text("", encoding="utf-8")
    result = analyze_file(src, tmp_path / "r.json")
    assert result == {"errors": {}, "skipped": 0}


def test_ex05_analyze_file_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        analyze_file(tmp_path / "nope.log", tmp_path / "r.json")
