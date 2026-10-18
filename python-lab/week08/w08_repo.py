"""Week 8: a repository layer over a database, with parameterised queries and transactions.

You write this against Python's built-in `sqlite3` (the DB-API). The ideas are identical with psycopg 3
and PostgreSQL: the placeholder changes from `?` to `%s`, and nothing else about the design changes.

Run:  pytest week08 -q          (one exercise: pytest week08 -k ex05)

THE RULES OF THIS EXERCISE
  * Every value that comes from outside goes in through a PLACEHOLDER (`?`) and a parameter tuple.
    Never build SQL with an f-string, `+`, `%` or `.format()` from a value. The tests try SQL injection.
  * SQL lives ONLY in this file's repository class (the "repository pattern"): callers never see SQL.
  * Money-like operations that touch two tables happen in ONE transaction: all or nothing.

Given to you (do not change): SCHEMA, Status, AccessRequest, NotFoundError, NotPendingError, connect().
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from enum import Enum
import sqlite3
from typing import Iterator, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS access_requests (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id TEXT NOT NULL REFERENCES employees(id),
  site_id     TEXT NOT NULL,
  starts_on   TEXT NOT NULL,
  ends_on     TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  reason      TEXT,
  CHECK (ends_on >= starts_on)
);
CREATE TABLE IF NOT EXISTS audit_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  actor      TEXT NOT NULL,
  action     TEXT NOT NULL,
  request_id INTEGER NOT NULL
);
"""


class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class AccessRequest:
    id: int
    employee_id: str
    site_id: str
    starts_on: date
    ends_on: date
    status: Status
    reason: Optional[str]


class NotFoundError(Exception):
    """No request with that id."""


class NotPendingError(Exception):
    """The request exists but is not pending, so it cannot be approved."""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Given. Autocommit mode (isolation_level=None) so YOU control BEGIN / COMMIT / ROLLBACK explicitly,
    foreign keys on, and rows you can index by column name (row["id"])."""
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


# ---------------------------------------------------------------------------------------------------

def row_to_request(row: sqlite3.Row) -> AccessRequest:
    """ex01. Map one database row to an AccessRequest.
    starts_on / ends_on are stored as 'YYYY-MM-DD' text: convert with date.fromisoformat.
    status is stored as text: convert to the Status enum. reason may be None and must stay None."""
    raise NotImplementedError


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """ex02. A context manager for one transaction:
        with transaction(conn):
            ...statements...
    Run BEGIN first. If the block finishes normally, COMMIT. If it raises ANY exception, ROLLBACK and
    re-raise the same exception. Yield the connection. (Hint: try / except BaseException / else.)"""
    raise NotImplementedError
    yield conn  # pragma: no cover  (makes this function a generator; leave it)


class RequestRepository:
    """All SQL for access requests lives here. Callers pass Python values and get AccessRequest objects."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add(self, employee_id: str, site_id: str, starts_on: date, ends_on: date,
            reason: Optional[str] = None) -> AccessRequest:
        """ex03. INSERT one row (status stays at its default, 'pending'), using placeholders and passing
        dates as isoformat() strings. Return the new AccessRequest, including the generated id
        (cursor.lastrowid). A single INSERT is already atomic: no explicit transaction needed.
        Unknown employee_id -> let sqlite3.IntegrityError propagate."""
        raise NotImplementedError

    def get(self, request_id: int) -> Optional[AccessRequest]:
        """ex04. One request by id, or None if it does not exist."""
        raise NotImplementedError

    def list_for_employee(self, employee_id: str, status: Optional[Status] = None) -> list[AccessRequest]:
        """ex05. Requests of one employee ordered by id; if `status` is given, only that status.
        employee_id is user input. A value such as  e-902' OR '1'='1  must match NOTHING."""
        raise NotImplementedError

    def search_reason(self, text: str) -> list[AccessRequest]:
        """ex06. Requests whose reason CONTAINS `text` (case-insensitive is fine: LIKE already is, for ASCII).
        Ordered by id. Build the pattern '%' + text + '%' in PYTHON and pass it as ONE parameter.
        `text` is user input: zzz' OR 1=1 --   must match NOTHING, and  O'Brien  must work, not crash."""
        raise NotImplementedError

    def approve(self, request_id: int, approver_id: str) -> AccessRequest:
        """ex07. Approve a PENDING request and write an audit row, atomically (use transaction()):
            1. UPDATE access_requests SET status='approved' WHERE id = ? AND status = 'pending'
            2. if that changed 0 rows: raise NotFoundError (no such id) or NotPendingError (exists, not pending)
            3. INSERT INTO audit_log (actor, action, request_id) VALUES (approver_id, 'approve', request_id)
        If ANY step fails, nothing is kept: the status must still be 'pending' and there is no audit row.
        Return the updated AccessRequest."""
        raise NotImplementedError

    def approve_many(self, request_ids: list[int], approver_id: str) -> list[AccessRequest]:
        """ex08. Approve several requests ALL OR NOTHING in ONE transaction. If any id is missing or not
        pending, raise that error and leave EVERY request (including ones earlier in the list) untouched,
        with no audit rows. Hint: write a private helper that does the work for one id WITHOUT opening its
        own transaction (SQLite does not allow BEGIN inside BEGIN), and call it inside a single transaction()."""
        raise NotImplementedError

    def counts_by_status(self) -> dict[str, int]:
        """ex09. {status: number of requests}, only statuses that occur. GROUP BY."""
        raise NotImplementedError
