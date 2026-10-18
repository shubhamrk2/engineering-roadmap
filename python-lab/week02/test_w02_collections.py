import pytest

from w02_collections import (
    count_errors,
    group_by_site,
    parse_log_line,
    top_n,
    unique_in_order,
    word_counts,
)

SAMPLE = [
    "2026-10-18 09:01:12 ERROR payments Timeout calling gateway",
    "2026-10-18 09:01:15 INFO  payments Retry succeeded",
    "2026-10-18 09:02:03 ERROR auth Invalid token",
    "2026-10-18 09:02:09 ERROR payments Timeout calling gateway",
    "2026-10-18 09:03:00 WARN  auth Slow response",
]


def test_ex01_unique_in_order_basic():
    assert unique_in_order([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_ex01_unique_in_order_empty_and_strings():
    assert unique_in_order([]) == []
    assert unique_in_order(["b", "a", "b"]) == ["b", "a"]


def test_ex01_unique_in_order_does_not_change_the_input():
    original = [1, 1, 2]
    unique_in_order(original)
    assert original == [1, 1, 2]


def test_ex02_word_counts_ignores_case():
    assert word_counts("The the THE cat") == {"the": 3, "cat": 1}


def test_ex02_word_counts_empty():
    assert word_counts("") == {}
    assert word_counts("   ") == {}


def test_ex03_group_by_site():
    requests = [
        {"id": "req-1", "site": "BLR-01"},
        {"id": "req-2", "site": "HYD-01"},
        {"id": "req-3", "site": "BLR-01"},
    ]
    assert group_by_site(requests) == {"BLR-01": ["req-1", "req-3"], "HYD-01": ["req-2"]}


def test_ex03_group_by_site_empty():
    assert group_by_site([]) == {}


def test_ex04_parse_log_line_valid():
    assert parse_log_line("2026-10-18 09:01:12 ERROR payments Timeout calling gateway") == {
        "date": "2026-10-18",
        "time": "09:01:12",
        "level": "ERROR",
        "service": "payments",
        "message": "Timeout calling gateway",
    }


def test_ex04_parse_log_line_single_word_message():
    parsed = parse_log_line("2026-10-18 09:01:12 INFO auth ok")
    assert parsed["message"] == "ok"


def test_ex04_parse_log_line_extra_spaces_between_parts():
    parsed = parse_log_line("2026-10-18 09:01:15 INFO  payments Retry succeeded")
    assert parsed["level"] == "INFO"
    assert parsed["service"] == "payments"
    assert parsed["message"] == "Retry succeeded"


@pytest.mark.parametrize("bad", ["garbage", "", "   ", "2026-10-18 09:01:12 ERROR payments"])
def test_ex04_parse_log_line_malformed_is_none(bad):
    assert parse_log_line(bad) is None


def test_ex05_count_errors_sample():
    assert count_errors(SAMPLE) == {"payments": 2, "auth": 1}


def test_ex05_count_errors_empty_input():
    assert count_errors([]) == {}


def test_ex05_count_errors_skips_malformed_lines():
    lines = SAMPLE + ["garbage", "", "ERROR"]
    assert count_errors(lines) == {"payments": 2, "auth": 1}


def test_ex05_count_errors_ignores_other_levels():
    assert count_errors(["2026-10-18 09:00:00 INFO auth fine", "2026-10-18 09:00:01 WARN auth meh"]) == {}


def test_ex06_top_n_basic():
    assert top_n({"a": 2, "b": 5, "c": 2}, 2) == [("b", 5), ("a", 2)]


def test_ex06_top_n_ties_break_by_name():
    assert top_n({"b": 1, "a": 1, "c": 1}, 3) == [("a", 1), ("b", 1), ("c", 1)]


def test_ex06_top_n_edges():
    assert top_n({"a": 1}, 5) == [("a", 1)]
    assert top_n({"a": 1}, 0) == []
    assert top_n({}, 3) == []
