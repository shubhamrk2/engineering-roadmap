"""Week 9 - reliability toolkit for a mock badge-vendor integration (Gate 2).

Edit this file until `pytest week09` is green. Every function and method below is a stub that raises
NotImplementedError; the docstring is the specification and test_w09_reliability.py is the judge.

Rules of this lab: standard library only, no network, no real sleeping, no real clock. Time and
randomness are INJECTED (sleep=, rand=, clock=) so tests run in milliseconds and are deterministic.
That injection is the technique being taught; you must be able to explain it.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import random
import re
import time
from typing import Any, Callable


# ---------------------------------------------------------------- errors (given, do not edit)
class TransientError(Exception):
    """A failure that a retry may fix: timeout, HTTP 503, connection reset."""


class PermanentError(Exception):
    """A failure no retry will fix: HTTP 400, 403, 404, 422."""


class VendorTimeout(TransientError):
    """The vendor did not answer in time. The work may or may not have happened on their side."""


class CircuitOpenError(Exception):
    """Raised by CircuitBreaker.call without calling the function, while the circuit is open."""


class IdempotencyConflict(Exception):
    """The same idempotency key was reused with a different request."""


# ---------------------------------------------------------------- 1. checksums
def sha256_file(path, chunk_size: int = 65536) -> str:
    """Return the hex SHA-256 of the file at `path`, reading it `chunk_size` bytes at a time.

    Never read the whole file into memory (the file may be 5 GB). Open it in binary mode.
    Raise ValueError if chunk_size is less than 1.
    """
    raise NotImplementedError


# ---------------------------------------------------------------- 2. webhook signatures
def sign(secret: bytes, timestamp: int, body: bytes) -> str:
    """Return the hex HMAC-SHA256 of  str(timestamp) + "." + body  using `secret` as the key.

    The timestamp is part of the signed message, so an attacker cannot replay an old body with a fresh
    timestamp. Example: sign(b"k", 100, b"{}") signs the bytes b"100.{}".
    """
    raise NotImplementedError


def verify_signature(secret: bytes, timestamp: int, body: bytes, signature: str,
                     now: int, tolerance: int = 300) -> bool:
    """True only if the signature is valid AND the timestamp is within `tolerance` seconds of `now`.

    - A timestamp too old OR too far in the future (abs(now - timestamp) > tolerance) is rejected.
      The boundary itself (difference == tolerance) is accepted.
    - Compare signatures with hmac.compare_digest (constant time), never with ==.
    - Never raise on garbage: a non-hex or non-ASCII signature simply returns False.
    """
    raise NotImplementedError


# ---------------------------------------------------------------- 3. idempotency and dedupe
class IdempotencyStore:
    """Remember the result of an operation per idempotency key (in memory; a real one is a DB table)."""

    def __init__(self):
        """Start empty."""
        raise NotImplementedError

    def run(self, key: str, fingerprint: str, fn: Callable[[], Any]) -> Any:
        """Run `fn` at most once per `key` and return its result.

        - First time a key is seen: call fn(), remember (fingerprint, result), return result.
        - Key seen before with the SAME fingerprint: return the remembered result WITHOUT calling fn.
        - Key seen before with a DIFFERENT fingerprint: raise IdempotencyConflict(key).
        - If fn raises, remember nothing and let the exception propagate, so the caller may retry the key.
        """
        raise NotImplementedError


class EventDeduper:
    """Remember which webhook event ids have been accepted."""

    def __init__(self):
        """Start empty."""
        raise NotImplementedError

    def first_time(self, event_id: str) -> bool:
        """Return True the first time `event_id` is offered (and remember it), False on every later call."""
        raise NotImplementedError

    def forget(self, event_id: str) -> None:
        """Un-remember an id so a later redelivery of it is treated as new. Unknown ids are ignored."""
        raise NotImplementedError


# ---------------------------------------------------------------- 4. retry with backoff and jitter
def retry_with_backoff(fn: Callable[[], Any], *, max_attempts: int = 4, base: float = 0.5,
                       cap: float = 8.0, sleep: Callable[[float], None] = time.sleep,
                       rand: Callable[[], float] = random.random,
                       retry_on: tuple = (TransientError,)) -> Any:
    """Call fn() until it returns, retrying only exceptions in `retry_on`, with full-jitter backoff.

    - max_attempts is the TOTAL number of calls (4 means 1 try + 3 retries). Raise ValueError if < 1.
    - After a failed attempt n (n = 1, 2, 3, ...) that will be retried, call
          sleep(rand() * min(cap, base * 2 ** (n - 1)))
      This is "full jitter": a random delay between 0 and an exponentially growing, capped ceiling.
    - Do not sleep after the final failed attempt: re-raise that exception.
    - An exception NOT in retry_on propagates immediately: no sleep, no further attempts.
    - Return fn()'s value on the first success.
    """
    raise NotImplementedError


# ---------------------------------------------------------------- 5. circuit breaker
class CircuitBreaker:
    """closed -> open -> half_open -> closed, driven by an injected clock.

    Attribute `state` is one of the strings "closed", "open", "half_open".
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 30.0,
                 clock: Callable[[], float] = time.monotonic):
        """Start closed with zero failures."""
        raise NotImplementedError

    def call(self, fn: Callable[[], Any]) -> Any:
        """Call fn() through the breaker and return its result.

        - closed: call fn. A success resets the consecutive-failure count to 0. A failure (any Exception)
          adds 1 and re-raises; when the count reaches failure_threshold, state becomes "open" and the
          clock time is remembered.
        - open: if clock() - opened_at < reset_timeout, raise CircuitOpenError WITHOUT calling fn.
          Otherwise move to "half_open" and fall through to the next rule.
        - half_open: let this one call through. Success -> state "closed", failures 0.
          Failure -> state "open" again, opened-at set to the current clock time, exception re-raised.
        """
        raise NotImplementedError


# ---------------------------------------------------------------- 6. rate limiting
class TokenBucket:
    """A token bucket driven by an injected clock."""

    def __init__(self, capacity: float, refill_per_sec: float,
                 clock: Callable[[], float] = time.monotonic):
        """Start FULL: tokens == capacity at the time of construction."""
        raise NotImplementedError

    def allow(self, cost: float = 1) -> bool:
        """Refill for the time elapsed since the last call (never above capacity), then try to take `cost`.

        Return True and remove the tokens if there are enough; otherwise return False and take nothing.
        """
        raise NotImplementedError


# ---------------------------------------------------------------- 7. audit-log redaction
SENSITIVE_KEYS = frozenset({"password", "token", "secret", "authorization", "api_key", "email", "phone"})
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def redact(value: Any, sensitive_keys=SENSITIVE_KEYS) -> Any:
    """Return a COPY of `value` that is safe to write to an audit log. Never mutate the input.

    - dict: every key whose lowercase form is in sensitive_keys gets the value "[REDACTED]";
      other values are redacted recursively.
    - list or tuple: return a list with each item redacted recursively.
    - str: replace every e-mail address inside it with "[EMAIL]".
    - anything else (int, None, bool...): return unchanged.
    """
    raise NotImplementedError


# ---------------------------------------------------------------- 8. fake vendor
class FakeVendor:
    """A scripted stand-in for the badge vendor's HTTP API. No network."""

    def __init__(self, script: list[str] | None = None, honours_idempotency: bool = True):
        """`script` is a list of behaviours consumed one per call to provision(); when it runs out the
        behaviour is "ok". Behaviours: "ok", "timeout", "timeout_after_commit", "server_error", "bad_request".

        Public attributes: `calls` (list of dicts, one per call, recording the four arguments),
        `badges` (dict badge_id -> {"employee_id", "site_id"} of badges that really exist on the vendor side).
        """
        raise NotImplementedError

    def provision(self, request_id: str, employee_id: str, site_id: str, idempotency_key: str) -> dict:
        """Record the call in self.calls, then act out the next scripted behaviour:

        - "timeout": raise VendorTimeout; nothing is created.
        - "server_error": raise TransientError; nothing is created.
        - "bad_request": raise PermanentError; nothing is created.
        - "ok": create the badge and return {"badge_id", "employee_id", "site_id"}.
        - "timeout_after_commit": create the badge, THEN raise VendorTimeout (the reply was lost).

        Badge ids are "bdg-1", "bdg-2", ... in creation order. If honours_idempotency is True and
        idempotency_key was already used for a created badge, return that same badge and do NOT
        create a second one. If it is False, every successful call creates a new badge.
        self.calls entries have the keys request_id, employee_id, site_id, idempotency_key.
        """
        raise NotImplementedError


# ---------------------------------------------------------------- 9. the integration (Gate 2)
class BadgeService:
    """Consumes access-request events and provisions badges at the vendor, safely."""

    def __init__(self, vendor, *, store: IdempotencyStore | None = None,
                 deduper: EventDeduper | None = None,
                 sleep: Callable[[float], None] = time.sleep,
                 rand: Callable[[], float] = random.random, max_attempts: int = 4):
        """Keep the arguments (create a fresh IdempotencyStore / EventDeduper when None).

        Public attributes: `audit` (list of dicts), `dead_letters` (list of events that failed).
        """
        raise NotImplementedError

    def _log(self, event_id: str, outcome: str, **fields) -> None:
        self.audit.append(redact({"event_id": event_id, "outcome": outcome, **fields}))

    def handle_event(self, event: dict) -> str:
        """Process one event dict with keys event_id, request_id, employee_id, site_id (and maybe email).

        Returns "processed", "duplicate" or "failed". Steps:
        1. deduper.first_time(event_id) is False -> audit outcome "duplicate", return "duplicate".
        2. Idempotency key is "provision:" + request_id; fingerprint is employee_id + "|" + site_id.
        3. Through self.store.run(...) call vendor.provision(request_id, employee_id, site_id, key)
           inside retry_with_backoff (pass self.sleep, self.rand, self.max_attempts). The SAME key is
           sent on every attempt: that is what makes a retry after a lost reply safe.
        4. Audit one entry per vendor attempt: outcome "attempt_ok" or "attempt_failed" with field
           attempt (1, 2, ...) and, on failure, field error (the exception class name).
        5. Success: audit outcome "processed" with badge_id; return "processed".
        6. TransientError (retries exhausted), PermanentError or IdempotencyConflict: forget the event id
           so a redelivery can try again, append the event (passed through redact) to dead_letters,
           audit outcome "dead_lettered" with field error, return "failed".
        Every audit entry has "event_id" and "outcome", and passes through redact().
        """
        raise NotImplementedError


class WebhookReceiver:
    """Receives vendor webhooks: verify, validate, acknowledge fast, process later."""

    REQUIRED = ("event_id", "request_id", "employee_id", "site_id")

    def __init__(self, secret: bytes, service: BadgeService, *,
                 clock: Callable[[], float] = time.time, tolerance: int = 300):
        """Keep the arguments; `queue` starts as an empty list."""
        raise NotImplementedError

    def receive(self, body: bytes, timestamp: int, signature: str) -> int:
        """Return the HTTP status to send back; never call the service here (acknowledge fast).

        - Signature or timestamp invalid (verify_signature with now=int(self.clock())) -> 401, queue nothing.
        - Body is not valid JSON, is not a JSON object, or lacks any key in REQUIRED -> 400, queue nothing.
        - Otherwise append the parsed event to self.queue and return 200. A duplicate event id is STILL
          acknowledged with 200 here; de-duplication happens when the event is processed.
        Check the signature BEFORE parsing the body.
        """
        raise NotImplementedError

    def drain(self) -> list[str]:
        """Process every queued event in order with service.handle_event and return the list of outcomes.
        The queue is empty afterwards."""
        raise NotImplementedError
