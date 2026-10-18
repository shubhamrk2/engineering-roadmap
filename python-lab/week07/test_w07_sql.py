"""Week 7 tests. Do not edit. Every test seeds a fresh in-memory SQLite database, runs YOUR SQL, and
compares the rows. Run:  pytest week07 -q

Tested with Python 3.14, SQLite 3.50 (needs SQLite 3.25 or newer for window functions).
"""
import sqlite3

import pytest

import w07_sql as w

SEED = """
PRAGMA foreign_keys = ON;
CREATE TABLE sites (id TEXT PRIMARY KEY, city TEXT NOT NULL, capacity INTEGER NOT NULL CHECK (capacity > 0));
CREATE TABLE employees (id TEXT PRIMARY KEY, name TEXT NOT NULL, site_id TEXT REFERENCES sites(id),
                        manager_id TEXT REFERENCES employees(id), hired_on TEXT NOT NULL);
CREATE TABLE access_requests (
  id TEXT PRIMARY KEY,
  employee_id TEXT NOT NULL REFERENCES employees(id),
  site_id TEXT NOT NULL REFERENCES sites(id),
  starts_on TEXT NOT NULL, ends_on TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  reason TEXT);
CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT NOT NULL);
CREATE TABLE chunks (id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id),
                     position INTEGER NOT NULL, body TEXT NOT NULL);
INSERT INTO sites VALUES ('BLR-01','Bengaluru',500),('BLR-02','Bengaluru',200),('HYD-01','Hyderabad',300),('PUN-01','Pune',100);
INSERT INTO employees VALUES
 ('e-901','Meera','BLR-01',NULL,'2019-04-01'), ('e-902','Asha','BLR-01','e-901','2021-07-15'),
 ('e-903','Ravi','HYD-01','e-901','2022-01-10'), ('e-904','Kiran','BLR-02','e-902','2023-03-20'),
 ('e-905','Neha',NULL,'e-902','2024-09-02');
INSERT INTO access_requests VALUES
 ('req-1','e-902','HYD-01','2026-11-02','2026-11-06','approved','project kickoff'),
 ('req-2','e-902','BLR-02','2026-11-09','2026-11-09','pending',NULL),
 ('req-3','e-903','BLR-01','2026-11-10','2026-11-12','approved','training'),
 ('req-4','e-903','BLR-01','2026-12-01','2026-12-05','rejected','training'),
 ('req-5','e-904','HYD-01','2026-11-16','2026-11-20','pending','audit'),
 ('req-6','e-904','BLR-01','2026-11-23','2026-11-23','approved',NULL),
 ('req-7','e-901','HYD-01','2026-12-07','2026-12-08','pending','site visit');
INSERT INTO documents VALUES (1,'Badge policy'),(2,'Visitor guide'),(3,'Empty draft');
INSERT INTO chunks VALUES (1,1,0,'Badges expire after 90 days'),(2,1,1,'Managers approve requests'),
                          (3,2,0,'Visitors need an escort');
"""


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.executescript(SEED)
    yield c
    c.close()


def rows(con, sql, params=()):
    assert isinstance(sql, str) and sql.strip(), "your function must return a non-empty SQL string"
    return con.execute(sql, params).fetchall()


def test_ex01_pending_requests(con):
    assert rows(con, w.q_pending_requests()) == [("req-2",), ("req-5",), ("req-7",)]


def test_ex02_sites_with_min_capacity(con):
    # one ? placeholder: the minimum capacity. Rows are (id, capacity), largest capacity first.
    sql = w.q_sites_with_min_capacity()
    assert "?" in sql, "use a ? placeholder, do not paste the number into the string"
    assert rows(con, sql, (200,)) == [("BLR-01", 500), ("HYD-01", 300), ("BLR-02", 200)]
    assert rows(con, sql, (301,)) == [("BLR-01", 500)]


def test_ex03_employees_without_site(con):
    assert rows(con, w.q_employees_without_site()) == [("Neha",)]


def test_ex04_requests_with_employee_names(con):
    got = rows(con, w.q_requests_with_employee_names())
    assert len(got) == 7
    assert got[0] == ("req-1", "Asha") and got[2] == ("req-3", "Ravi") and got[6] == ("req-7", "Meera")


def test_ex05_request_counts_include_zero(con):
    assert rows(con, w.q_request_counts_per_employee()) == [
        ("Asha", 2), ("Kiran", 2), ("Meera", 1), ("Neha", 0), ("Ravi", 2)]


def test_ex06_sites_without_employees(con):
    assert rows(con, w.q_sites_without_employees()) == [("PUN-01",)]


def test_ex07_busy_sites_having(con):
    # sites with at least 2 requests that are NOT rejected: (site_id, n), ordered by site_id
    assert rows(con, w.q_busy_sites()) == [("BLR-01", 2), ("HYD-01", 3)]


def test_ex08_employees_with_an_approved_request(con):
    assert rows(con, w.q_employees_with_approved_request()) == [("Asha",), ("Kiran",), ("Ravi",)]


def test_ex09_cte_above_average_requesters(con):
    sql = w.q_above_average_requesters()
    assert sql.lstrip().lower().startswith("with"), "this exercise must use a CTE (WITH ...)"
    # employees whose request count is above the average count per requesting employee
    assert rows(con, sql) == [("Asha", 2), ("Kiran", 2), ("Ravi", 2)]


def test_ex10_latest_request_per_employee_window(con):
    sql = w.q_latest_request_per_employee()
    assert "over" in sql.lower(), "this exercise must use a window function (OVER ...)"
    assert rows(con, sql) == [("e-901", "req-7"), ("e-902", "req-2"), ("e-903", "req-4"), ("e-904", "req-6")]


def test_ex11_days_since_previous_request(con):
    sql = w.q_days_since_previous_request()
    assert "lag" in sql.lower()
    # only requests that HAVE a previous one for the same employee; days between the two starts_on dates
    assert rows(con, sql) == [("req-2", 7), ("req-4", 21), ("req-6", 7)]


def test_ex12_documents_with_chunk_counts(con):
    assert rows(con, w.q_documents_with_chunk_counts()) == [
        ("Badge policy", 2), ("Empty draft", 0), ("Visitor guide", 1)]


def test_ex13_union_of_places(con):
    # every distinct site id mentioned by employees OR by requests, as one column, sorted
    assert rows(con, w.q_sites_mentioned()) == [("BLR-01",), ("BLR-02",), ("HYD-01",)]


def test_ex14_not_in_null_trap(con):
    # sites that have no request. Must still be correct when a request row has a NULL site (we add one).
    con.execute("PRAGMA foreign_keys = OFF")
    con.execute("CREATE TABLE loose (site_id TEXT)")
    con.execute("INSERT INTO loose VALUES ('BLR-01'), (NULL)")
    got = rows(con, w.q_sites_not_in_loose())
    assert got == [("BLR-02",), ("HYD-01",), ("PUN-01",)]


# ---- schema with constraints --------------------------------------------------------------------

@pytest.fixture
def badge_con(con):
    con.executescript(w.badges_schema())
    return con


def test_ex15_badges_table_accepts_a_valid_row_and_defaults(badge_con):
    badge_con.execute("INSERT INTO badges (id, employee_id, issued_on, expires_on) "
                      "VALUES ('b-1','e-902','2026-11-01','2027-02-01')")
    assert badge_con.execute("SELECT status FROM badges WHERE id='b-1'").fetchone() == ("active",)


@pytest.mark.parametrize("sql", [
    # unknown employee (foreign key)
    "INSERT INTO badges (id, employee_id, issued_on, expires_on) VALUES ('b-2','e-000','2026-11-01','2027-02-01')",
    # bad status (check)
    "INSERT INTO badges (id, employee_id, issued_on, expires_on, status) VALUES ('b-3','e-902','2026-11-01','2027-02-01','lost')",
    # expires before it is issued (check)
    "INSERT INTO badges (id, employee_id, issued_on, expires_on) VALUES ('b-4','e-902','2026-11-01','2026-10-01')",
    # missing issued_on (not null)
    "INSERT INTO badges (id, employee_id, expires_on) VALUES ('b-5','e-902','2027-02-01')",
])
def test_ex15_badges_table_rejects_bad_rows(badge_con, sql):
    with pytest.raises(sqlite3.IntegrityError):
        badge_con.execute(sql)


def test_ex15_badges_table_rejects_duplicates(badge_con):
    ins = "INSERT INTO badges (id, employee_id, issued_on, expires_on) VALUES (?, 'e-902', '2026-11-01', '2027-02-01')"
    badge_con.execute(ins, ("b-6",))
    with pytest.raises(sqlite3.IntegrityError):      # same primary key
        badge_con.execute(ins, ("b-6",))
    with pytest.raises(sqlite3.IntegrityError):      # same (employee_id, issued_on): UNIQUE
        badge_con.execute(ins, ("b-7",))
