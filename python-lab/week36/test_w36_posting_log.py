"""Tests for w36_posting_log. Companies here are invented."""
from datetime import date

import pytest

from w36_posting_log import (COLUMNS, STATUSES, add_row, due_follow_ups, next_follow_up,
                             read_rows, response_rate, summarise)


def test_add_row_writes_header_once_and_fills_blanks(tmp_path):
    p = tmp_path / "jobs.csv"
    add_row(p, {"company": "ExampleCo", "role": "AI Integration Engineer"})
    add_row(p, {"company": "SampleLtd", "role": "GenAI Developer", "status": "applied"})
    lines = p.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(COLUMNS)
    assert len(lines) == 3
    rows = read_rows(p)
    assert rows[0]["status"] == "saved"
    assert rows[0]["url"] == ""
    assert rows[1]["status"] == "applied"


def test_add_row_rejects_unknown_column_and_writes_nothing(tmp_path):
    p = tmp_path / "jobs.csv"
    with pytest.raises(ValueError):
        add_row(p, {"company": "X", "salary": "?"})
    assert not p.exists()


def test_add_row_rejects_bad_status(tmp_path):
    p = tmp_path / "jobs.csv"
    with pytest.raises(ValueError):
        add_row(p, {"company": "X", "status": "hired"})
    assert not p.exists()


def test_add_row_quotes_commas_and_roundtrips(tmp_path):
    p = tmp_path / "jobs.csv"
    add_row(p, {"company": "A, B and C", "notes": 'said "maybe", later'})
    assert read_rows(p)[0]["company"] == "A, B and C"
    assert read_rows(p)[0]["notes"] == 'said "maybe", later'


def test_read_rows_missing_file_is_empty(tmp_path):
    assert read_rows(tmp_path / "nope.csv") == []


def test_next_follow_up_plain_weekday():
    assert next_follow_up(date(2027, 3, 1)) == date(2027, 3, 8)  # Mon + 7 = Mon


def test_next_follow_up_moves_weekend_to_monday():
    # Fri 5 Mar + 1 day = Sat 6 Mar -> Mon 8 Mar
    assert next_follow_up(date(2027, 3, 5), days=1) == date(2027, 3, 8)
    # Sat 6 Mar + 1 day = Sun 7 Mar -> Mon 8 Mar
    assert next_follow_up(date(2027, 3, 6), days=1) == date(2027, 3, 8)


def test_summarise_counts_every_status_in_order():
    rows = [{"status": "applied"}, {"status": "applied"}, {"status": "offer"}]
    s = summarise(rows)
    assert list(s)[: len(STATUSES)] == STATUSES
    assert s["applied"] == 2 and s["offer"] == 1 and s["rejected"] == 0
    assert s["total"] == 3
    assert "other" not in s


def test_summarise_counts_unknown_status_as_other():
    s = summarise([{"status": "applied"}, {"status": "weird"}, {}])
    assert s["other"] == 2 and s["total"] == 3


def test_due_follow_ups_filters_status_and_date_and_sorts():
    rows = [
        {"company": "B", "role": "r2", "status": "applied", "follow_up_on": "2027-03-10"},
        {"company": "A", "role": "r1", "status": "screen", "follow_up_on": "2027-03-08"},
        {"company": "C", "role": "r3", "status": "applied", "follow_up_on": "2027-03-20"},
        {"company": "D", "role": "r4", "status": "rejected", "follow_up_on": "2027-03-01"},
        {"company": "E", "role": "r5", "status": "applied", "follow_up_on": ""},
        {"company": "F", "role": "r6", "status": "applied", "follow_up_on": "soon"},
    ]
    assert due_follow_ups(rows, date(2027, 3, 10)) == [("A", "r1"), ("B", "r2")]


def test_due_follow_ups_includes_today():
    rows = [{"company": "A", "role": "r", "status": "applied", "follow_up_on": "2027-03-10"}]
    assert due_follow_ups(rows, date(2027, 3, 10)) == [("A", "r")]
    assert due_follow_ups(rows, date(2027, 3, 9)) == []


def test_response_rate():
    rows = [
        {"applied_on": "2027-03-01", "status": "rejected"},
        {"applied_on": "2027-03-01", "status": "interview"},
        {"applied_on": "2027-03-01", "status": "ghosted"},
        {"applied_on": "2027-03-01", "status": "applied"},
        {"applied_on": "", "status": "saved"},
    ]
    assert response_rate(rows) == 0.5


def test_response_rate_none_when_nothing_applied():
    assert response_rate([{"applied_on": "", "status": "saved"}]) is None
    assert response_rate([]) is None
