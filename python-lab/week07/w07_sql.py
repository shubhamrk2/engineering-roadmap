"""Week 7: SQL. Each function RETURNS A SQL STRING; the tests run it against an in-memory SQLite
database that they seed, and compare the rows. Replace each `raise NotImplementedError` with your SQL.

Run:  pytest week07 -q          (one exercise: pytest week07 -k ex05)

THE TABLES (the tests create these; you only write queries)

    sites(id TEXT PK, city TEXT, capacity INTEGER)
    employees(id TEXT PK, name TEXT, site_id TEXT -> sites.id (may be NULL), manager_id TEXT -> employees.id,
              hired_on TEXT 'YYYY-MM-DD')
    access_requests(id TEXT PK, employee_id -> employees.id, site_id -> sites.id,
                    starts_on TEXT, ends_on TEXT, status TEXT 'pending'|'approved'|'rejected', reason TEXT (may be NULL))
    documents(id INTEGER PK, title TEXT)
    chunks(id INTEGER PK, document_id -> documents.id, position INTEGER, body TEXT)

Seed data, so you can reason about the expected rows:
    employees: e-901 Meera (BLR-01), e-902 Asha (BLR-01), e-903 Ravi (HYD-01), e-904 Kiran (BLR-02), e-905 Neha (no site)
    requests : req-1..req-7, two or fewer per employee; Neha (e-905) has none; PUN-01 has no employees and no requests.

Dialect: SQLite. Dates are ISO text; julianday('2026-11-09') gives a number you can subtract.
ORDER BY matters: without it, row order is not guaranteed, and the tests compare lists.
Predict the row count BEFORE you run a join. If your prediction was wrong, that is the lesson.
"""


def q_pending_requests() -> str:
    """ex01. Ids of requests whose status is 'pending', ordered by id. One column: id."""
    raise NotImplementedError


def q_sites_with_min_capacity() -> str:
    """ex02. Sites whose capacity is AT LEAST a number you pass in. Use ONE `?` placeholder (no pasting the
    number into the string). Columns: id, capacity. Largest capacity first."""
    raise NotImplementedError


def q_employees_without_site() -> str:
    """ex03. Names of employees who have no site (site_id is NULL). One column: name.
    Hint: `site_id = NULL` is never true. Use IS NULL."""
    raise NotImplementedError


def q_requests_with_employee_names() -> str:
    """ex04. INNER JOIN. Columns: request id, employee name. One row per request, ordered by request id."""
    raise NotImplementedError


def q_request_counts_per_employee() -> str:
    """ex05. LEFT JOIN + GROUP BY. Columns: name, n (number of requests). EVERY employee appears, including
    the one with zero requests (n = 0). Ordered by name. Hint: COUNT(r.id), not COUNT(*)."""
    raise NotImplementedError


def q_sites_without_employees() -> str:
    """ex06. Ids of sites that no employee has as their site. One column: id. Ordered by id.
    Use a LEFT JOIN ... IS NULL, or NOT EXISTS."""
    raise NotImplementedError


def q_busy_sites() -> str:
    """ex07. WHERE vs HAVING. Sites with at least 2 requests whose status is NOT 'rejected'.
    Columns: site_id, n. Ordered by site_id. Filter rows with WHERE, filter groups with HAVING."""
    raise NotImplementedError


def q_employees_with_approved_request() -> str:
    """ex08. Names of employees that have at least one approved request. One column: name; each name once;
    ordered by name. Use IN (subquery) or EXISTS, not a plain join (a join repeats names)."""
    raise NotImplementedError


def q_above_average_requesters() -> str:
    """ex09. MUST start with WITH (a CTE). Employees whose number of requests is strictly greater than the
    average number of requests per employee who has at least one. Columns: name, n. Ordered by name.
    Seed: counts are 1, 2, 2, 2 so the average is 1.75."""
    raise NotImplementedError


def q_latest_request_per_employee() -> str:
    """ex10. MUST use a window function (OVER). For each employee that has requests, the request with the
    LATEST starts_on. Columns: employee_id, id. Ordered by employee_id.
    Hint: ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY starts_on DESC) in a subquery, keep rn = 1."""
    raise NotImplementedError


def q_days_since_previous_request() -> str:
    """ex11. MUST use LAG. For each request that has an EARLIER request by the same employee, the whole days
    between the two starts_on dates. Columns: id, days (integer). Ordered by id. Requests with no earlier
    request are not returned. Hint: compute LAG in a subquery, then filter `prev IS NOT NULL` outside it."""
    raise NotImplementedError


def q_documents_with_chunk_counts() -> str:
    """ex12. Columns: title, n (number of chunks). Every document appears, including the one with zero chunks.
    Ordered by title."""
    raise NotImplementedError


def q_sites_mentioned() -> str:
    """ex13. Set operation. Every DISTINCT site id mentioned either as an employee's site or as a request's
    site, in ONE column called id, sorted. (PUN-01 is mentioned by neither.) Use UNION."""
    raise NotImplementedError


def q_sites_not_in_loose() -> str:
    """ex14. The NULL trap. The test creates a table `loose(site_id TEXT)` holding 'BLR-01' and a NULL.
    Return ids of sites that are NOT in loose.site_id. Columns: id. Ordered by id.
    `WHERE id NOT IN (SELECT site_id FROM loose)` returns NOTHING because of the NULL. Write it so it works."""
    raise NotImplementedError


def badges_schema() -> str:
    """ex15. Return SQL (several statements are fine) that creates a table `badges` with:
        id           TEXT primary key
        employee_id  TEXT not null, foreign key to employees(id)
        issued_on    TEXT not null
        expires_on   TEXT not null, and the table must reject expires_on <= issued_on (CHECK)
        status       TEXT not null, default 'active', only 'active' or 'revoked' allowed (CHECK)
        and one employee cannot have two badges issued on the same day: UNIQUE (employee_id, issued_on)
    The tests insert good and bad rows and expect sqlite3.IntegrityError for each bad one."""
    raise NotImplementedError
