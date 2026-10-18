"""Week 8 tests. Do not edit. Run:  pytest week08 -q

Everything runs against a fresh in-memory SQLite database. No network, no PostgreSQL needed.
Tested with Python 3.14 and SQLite 3.50.
"""
import sqlite3
from datetime import date

import pytest

import w08_repo as r
from w08_repo import AccessRequest, NotFoundError, NotPendingError, RequestRepository, Status


@pytest.fixture
def conn():
    c = r.connect(":memory:")
    c.executemany("INSERT INTO employees VALUES (?, ?)",
                  [("e-902", "Asha"), ("e-903", "Ravi"), ("e-904", "Kiran")])
    yield c
    c.close()


@pytest.fixture
def repo(conn):
    return RequestRepository(conn)


def seed(repo):
    a = repo.add("e-902", "HYD-01", date(2026, 11, 2), date(2026, 11, 6), "project kickoff")
    b = repo.add("e-902", "BLR-02", date(2026, 11, 9), date(2026, 11, 9))
    c = repo.add("e-903", "BLR-01", date(2026, 11, 10), date(2026, 11, 12), "training")
    return a, b, c


def count(conn, table, where="1=1"):
    return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]


# ---- ex01 row mapping ---------------------------------------------------------------------------

def test_ex01_row_to_request_converts_types(conn):
    conn.execute("INSERT INTO access_requests (employee_id, site_id, starts_on, ends_on, status, reason) "
                 "VALUES ('e-902','HYD-01','2026-11-02','2026-11-06','approved','kickoff')")
    row = conn.execute("SELECT * FROM access_requests").fetchone()
    req = r.row_to_request(row)
    assert req == AccessRequest(1, "e-902", "HYD-01", date(2026, 11, 2), date(2026, 11, 6), Status.APPROVED, "kickoff")
    assert isinstance(req.starts_on, date) and isinstance(req.status, Status)


def test_ex01_row_to_request_keeps_none(conn):
    conn.execute("INSERT INTO access_requests (employee_id, site_id, starts_on, ends_on) "
                 "VALUES ('e-902','HYD-01','2026-11-02','2026-11-06')")
    req = r.row_to_request(conn.execute("SELECT * FROM access_requests").fetchone())
    assert req.reason is None and req.status is Status.PENDING


# ---- ex02 transaction ---------------------------------------------------------------------------

def test_ex02_transaction_commits_on_success(conn):
    with r.transaction(conn):
        conn.execute("INSERT INTO employees VALUES ('e-905', 'Neha')")
    assert not conn.in_transaction
    assert count(conn, "employees", "id = 'e-905'") == 1


def test_ex02_transaction_rolls_back_and_reraises(conn):
    with pytest.raises(ZeroDivisionError):
        with r.transaction(conn):
            conn.execute("INSERT INTO employees VALUES ('e-905', 'Neha')")
            1 / 0
    assert not conn.in_transaction
    assert count(conn, "employees", "id = 'e-905'") == 0


def test_ex02_transaction_rolls_back_on_database_error(conn):
    with pytest.raises(sqlite3.IntegrityError):
        with r.transaction(conn):
            conn.execute("INSERT INTO employees VALUES ('e-905', 'Neha')")
            conn.execute("INSERT INTO employees VALUES ('e-902', 'Duplicate id')")
    assert count(conn, "employees", "id = 'e-905'") == 0


def test_ex02_transaction_is_reusable_after_failure(conn):
    with pytest.raises(RuntimeError):
        with r.transaction(conn):
            raise RuntimeError("boom")
    with r.transaction(conn):
        conn.execute("INSERT INTO employees VALUES ('e-905', 'Neha')")
    assert count(conn, "employees", "id = 'e-905'") == 1


# ---- ex03 add / ex04 get ------------------------------------------------------------------------

def test_ex03_add_returns_request_with_generated_id(repo):
    a, b, _ = seed(repo)
    assert (a.id, b.id) == (1, 2)
    assert a.status is Status.PENDING and a.reason == "project kickoff" and b.reason is None
    assert a.starts_on == date(2026, 11, 2)


def test_ex03_add_unknown_employee_is_rejected_by_the_database(repo, conn):
    with pytest.raises(sqlite3.IntegrityError):
        repo.add("e-000", "HYD-01", date(2026, 11, 2), date(2026, 11, 3))
    assert count(conn, "access_requests") == 0


def test_ex03_add_rejects_end_before_start(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.add("e-902", "HYD-01", date(2026, 11, 5), date(2026, 11, 3))


def test_ex04_get_found_and_missing(repo):
    a, _, _ = seed(repo)
    assert repo.get(a.id) == a
    assert repo.get(999) is None


# ---- ex05 list / ex06 search: parameters and injection -------------------------------------------

def test_ex05_list_for_employee_and_status_filter(repo):
    a, b, c = seed(repo)
    assert [x.id for x in repo.list_for_employee("e-902")] == [1, 2]
    assert [x.id for x in repo.list_for_employee("e-903")] == [3]
    assert repo.list_for_employee("e-904") == []
    assert [x.id for x in repo.list_for_employee("e-902", Status.PENDING)] == [1, 2]
    assert repo.list_for_employee("e-902", Status.APPROVED) == []


def test_ex05_list_for_employee_resists_sql_injection(repo):
    seed(repo)
    evil = "e-902' OR '1'='1"
    assert repo.list_for_employee(evil) == []
    assert repo.list_for_employee("x' OR 1=1 --") == []


def test_ex06_search_reason_contains_and_none_reason_skipped(repo):
    seed(repo)
    assert [x.id for x in repo.search_reason("train")] == [3]
    assert [x.id for x in repo.search_reason("KICK")] == [1]
    assert repo.search_reason("nothing like this") == []


def test_ex06_search_reason_resists_sql_injection(repo):
    seed(repo)
    assert repo.search_reason("zzz' OR 1=1 --") == []
    assert repo.search_reason("%' OR '1'='1") == []


def test_ex06_search_reason_handles_apostrophes(repo):
    repo.add("e-902", "HYD-01", date(2026, 11, 2), date(2026, 11, 3), "O'Brien site visit")
    assert [x.id for x in repo.search_reason("O'Brien")] == [1]


# ---- ex07 approve: atomic ------------------------------------------------------------------------

def test_ex07_approve_updates_status_and_writes_audit_row(repo, conn):
    a, _, _ = seed(repo)
    done = repo.approve(a.id, "e-901")
    assert done.status is Status.APPROVED and done.id == a.id
    assert repo.get(a.id).status is Status.APPROVED
    rows = conn.execute("SELECT actor, action, request_id FROM audit_log").fetchall()
    assert [tuple(x) for x in rows] == [("e-901", "approve", a.id)]
    assert not conn.in_transaction


def test_ex07_approve_missing_request(repo, conn):
    seed(repo)
    with pytest.raises(NotFoundError):
        repo.approve(999, "e-901")
    assert count(conn, "audit_log") == 0 and not conn.in_transaction


def test_ex07_approve_twice_is_not_pending(repo, conn):
    a, _, _ = seed(repo)
    repo.approve(a.id, "e-901")
    with pytest.raises(NotPendingError):
        repo.approve(a.id, "e-901")
    assert count(conn, "audit_log") == 1       # still only the first audit row


def test_ex07_approve_rolls_back_the_update_when_the_audit_insert_fails(repo, conn):
    a, _, _ = seed(repo)
    conn.execute("DROP TABLE audit_log")        # make step 3 fail
    with pytest.raises(sqlite3.OperationalError):
        repo.approve(a.id, "e-901")
    assert repo.get(a.id).status is Status.PENDING, "the UPDATE must be rolled back with the failed audit insert"
    assert not conn.in_transaction


def test_ex07_approve_leaves_connection_usable_after_failure(repo):
    a, b, _ = seed(repo)
    with pytest.raises(NotFoundError):
        repo.approve(999, "e-901")
    assert repo.approve(b.id, "e-901").status is Status.APPROVED


# ---- ex08 approve_many: all or nothing -------------------------------------------------------------

def test_ex08_approve_many_all_succeed(repo, conn):
    a, b, c = seed(repo)
    done = repo.approve_many([a.id, c.id], "e-901")
    assert [x.id for x in done] == [a.id, c.id] and all(x.status is Status.APPROVED for x in done)
    assert count(conn, "audit_log") == 2
    assert repo.get(b.id).status is Status.PENDING


def test_ex08_approve_many_is_all_or_nothing_on_missing_id(repo, conn):
    a, b, c = seed(repo)
    with pytest.raises(NotFoundError):
        repo.approve_many([a.id, c.id, 999], "e-901")
    assert [repo.get(x.id).status for x in (a, b, c)] == [Status.PENDING] * 3
    assert count(conn, "audit_log") == 0 and not conn.in_transaction


def test_ex08_approve_many_is_all_or_nothing_on_not_pending(repo, conn):
    a, b, c = seed(repo)
    repo.approve(b.id, "e-901")
    with pytest.raises(NotPendingError):
        repo.approve_many([a.id, b.id], "e-901")
    assert repo.get(a.id).status is Status.PENDING       # a was earlier in the list; it must NOT stick
    assert count(conn, "audit_log") == 1                  # only the audit row from approving b above


# ---- ex09 group by ------------------------------------------------------------------------------

def test_ex09_counts_by_status(repo):
    a, b, c = seed(repo)
    assert repo.counts_by_status() == {"pending": 3}
    repo.approve(a.id, "e-901")
    assert repo.counts_by_status() == {"pending": 2, "approved": 1}
    assert RequestRepository(r.connect()).counts_by_status() == {}
