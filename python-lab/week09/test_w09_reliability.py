"""Tests for week 9. Do not edit. No network, no real sleeping, no real clock.

Run from the python-lab folder:   pytest week09 -q
"""
import hashlib
import json

import pytest

from w09_reliability import (
    BadgeService, CircuitBreaker, CircuitOpenError, EventDeduper, FakeVendor, IdempotencyConflict,
    IdempotencyStore, PermanentError, TokenBucket, TransientError, VendorTimeout, WebhookReceiver,
    redact, retry_with_backoff, sha256_file, sign, verify_signature,
)


class FakeClock:
    """A clock you move by hand. Calling it returns the current fake time."""
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ------------------------------------------------------------------ checksums
def test_sha256_file_matches_hashlib_for_any_chunk_size(tmp_path):
    data = b"badge-export-" * 1000
    f = tmp_path / "export.bin"
    f.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_file(f) == expected
    assert sha256_file(f, chunk_size=1) == expected
    assert sha256_file(f, chunk_size=7) == expected


def test_sha256_file_empty_file(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    assert sha256_file(f) == hashlib.sha256(b"").hexdigest()


def test_sha256_file_rejects_bad_chunk_size(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    with pytest.raises(ValueError):
        sha256_file(f, chunk_size=0)


def test_sha256_file_reads_in_chunks(tmp_path, monkeypatch):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 100)
    sizes = []
    real_open = open

    def spying_open(*args, **kwargs):
        handle = real_open(*args, **kwargs)
        real_read = handle.read

        class Wrapper:
            def read(self, n=-1):
                sizes.append(n)
                return real_read(n)
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                handle.close()
        return Wrapper()

    monkeypatch.setattr("builtins.open", spying_open)
    sha256_file(f, chunk_size=10)
    assert sizes and all(s == 10 for s in sizes), "read the file 10 bytes at a time, never read() whole"


# ------------------------------------------------------------------ signatures
SECRET = b"whsec_test_not_a_real_secret"
BODY = b'{"event_id":"evt-1"}'


def test_sign_is_hmac_sha256_of_timestamp_dot_body():
    import hmac
    expected = hmac.new(SECRET, b"100." + BODY, hashlib.sha256).hexdigest()
    assert sign(SECRET, 100, BODY) == expected


def test_verify_accepts_a_good_signature():
    sig = sign(SECRET, 1000, BODY)
    assert verify_signature(SECRET, 1000, BODY, sig, now=1000) is True


def test_verify_rejects_tampered_body_wrong_secret_and_garbage():
    sig = sign(SECRET, 1000, BODY)
    assert verify_signature(SECRET, 1000, BODY + b" ", sig, now=1000) is False
    assert verify_signature(b"other", 1000, BODY, sig, now=1000) is False
    assert verify_signature(SECRET, 1000, BODY, "not-hex-at-all", now=1000) is False
    assert verify_signature(SECRET, 1000, BODY, "", now=1000) is False
    assert verify_signature(SECRET, 1000, BODY, "café", now=1000) is False


def test_verify_signature_covers_the_timestamp():
    # A valid signature for t=1000 must not be accepted if the sender claims t=1001.
    sig = sign(SECRET, 1000, BODY)
    assert verify_signature(SECRET, 1001, BODY, sig, now=1001) is False


def test_verify_rejects_old_and_future_timestamps_but_accepts_the_boundary():
    sig = sign(SECRET, 1000, BODY)
    assert verify_signature(SECRET, 1000, BODY, sig, now=1300, tolerance=300) is True     # exactly 300
    assert verify_signature(SECRET, 1000, BODY, sig, now=1301, tolerance=300) is False    # replay window over
    assert verify_signature(SECRET, 1000, BODY, sig, now=699, tolerance=300) is False     # 301 s in the future
    assert verify_signature(SECRET, 1000, BODY, sig, now=700, tolerance=300) is True


def test_verify_uses_constant_time_compare(monkeypatch):
    calls = []
    import hmac as hmac_module
    real = hmac_module.compare_digest

    def spy(a, b):
        calls.append(1)
        return real(a, b)

    monkeypatch.setattr(hmac_module, "compare_digest", spy)
    sig = sign(SECRET, 1000, BODY)
    verify_signature(SECRET, 1000, BODY, sig, now=1000)
    assert calls, "use hmac.compare_digest, not =="


# ------------------------------------------------------------------ idempotency and dedupe
def test_idempotency_runs_fn_once_per_key():
    store = IdempotencyStore()
    calls = []

    def work():
        calls.append(1)
        return {"badge_id": "bdg-1"}

    assert store.run("k1", "fp", work) == {"badge_id": "bdg-1"}
    assert store.run("k1", "fp", work) == {"badge_id": "bdg-1"}
    assert len(calls) == 1
    store.run("k2", "fp", work)
    assert len(calls) == 2


def test_idempotency_same_key_different_request_is_a_conflict():
    store = IdempotencyStore()
    store.run("k1", "e-902|BLR-01", lambda: "a")
    with pytest.raises(IdempotencyConflict):
        store.run("k1", "e-777|HYD-01", lambda: "b")


def test_idempotency_failure_is_not_remembered():
    store = IdempotencyStore()
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) == 1:
            raise TransientError("boom")
        return "ok"

    with pytest.raises(TransientError):
        store.run("k1", "fp", flaky)
    assert store.run("k1", "fp", flaky) == "ok"
    assert len(attempts) == 2


def test_event_deduper_first_time_then_never():
    d = EventDeduper()
    assert d.first_time("evt-1") is True
    assert d.first_time("evt-1") is False
    assert d.first_time("evt-2") is True


def test_event_deduper_forget_allows_redelivery():
    d = EventDeduper()
    d.first_time("evt-1")
    d.forget("evt-1")
    d.forget("never-seen")      # must not raise
    assert d.first_time("evt-1") is True


# ------------------------------------------------------------------ retry with backoff and jitter
def test_retry_returns_first_success_without_sleeping():
    slept = []
    assert retry_with_backoff(lambda: 42, sleep=slept.append, rand=lambda: 0.5) == 42
    assert slept == []


def test_retry_sleeps_with_full_jitter_growing_ceiling():
    slept = []
    state = {"n": 0}

    def fn():
        state["n"] += 1
        if state["n"] < 4:
            raise TransientError("503")
        return "done"

    result = retry_with_backoff(fn, max_attempts=5, base=1.0, cap=100.0, sleep=slept.append, rand=lambda: 1.0)
    assert result == "done"
    assert slept == [1.0, 2.0, 4.0]          # rand()=1.0 gives the ceiling: base * 2**(n-1)


def test_retry_jitter_scales_the_delay_by_rand():
    slept = []
    state = {"n": 0}

    def fn():
        state["n"] += 1
        if state["n"] < 3:
            raise TransientError("503")
        return "done"

    retry_with_backoff(fn, base=2.0, cap=100.0, sleep=slept.append, rand=lambda: 0.25)
    assert slept == [0.5, 1.0]


def test_retry_caps_the_ceiling():
    slept = []

    def always_fail():
        raise TransientError("503")

    with pytest.raises(TransientError):
        retry_with_backoff(always_fail, max_attempts=8, base=1.0, cap=5.0, sleep=slept.append, rand=lambda: 1.0)
    assert slept == [1.0, 2.0, 4.0, 5.0, 5.0, 5.0, 5.0]
    assert max(slept) <= 5.0


def test_retry_gives_up_after_max_attempts_and_does_not_sleep_after_last():
    slept, calls = [], []

    def always_fail():
        calls.append(1)
        raise VendorTimeout("slow")

    with pytest.raises(VendorTimeout):
        retry_with_backoff(always_fail, max_attempts=3, sleep=slept.append, rand=lambda: 1.0)
    assert len(calls) == 3
    assert len(slept) == 2


def test_retry_does_not_retry_permanent_errors():
    slept, calls = [], []

    def bad():
        calls.append(1)
        raise PermanentError("400")

    with pytest.raises(PermanentError):
        retry_with_backoff(bad, sleep=slept.append, rand=lambda: 1.0)
    assert len(calls) == 1 and slept == []


def test_retry_custom_retry_on_and_validation():
    calls = []

    def fn():
        calls.append(1)
        if len(calls) < 2:
            raise KeyError("x")
        return "ok"

    assert retry_with_backoff(fn, retry_on=(KeyError,), sleep=lambda s: None, rand=lambda: 0) == "ok"
    with pytest.raises(ValueError):
        retry_with_backoff(lambda: 1, max_attempts=0)


def test_retry_jitter_is_random_by_default():
    # With the real random.random the delays must differ between runs of the same failure sequence.
    runs = set()
    for _ in range(5):
        slept = []
        state = {"n": 0}

        def fn():
            state["n"] += 1
            if state["n"] < 2:
                raise TransientError("503")

        retry_with_backoff(fn, base=1.0, sleep=slept.append)
        runs.add(slept[0])
    assert len(runs) > 1


# ------------------------------------------------------------------ circuit breaker
def boom():
    raise TransientError("503")


def test_breaker_opens_after_threshold_and_fails_fast():
    clock = FakeClock()
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=30, clock=clock)
    for _ in range(3):
        with pytest.raises(TransientError):
            cb.call(boom)
    assert cb.state == "open"
    calls = []
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: calls.append(1))
    assert calls == [], "an open circuit must not call the function"


def test_breaker_stays_closed_below_threshold_and_success_resets_count():
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=30, clock=FakeClock())
    for _ in range(2):
        with pytest.raises(TransientError):
            cb.call(boom)
    assert cb.call(lambda: "ok") == "ok"
    for _ in range(2):
        with pytest.raises(TransientError):
            cb.call(boom)
    assert cb.state == "closed"       # 2 + reset + 2 never reaches 3 in a row


def test_breaker_half_open_success_closes():
    clock = FakeClock()
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=30, clock=clock)
    for _ in range(2):
        with pytest.raises(TransientError):
            cb.call(boom)
    clock.advance(29.9)
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: "x")
    clock.advance(0.1)                  # exactly reset_timeout elapsed
    assert cb.call(lambda: "recovered") == "recovered"
    assert cb.state == "closed"
    assert cb.call(lambda: "again") == "again"


def test_breaker_half_open_failure_reopens_and_restarts_the_wait():
    clock = FakeClock()
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=30, clock=clock)
    for _ in range(2):
        with pytest.raises(TransientError):
            cb.call(boom)
    clock.advance(30)
    with pytest.raises(TransientError):
        cb.call(boom)                   # the trial call fails
    assert cb.state == "open"
    clock.advance(29)
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: "x")            # wait restarted from the failed trial, not from the first opening
    clock.advance(1)
    assert cb.call(lambda: "ok") == "ok"


# ------------------------------------------------------------------ token bucket
def test_bucket_starts_full_then_rejects():
    clock = FakeClock()
    tb = TokenBucket(capacity=3, refill_per_sec=1, clock=clock)
    assert [tb.allow() for _ in range(4)] == [True, True, True, False]


def test_bucket_refills_over_time_but_never_above_capacity():
    clock = FakeClock()
    tb = TokenBucket(capacity=3, refill_per_sec=1, clock=clock)
    for _ in range(3):
        tb.allow()
    clock.advance(2)
    assert [tb.allow() for _ in range(3)] == [True, True, False]
    clock.advance(1000)
    assert [tb.allow() for _ in range(4)] == [True, True, True, False]


def test_bucket_fractional_refill_and_cost():
    clock = FakeClock()
    tb = TokenBucket(capacity=10, refill_per_sec=0.5, clock=clock)
    assert tb.allow(cost=10) is True
    assert tb.allow() is False
    clock.advance(1)                    # 0.5 token
    assert tb.allow() is False
    clock.advance(1)                    # 1.0 token
    assert tb.allow() is True
    assert tb.allow(cost=5) is False    # a refused request takes nothing
    clock.advance(10)                   # 5 tokens
    assert tb.allow(cost=5) is True


# ------------------------------------------------------------------ redaction
def test_redact_sensitive_keys_case_insensitive_and_nested():
    record = {"event_id": "evt-1", "Authorization": "Bearer abc", "user": {"email": "a@b.com", "id": "e-902"},
              "items": [{"password": "hunter2", "n": 1}]}
    out = redact(record)
    assert out["Authorization"] == "[REDACTED]"
    assert out["user"] == {"email": "[REDACTED]", "id": "e-902"}
    assert out["items"] == [{"password": "[REDACTED]", "n": 1}]
    assert out["event_id"] == "evt-1"


def test_redact_masks_emails_inside_free_text_and_keeps_other_types():
    out = redact({"note": "contact asha.k+it@example.org or bob@x.io today", "count": 3, "ok": True, "none": None})
    assert out["note"] == "contact [EMAIL] or [EMAIL] today"
    assert out["count"] == 3 and out["ok"] is True and out["none"] is None


def test_redact_does_not_mutate_its_input():
    record = {"token": "abc", "nested": {"secret": "s"}, "tags": ["a@b.com"]}
    snapshot = json.dumps(record, sort_keys=True)
    redact(record)
    assert json.dumps(record, sort_keys=True) == snapshot


def test_redact_lists_and_tuples():
    assert redact(["x@y.com", ("phone", {"phone": "1"})]) == ["[EMAIL]", ["phone", {"phone": "[REDACTED]"}]]


# ------------------------------------------------------------------ fake vendor
def test_fakevendor_ok_creates_badges_with_sequential_ids():
    v = FakeVendor()
    a = v.provision("req-1", "e-902", "BLR-01", "k1")
    b = v.provision("req-2", "e-903", "HYD-01", "k2")
    assert (a["badge_id"], b["badge_id"]) == ("bdg-1", "bdg-2")
    assert v.badges["bdg-1"] == {"employee_id": "e-902", "site_id": "BLR-01"}
    assert len(v.calls) == 2 and v.calls[0]["idempotency_key"] == "k1"


def test_fakevendor_scripted_failures_create_nothing():
    v = FakeVendor(["timeout", "server_error", "bad_request"])
    with pytest.raises(VendorTimeout):
        v.provision("req-1", "e-902", "BLR-01", "k1")
    with pytest.raises(TransientError):
        v.provision("req-1", "e-902", "BLR-01", "k1")
    with pytest.raises(PermanentError):
        v.provision("req-1", "e-902", "BLR-01", "k1")
    assert v.badges == {} and len(v.calls) == 3
    assert v.provision("req-1", "e-902", "BLR-01", "k1")["badge_id"] == "bdg-1"   # script exhausted -> ok


def test_fakevendor_timeout_after_commit_creates_the_badge_anyway():
    v = FakeVendor(["timeout_after_commit"])
    with pytest.raises(VendorTimeout):
        v.provision("req-1", "e-902", "BLR-01", "k1")
    assert list(v.badges) == ["bdg-1"]
    again = v.provision("req-1", "e-902", "BLR-01", "k1")     # same key: the vendor dedupes
    assert again["badge_id"] == "bdg-1" and len(v.badges) == 1


def test_fakevendor_without_idempotency_duplicates():
    v = FakeVendor(["timeout_after_commit"], honours_idempotency=False)
    with pytest.raises(VendorTimeout):
        v.provision("req-1", "e-902", "BLR-01", "k1")
    v.provision("req-1", "e-902", "BLR-01", "k1")
    assert len(v.badges) == 2


# ------------------------------------------------------------------ the Gate 2 scenarios
def make_event(event_id="evt-1", request_id="req-1", **extra):
    return {"event_id": event_id, "request_id": request_id, "employee_id": "e-902", "site_id": "BLR-01", **extra}


def make_service(script=None, **kwargs):
    slept = []
    vendor = FakeVendor(script, **kwargs)
    service = BadgeService(vendor, sleep=slept.append, rand=lambda: 1.0, max_attempts=4)
    return service, vendor, slept


def outcomes(service):
    return [e["outcome"] for e in service.audit]


def test_scenario_success():
    service, vendor, slept = make_service()
    assert service.handle_event(make_event()) == "processed"
    assert len(vendor.calls) == 1 and len(vendor.badges) == 1 and slept == []
    assert outcomes(service) == ["attempt_ok", "processed"]
    assert service.audit[-1]["badge_id"] == "bdg-1"
    assert all(e["event_id"] == "evt-1" for e in service.audit)


def test_scenario_timeout_then_success():
    service, vendor, slept = make_service(["timeout", "ok"])
    assert service.handle_event(make_event()) == "processed"
    assert len(vendor.calls) == 2 and len(slept) == 1
    assert outcomes(service) == ["attempt_failed", "attempt_ok", "processed"]
    assert service.audit[0]["attempt"] == 1 and service.audit[0]["error"] == "VendorTimeout"
    assert service.audit[1]["attempt"] == 2
    assert vendor.calls[0]["idempotency_key"] == vendor.calls[1]["idempotency_key"] == "provision:req-1"


def test_scenario_lost_reply_does_not_create_a_second_badge():
    service, vendor, _ = make_service(["timeout_after_commit"])
    assert service.handle_event(make_event()) == "processed"
    assert len(vendor.calls) == 2
    assert len(vendor.badges) == 1, "the retry carried the same idempotency key, so the vendor created one badge"


def test_scenario_permanent_failure_is_not_retried_and_is_dead_lettered():
    service, vendor, slept = make_service(["bad_request"])
    event = make_event(email="asha@example.com")
    assert service.handle_event(event) == "failed"
    assert len(vendor.calls) == 1 and slept == []
    assert outcomes(service) == ["attempt_failed", "dead_lettered"]
    assert service.audit[-1]["error"] == "PermanentError"
    assert len(service.dead_letters) == 1
    assert service.dead_letters[0]["event_id"] == "evt-1"
    assert service.dead_letters[0]["email"] == "[REDACTED]"
    assert event["email"] == "asha@example.com", "the caller's event must not be modified"
    assert vendor.badges == {}


def test_scenario_retries_exhausted_then_redelivery_can_succeed():
    service, vendor, slept = make_service(["timeout"] * 4)
    assert service.handle_event(make_event()) == "failed"
    assert len(vendor.calls) == 4 and len(slept) == 3
    assert len(service.dead_letters) == 1
    # The vendor recovers; the same event is redelivered. Not a duplicate, because failure was forgotten.
    assert service.handle_event(make_event()) == "processed"
    assert len(vendor.badges) == 1


def test_scenario_duplicate_delivery_is_ignored():
    service, vendor, _ = make_service()
    assert service.handle_event(make_event("evt-1")) == "processed"
    assert service.handle_event(make_event("evt-1")) == "duplicate"
    assert len(vendor.calls) == 1 and len(vendor.badges) == 1
    assert outcomes(service)[-1] == "duplicate"


def test_scenario_same_request_new_event_id_does_not_call_vendor_again():
    service, vendor, _ = make_service()
    assert service.handle_event(make_event("evt-1", "req-1")) == "processed"
    assert service.handle_event(make_event("evt-2", "req-1")) == "processed"
    assert len(vendor.calls) == 1 and len(vendor.badges) == 1


def test_scenario_idempotency_conflict_is_failed_not_crash():
    service, vendor, _ = make_service()
    service.handle_event(make_event("evt-1", "req-1"))
    other = make_event("evt-2", "req-1")
    other["employee_id"] = "e-777"
    assert service.handle_event(other) == "failed"
    assert len(vendor.badges) == 1
    assert service.audit[-1]["error"] == "IdempotencyConflict"


def test_audit_never_contains_the_raw_email():
    service, _, _ = make_service(["bad_request"])
    service.handle_event(make_event(email="asha@example.com"))
    assert "asha@example.com" not in json.dumps(service.audit)


# ------------------------------------------------------------------ webhook receiver + whole slice
def signed(body_dict, timestamp, secret=SECRET):
    body = json.dumps(body_dict).encode()
    return body, timestamp, sign(secret, timestamp, body)


def make_receiver(script=None, now=5000.0):
    service, vendor, slept = make_service(script)
    clock = FakeClock(now)
    return WebhookReceiver(SECRET, service, clock=clock, tolerance=300), service, vendor, clock


def test_receiver_bad_signature_is_401_and_queues_nothing():
    rx, service, vendor, _ = make_receiver()
    body, ts, _sig = signed(make_event(), 5000)
    assert rx.receive(body, ts, "0" * 64) == 401
    forged = sign(b"wrong-secret", ts, body)
    assert rx.receive(body, ts, forged) == 401
    assert rx.queue == [] and vendor.calls == []


def test_receiver_replayed_old_message_is_401():
    rx, _, vendor, clock = make_receiver(now=5000)
    body, ts, sig = signed(make_event(), 5000)
    assert rx.receive(body, ts, sig) == 200
    clock.advance(301)                       # the attacker replays the captured request 301 s later
    assert rx.receive(body, ts, sig) == 401


def test_receiver_malformed_bodies_are_400_after_signature_check():
    rx, _, _, _ = make_receiver()
    for raw in (b"not json", b"[1,2]", json.dumps({"event_id": "evt-1"}).encode(), b"\xff\xfe"):
        assert rx.receive(raw, 5000, sign(SECRET, 5000, raw)) == 400
    assert rx.queue == []
    # an unsigned malformed body must be 401, proving the signature is checked first
    assert rx.receive(b"not json", 5000, "bad") == 401


def test_receiver_acknowledges_without_processing_then_drains():
    rx, service, vendor, _ = make_receiver()
    body, ts, sig = signed(make_event(), 5000)
    assert rx.receive(body, ts, sig) == 200
    assert vendor.calls == [] and len(rx.queue) == 1, "ack fast: no vendor call inside receive()"
    assert rx.drain() == ["processed"]
    assert rx.queue == [] and len(vendor.badges) == 1


def test_gate2_full_scenario_duplicates_forgeries_and_a_slow_vendor():
    rx, service, vendor, clock = make_receiver(["timeout", "ok"])
    body1, ts, sig1 = signed(make_event("evt-1", "req-1"), 5000)
    body2, _, sig2 = signed(make_event("evt-2", "req-2"), 5000)

    statuses = [
        rx.receive(body1, ts, sig1),            # good
        rx.receive(body1, ts, sig1),            # vendor delivers the same event twice
        rx.receive(body2, ts, "f" * 64),        # forged
        rx.receive(body2, ts, sig2),            # good, different request
    ]
    assert statuses == [200, 200, 401, 200]
    assert rx.drain() == ["processed", "duplicate", "processed"]
    assert len(vendor.badges) == 2
    assert len(vendor.calls) == 3               # req-1 took two attempts (timeout, ok), req-2 one
    assert service.dead_letters == []
