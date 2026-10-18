"""Week 6: Pydantic models, a FastAPI app factory, a dependency, error handlers.

Replace each stub with your own code. Do not edit test_w06_api.py.
Run:  pytest week06            (from the python-lab folder, with the venv active)

Synthetic domain: access requests. Employee ids look like e-902, sites like BLR-01.

Hints on the imports you will need (delete the ones you do not use):
    from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, ConfigDict, Field, model_validator
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from typing import Annotated
"""
from datetime import date  # noqa: F401  (you will need this)
from enum import Enum

from pydantic import BaseModel  # noqa: F401


class Status(str, Enum):
    """Given to you: the allowed states of an access request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessRequestIn(BaseModel):
    """What a client may send to POST /requests. Replace this docstring-only stub with fields.

    Fields (all required):
        employee_id: str   must match  e-<digits>      e.g. "e-902"
        site_id:     str   must match  three capital letters, a hyphen, two digits   e.g. "BLR-01"
        starts_on:   date  (a JSON string "2026-12-07" is parsed into a date)
        ends_on:     date
        reason:      str   5 to 200 characters long

    Rules:
        - ends_on before starts_on is invalid (the same day is fine). Use a model validator.
        - Unknown fields are rejected (extra="forbid"), so a client cannot smuggle in "status".
    """


class AccessRequestOut(BaseModel):
    """What the API sends back. Replace this docstring-only stub with fields.

    Fields, in this order:
        id: str, employee_id: str, site_id: str, starts_on: date, ends_on: date,
        status: Status, reason: str

    It must NOT contain the stored internal_note field: this model is the response_model.
    """


def error_body(code, message, details=None):
    """Build the one error shape every failure in this API uses.

    error_body("not_found", "gone")
        -> {"error": {"code": "not_found", "message": "gone"}}
    error_body("validation_error", "bad", [{"field": "body.days", "message": "too big"}])
        -> {"error": {"code": "validation_error", "message": "bad",
                      "details": [{"field": "body.days", "message": "too big"}]}}
    The "details" key is present only when details is not None.
    """
    raise NotImplementedError("Write error_body")


def paginate(items, limit, offset):
    """Return the window of `items` that starts at `offset` and holds at most `limit` entries.

    paginate(list(range(10)), 3, 3) -> [3, 4, 5];  paginate(list(range(10)), 3, 50) -> []
    """
    raise NotImplementedError("Write paginate")


def create_app(api_keys=None):
    """Build and return a FastAPI app. A fresh call must give a fresh, empty store (no module-level state).

    api_keys: dict mapping an API key to a role, default {"key-emp": "employee", "key-mgr": "manager"}.

    Authentication (a dependency reading the X-API-Key header):
        - header missing, or key not in api_keys -> HTTPException 401
        - /health needs no key; every /requests route does.
    Authorisation:
        - POST /requests/{request_id}/approve needs role "manager"; an employee gets 403.
          (No key is still 401, not 403.)

    Routes:
        GET    /health                            -> 200 {"status": "ok"}
        POST   /requests                          -> 201, body AccessRequestIn, response_model AccessRequestOut.
                                                     ids are "req-1", "req-2", ... in creation order.
                                                     Store a record with status PENDING and an extra
                                                     internal_note="created via API" that must never be returned.
        GET    /requests                          -> list of AccessRequestOut in creation order.
                                                     query: site (optional, matches site_id),
                                                            status (optional Status),
                                                            limit  (int, default 10, 1..50),
                                                            offset (int, default 0, >= 0)
        GET    /requests/{request_id}             -> 200 AccessRequestOut, or 404
        POST   /requests/{request_id}/approve     -> 200 with status "approved"; 404 if unknown;
                                                     409 if the request is not pending any more
        DELETE /requests/{request_id}             -> 204 with no body; 404 if unknown

    Errors: every failure body is error_body(...). Register two exception handlers:
        - for starlette.exceptions.HTTPException (so unknown routes and 405 are covered too):
              code is one of unauthorized(401) forbidden(403) not_found(404)
              method_not_allowed(405) conflict(409), otherwise "http_error"; message is str(exc.detail).
              404 detail for a missing request: f"request {request_id} not found"
        - for fastapi.exceptions.RequestValidationError: status 422, code "validation_error",
          message "request failed validation", details = one {"field": "body.employee_id", "message": ...}
          per error, where field is the error's loc joined with ".".
    """
    raise NotImplementedError("Write create_app")
