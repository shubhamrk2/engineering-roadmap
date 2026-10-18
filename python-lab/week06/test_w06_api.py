"""Week 6 tests. Do not edit; make them pass by writing w06_api.py.

Run:  pytest week06
Every API test builds a fresh app with create_app(), so tests never share state.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from w06_api import (
    AccessRequestIn,
    AccessRequestOut,
    Status,
    create_app,
    error_body,
    paginate,
)

EMP = {"X-API-Key": "key-emp"}
MGR = {"X-API-Key": "key-mgr"}

VALID = {
    "employee_id": "e-902",
    "site_id": "BLR-01",
    "starts_on": "2026-12-07",
    "ends_on": "2026-12-11",
    "reason": "Quarterly planning week",
}


@pytest.fixture
def client():
    return TestClient(create_app())


def make(client, **overrides):
    return client.post("/requests", json={**VALID, **overrides}, headers=EMP)


# ---------------------------------------------------------------- Pydantic models (no server)

def test_in_model_accepts_valid_payload_and_parses_dates():
    m = AccessRequestIn(**VALID)
    assert m.starts_on == date(2026, 12, 7)
    assert m.ends_on == date(2026, 12, 11)


@pytest.mark.parametrize("field, bad", [
    ("employee_id", "902"),
    ("employee_id", "e-"),
    ("site_id", "blr-01"),
    ("site_id", "BLR1"),
    ("reason", "hey"),
    ("reason", "x" * 201),
    ("starts_on", "not-a-date"),
])
def test_in_model_rejects_bad_field(field, bad):
    with pytest.raises(ValidationError) as info:
        AccessRequestIn(**{**VALID, field: bad})
    assert [e["loc"] for e in info.value.errors()] == [(field,)]


def test_in_model_rejects_end_before_start():
    with pytest.raises(ValidationError):
        AccessRequestIn(**{**VALID, "starts_on": "2026-12-11", "ends_on": "2026-12-07"})


def test_in_model_allows_one_day_request():
    m = AccessRequestIn(**{**VALID, "starts_on": "2026-12-07", "ends_on": "2026-12-07"})
    assert m.starts_on == m.ends_on == date(2026, 12, 7)


def test_in_model_forbids_unknown_fields():
    with pytest.raises(ValidationError):
        AccessRequestIn(**VALID, status="approved")


def test_in_model_reports_every_missing_field():
    with pytest.raises(ValidationError) as info:
        AccessRequestIn()
    assert len(info.value.errors()) == 5


def test_out_model_has_no_internal_fields_and_dumps_json_types():
    out = AccessRequestOut(
        id="req-1", employee_id="e-902", site_id="BLR-01",
        starts_on=date(2026, 12, 7), ends_on=date(2026, 12, 11),
        status=Status.PENDING, reason="Quarterly planning week",
    )
    assert out.model_dump(mode="json") == {
        "id": "req-1", "employee_id": "e-902", "site_id": "BLR-01",
        "starts_on": "2026-12-07", "ends_on": "2026-12-11",
        "status": "pending", "reason": "Quarterly planning week",
    }


def test_out_model_rejects_unknown_status():
    with pytest.raises(ValidationError):
        AccessRequestOut(
            id="req-1", employee_id="e-902", site_id="BLR-01",
            starts_on=date(2026, 12, 7), ends_on=date(2026, 12, 7),
            status="banana", reason="Quarterly planning week",
        )


# ---------------------------------------------------------------- pure helpers

def test_error_body_without_details():
    assert error_body("not_found", "gone") == {"error": {"code": "not_found", "message": "gone"}}


def test_error_body_with_details():
    body = error_body("validation_error", "bad", [{"field": "body.days", "message": "too big"}])
    assert body["error"]["details"] == [{"field": "body.days", "message": "too big"}]
    assert body["error"]["code"] == "validation_error"


def test_paginate_window():
    items = list(range(10))
    assert paginate(items, 3, 0) == [0, 1, 2]
    assert paginate(items, 3, 3) == [3, 4, 5]
    assert paginate(items, 3, 9) == [9]
    assert paginate(items, 3, 50) == []


# ---------------------------------------------------------------- routes

def test_health_needs_no_key(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_missing_key_is_401_with_error_shape(client):
    r = client.get("/requests")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_wrong_key_is_401(client):
    r = client.get("/requests", headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_create_returns_201_and_hides_internal_fields(client):
    r = make(client)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == "req-1"
    assert body["status"] == "pending"
    assert body["starts_on"] == "2026-12-07"
    assert "internal_note" not in body
    assert set(body) == {"id", "employee_id", "site_id", "starts_on", "ends_on", "status", "reason"}


def test_read_routes_also_hide_internal_fields(client):
    make(client)
    one = client.get("/requests/req-1", headers=EMP).json()
    listed = client.get("/requests", headers=EMP).json()[0]
    approved = client.post("/requests/req-1/approve", headers=MGR).json()
    for body in (one, listed, approved):
        assert "internal_note" not in body
        assert set(body) == {"id", "employee_id", "site_id", "starts_on", "ends_on", "status", "reason"}


def test_create_assigns_sequential_ids(client):
    assert make(client).json()["id"] == "req-1"
    assert make(client).json()["id"] == "req-2"


def test_create_requires_key(client):
    r = client.post("/requests", json=VALID)
    assert r.status_code == 401


def test_validation_error_uses_our_shape(client):
    r = make(client, employee_id="902")
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    fields = [d["field"] for d in err["details"]]
    assert fields == ["body.employee_id"]
    assert "detail" not in r.json()


def test_bad_date_order_is_422(client):
    r = make(client, starts_on="2026-12-11", ends_on="2026-12-07")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_get_one_and_404_shape(client):
    make(client)
    assert client.get("/requests/req-1", headers=EMP).json()["employee_id"] == "e-902"
    r = client.get("/requests/req-99", headers=EMP)
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message": "request req-99 not found"}}


def test_unknown_route_also_gets_our_error_shape(client):
    r = client.get("/nope", headers=EMP)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_wrong_method_is_405_in_our_shape(client):
    r = client.put("/health")
    assert r.status_code == 405
    assert r.json()["error"]["code"] == "method_not_allowed"


def test_list_filters_by_site_and_status(client):
    make(client)
    make(client, site_id="HYD-01")
    make(client, site_id="HYD-01")
    client.post("/requests/req-3/approve", headers=MGR)
    assert [r["id"] for r in client.get("/requests?site=HYD-01", headers=EMP).json()] == ["req-2", "req-3"]
    assert [r["id"] for r in client.get("/requests?status=approved", headers=EMP).json()] == ["req-3"]
    assert [r["id"] for r in client.get("/requests?site=HYD-01&status=pending", headers=EMP).json()] == ["req-2"]


def test_list_pagination(client):
    for _ in range(5):
        make(client)

    def ids(query):
        return [r["id"] for r in client.get("/requests" + query, headers=EMP).json()]

    assert ids("") == ["req-1", "req-2", "req-3", "req-4", "req-5"]
    assert ids("?limit=2") == ["req-1", "req-2"]
    assert ids("?limit=2&offset=4") == ["req-5"]


@pytest.mark.parametrize("query", ["limit=0", "limit=51", "offset=-1", "limit=abc", "status=banana"])
def test_list_rejects_bad_query(client, query):
    r = client.get(f"/requests?{query}", headers=EMP)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["details"][0]["field"].startswith("query.")


def test_employee_cannot_approve_403(client):
    make(client)
    r = client.post("/requests/req-1/approve", headers=EMP)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_approve_without_key_is_401_not_403(client):
    make(client)
    assert client.post("/requests/req-1/approve").status_code == 401


def test_manager_approves_then_second_approve_is_409(client):
    make(client)
    r = client.post("/requests/req-1/approve", headers=MGR)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    again = client.post("/requests/req-1/approve", headers=MGR)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "conflict"


def test_approve_unknown_is_404(client):
    assert client.post("/requests/req-9/approve", headers=MGR).status_code == 404


def test_delete_is_204_with_empty_body_then_404(client):
    make(client)
    r = client.delete("/requests/req-1", headers=EMP)
    assert r.status_code == 204
    assert r.content == b""
    assert client.delete("/requests/req-1", headers=EMP).status_code == 404
    assert client.get("/requests", headers=EMP).json() == []


def test_apps_do_not_share_state():
    a, b = TestClient(create_app()), TestClient(create_app())
    make(a)
    assert b.get("/requests", headers=EMP).json() == []


def test_custom_api_keys():
    c = TestClient(create_app(api_keys={"k1": "manager"}))
    assert c.get("/requests", headers=EMP).status_code == 401
    assert c.get("/requests", headers={"X-API-Key": "k1"}).status_code == 200
