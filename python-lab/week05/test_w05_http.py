"""Tests for week 5. Do not edit. No network: every HTTP call goes to httpx.MockTransport."""
from datetime import datetime, timezone

import httpx
import pytest

from w05_http import (
    ConfigError, PaginationError, PermanentError, ResilientClient, RetryableError,
    backoff_delays, call_with_retry, fetch_all, is_retryable_status,
    parse_retry_after, read_api_key,
)


# ---------- helpers -------------------------------------------------------
class Recorder:
    """A fake sleep: records the waits instead of waiting."""
    def __init__(self):
        self.waits = []

    def __call__(self, seconds):
        self.waits.append(seconds)


def failing_then_ok(failures, exc_factory=lambda n: RetryableError(f"fail {n}")):
    """A function that raises `failures` times and then returns 'ok'. fn.calls[0] counts the calls."""
    calls = [0]

    def fn():
        calls[0] += 1
        if calls[0] <= failures:
            raise exc_factory(calls[0])
        return "ok"
    fn.calls = calls
    return fn


class FakePages:
    """Serves pages from a dict cursor -> page. Records the cursors it was asked for."""
    def __init__(self, pages):
        self.pages, self.asked = pages, []

    def get_page(self, cursor):
        self.asked.append(cursor)
        if len(self.asked) > 50:      # safety net: an endless loop fails fast instead of hanging
            raise AssertionError("fetch_all kept asking for pages: no loop guard?")
        return self.pages[cursor]


def make_client(handler, **kw):
    kw.setdefault("sleep", Recorder())
    return ResilientClient(httpx.MockTransport(handler), "k-123", **kw)


# ---------- ex01 is_retryable_status ---------------------------------------
@pytest.mark.parametrize("status", [408, 429, 500, 502, 503, 504])
def test_retryable_statuses(status):
    assert is_retryable_status(status) is True


@pytest.mark.parametrize("status", [200, 201, 204, 301, 400, 401, 403, 404, 409, 422, 501])
def test_non_retryable_statuses(status):
    assert is_retryable_status(status) is False


# ---------- ex02 backoff_delays --------------------------------------------
def test_backoff_doubles():
    assert backoff_delays(5, 1, 30) == [1, 2, 4, 8]


def test_backoff_has_attempts_minus_one_waits():
    assert backoff_delays(1, 1, 30) == []
    assert len(backoff_delays(4, 0.5, 30)) == 3


def test_backoff_is_capped():
    assert backoff_delays(8, 1, 10) == [1, 2, 4, 8, 10, 10, 10]


def test_backoff_uses_base_delay():
    assert backoff_delays(3, 0.25, 30) == [0.25, 0.5]


def test_backoff_jitter_scales_each_wait():
    assert backoff_delays(4, 1, 30, jitter=lambda: 0.5) == [0.5, 1.0, 2.0]
    assert backoff_delays(4, 1, 30, jitter=lambda: 0.0) == [0.0, 0.0, 0.0]


def test_backoff_jitter_applies_after_the_cap():
    assert backoff_delays(6, 1, 4, jitter=lambda: 0.5) == [0.5, 1.0, 2.0, 2.0, 2.0]


def test_backoff_rejects_zero_attempts():
    with pytest.raises(ValueError):
        backoff_delays(0, 1, 30)


# ---------- ex03 parse_retry_after -----------------------------------------
NOW = datetime(2026, 10, 21, 7, 27, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("value", [None, "", "   ", "soon", "-5", "1.5"])
def test_retry_after_unparseable_is_none(value):
    assert parse_retry_after(value, now=NOW) is None


def test_retry_after_seconds():
    assert parse_retry_after("120") == 120.0
    assert parse_retry_after(" 7 ") == 7.0
    assert parse_retry_after("0") == 0.0


def test_retry_after_http_date():
    assert parse_retry_after("Wed, 21 Oct 2026 07:28:00 GMT", now=NOW) == 60.0


def test_retry_after_date_in_the_past_is_zero():
    assert parse_retry_after("Wed, 21 Oct 2026 07:00:00 GMT", now=NOW) == 0.0


def test_retry_after_default_now_is_current_time():
    far_future = "Fri, 01 Jan 2100 00:00:00 GMT"
    assert parse_retry_after(far_future) > 1_000_000


# ---------- ex04 call_with_retry -------------------------------------------
def test_returns_immediately_when_first_call_works():
    s = Recorder()
    fn = failing_then_ok(0)
    assert call_with_retry(fn, attempts=3, sleep=s) == "ok"
    assert fn.calls[0] == 1 and s.waits == []


def test_fails_twice_then_succeeds():
    s = Recorder()
    fn = failing_then_ok(2)
    assert call_with_retry(fn, attempts=3, base_delay=1, sleep=s) == "ok"
    assert fn.calls[0] == 3
    assert s.waits == [1, 2]


def test_raises_the_last_error_after_the_limit_and_does_not_sleep_after_it():
    s = Recorder()
    fn = failing_then_ok(99)
    with pytest.raises(RetryableError, match="fail 3"):
        call_with_retry(fn, attempts=3, base_delay=1, sleep=s)
    assert fn.calls[0] == 3          # exactly `attempts` calls, not attempts + 1
    assert s.waits == [1, 2]         # two waits, none after the final failure


def test_attempts_one_means_no_retry():
    s = Recorder()
    fn = failing_then_ok(5)
    with pytest.raises(RetryableError):
        call_with_retry(fn, attempts=1, sleep=s)
    assert fn.calls[0] == 1 and s.waits == []


def test_other_exceptions_are_not_retried():
    s = Recorder()
    fn = failing_then_ok(5, exc_factory=lambda n: PermanentError("bad request"))
    with pytest.raises(PermanentError):
        call_with_retry(fn, attempts=5, sleep=s)
    assert fn.calls[0] == 1 and s.waits == []


def test_retry_on_can_be_widened():
    s = Recorder()
    fn = failing_then_ok(1, exc_factory=lambda n: ConnectionError("reset"))
    assert call_with_retry(fn, attempts=2, sleep=s, retry_on=(ConnectionError,)) == "ok"


def test_waits_are_capped():
    s = Recorder()
    fn = failing_then_ok(5)
    call_with_retry(fn, attempts=6, base_delay=1, cap=3, sleep=s)
    assert s.waits == [1, 2, 3, 3, 3]


def test_jitter_is_applied_to_the_waits():
    s = Recorder()
    fn = failing_then_ok(2)
    call_with_retry(fn, attempts=3, base_delay=4, sleep=s, jitter=lambda: 0.25)
    assert s.waits == [1.0, 2.0]


def test_retry_after_from_the_error_replaces_the_backoff():
    s = Recorder()
    fn = failing_then_ok(2, exc_factory=lambda n: RetryableError("429", retry_after=5))
    call_with_retry(fn, attempts=3, base_delay=0.1, sleep=s, jitter=lambda: 0.5)
    assert s.waits == [5, 5]          # server's number, no jitter, not the 0.05 / 0.1 backoff


def test_retry_after_is_capped():
    s = Recorder()
    fn = failing_then_ok(1, exc_factory=lambda n: RetryableError("429", retry_after=3600))
    call_with_retry(fn, attempts=2, cap=30, sleep=s)
    assert s.waits == [30]


def test_none_retry_after_falls_back_to_backoff():
    s = Recorder()
    fn = failing_then_ok(1, exc_factory=lambda n: RetryableError("503", retry_after=None))
    call_with_retry(fn, attempts=2, base_delay=2, sleep=s)
    assert s.waits == [2]


def test_zero_attempts_is_a_programming_error():
    with pytest.raises(ValueError):
        call_with_retry(lambda: 1, attempts=0)


# ---------- ex05 fetch_all -------------------------------------------------
def test_fetch_all_one_page():
    c = FakePages({None: {"items": ["a", "b"], "next_cursor": None}})
    assert fetch_all(c) == ["a", "b"]
    assert c.asked == [None]


def test_fetch_all_zero_items():
    c = FakePages({None: {"items": [], "next_cursor": None}})
    assert fetch_all(c) == []


def test_fetch_all_three_pages_in_order():
    c = FakePages({
        None: {"items": [1, 2], "next_cursor": "p2"},
        "p2": {"items": [3, 4], "next_cursor": "p3"},
        "p3": {"items": [5], "next_cursor": None},
    })
    assert fetch_all(c) == [1, 2, 3, 4, 5]
    assert c.asked == [None, "p2", "p3"]


def test_fetch_all_missing_next_cursor_key_means_done():
    c = FakePages({None: {"items": [1]}})
    assert fetch_all(c) == [1]


def test_fetch_all_detects_a_cursor_that_points_to_itself():
    c = FakePages({None: {"items": [1], "next_cursor": "x"}, "x": {"items": [2], "next_cursor": "x"}})
    with pytest.raises(PaginationError):
        fetch_all(c)
    assert len(c.asked) <= 3          # it stopped quickly, it did not spin


def test_fetch_all_detects_a_longer_cycle():
    c = FakePages({
        None: {"items": [1], "next_cursor": "a"},
        "a": {"items": [2], "next_cursor": "b"},
        "b": {"items": [3], "next_cursor": "a"},
    })
    with pytest.raises(PaginationError):
        fetch_all(c)


def test_fetch_all_stops_at_max_pages_even_with_fresh_cursors():
    class Endless:
        n = 0

        def get_page(self, cursor):
            self.n += 1
            if self.n > 50:
                raise AssertionError("fetch_all ignored max_pages")
            return {"items": [self.n], "next_cursor": f"c{self.n}"}

    e = Endless()
    with pytest.raises(PaginationError):
        fetch_all(e, max_pages=5)
    assert e.n == 5                    # asked for exactly max_pages pages, then gave up


def test_fetch_all_allows_exactly_max_pages():
    c = FakePages({None: {"items": [1], "next_cursor": "b"}, "b": {"items": [2], "next_cursor": None}})
    assert fetch_all(c, max_pages=2) == [1, 2]


# ---------- ex06 read_api_key ----------------------------------------------
def test_read_api_key_returns_value():
    assert read_api_key({"BADGEDESK_API_KEY": "abc123"}) == "abc123"


def test_read_api_key_strips_whitespace():
    assert read_api_key({"BADGEDESK_API_KEY": "  abc123\n"}) == "abc123"


def test_read_api_key_custom_name():
    assert read_api_key({"VENDOR_TOKEN": "t"}, name="VENDOR_TOKEN") == "t"


@pytest.mark.parametrize("env", [{}, {"BADGEDESK_API_KEY": ""}, {"BADGEDESK_API_KEY": "   "}])
def test_read_api_key_fails_loudly(env):
    with pytest.raises(ConfigError) as err:
        read_api_key(env)
    assert "BADGEDESK_API_KEY" in str(err.value)


def test_read_api_key_error_never_contains_other_secrets():
    with pytest.raises(ConfigError) as err:
        read_api_key({"OTHER": "super-secret-value"})
    assert "super-secret-value" not in str(err.value)


# ---------- ex07 ResilientClient: requests it sends ------------------------
def test_client_sends_bearer_header_and_accept():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        seen["accept"] = request.headers.get("accept")
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True})

    c = make_client(handler)
    assert c.get_json("/v1/ping") == {"ok": True}
    assert seen["auth"] == "Bearer k-123"
    assert seen["accept"] == "application/json"
    assert seen["url"] == "https://api.example.test/v1/ping"


def test_client_passes_params():
    seen = {}

    def handler(request):
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json=[])

    make_client(handler).get_json("/v1/requests", params={"status": "pending", "limit": 2})
    assert seen["query"] == {"status": "pending", "limit": "2"}


def test_client_has_an_explicit_timeout():
    c = make_client(lambda r: httpx.Response(200, json={}))
    t = c._http.timeout
    assert t.connect == 3.0 and t.read == 10.0


def test_client_uses_the_base_url():
    seen = {}

    def handler(request):
        seen["host"] = request.url.host
        return httpx.Response(200, json={})

    make_client(handler, base_url="https://vendor.example.test").get_json("/x")
    assert seen["host"] == "vendor.example.test"


# ---------- ex07 ResilientClient: failure handling -------------------------
def test_client_does_not_retry_a_404():
    n = [0]

    def handler(request):
        n[0] += 1
        return httpx.Response(404, json={"error": "no such request"})

    c = make_client(handler)
    with pytest.raises(PermanentError):
        c.get_json("/v1/requests/req-9")
    assert n[0] == 1


@pytest.mark.parametrize("status", [400, 401, 403, 409, 422])
def test_client_does_not_retry_other_4xx(status):
    n = [0]

    def handler(request):
        n[0] += 1
        return httpx.Response(status)

    with pytest.raises(PermanentError):
        make_client(handler).get_json("/x")
    assert n[0] == 1


def test_client_retries_503_then_succeeds():
    codes = iter([503, 503, 200])
    s = Recorder()

    def handler(request):
        code = next(codes)
        return httpx.Response(code, json={"ok": True}) if code == 200 else httpx.Response(code)

    c = make_client(handler, sleep=s, base_delay=1)
    assert c.get_json("/x") == {"ok": True}
    assert s.waits == [1, 2]


def test_client_gives_up_after_attempts_and_raises_retryable():
    n = [0]

    def handler(request):
        n[0] += 1
        return httpx.Response(502)

    s = Recorder()
    with pytest.raises(RetryableError):
        make_client(handler, attempts=4, sleep=s).get_json("/x")
    assert n[0] == 4 and len(s.waits) == 3


def test_client_retries_a_timeout_then_succeeds():
    n = [0]

    def handler(request):
        n[0] += 1
        if n[0] == 1:
            raise httpx.ReadTimeout("slow", request=request)
        return httpx.Response(200, json={"n": n[0]})

    assert make_client(handler).get_json("/x") == {"n": 2}


def test_client_retries_a_connection_error():
    n = [0]

    def handler(request):
        n[0] += 1
        if n[0] == 1:
            raise httpx.ConnectError("refused", request=request)
        return httpx.Response(200, json={"n": n[0]})

    assert make_client(handler).get_json("/x") == {"n": 2}


def test_client_honours_retry_after_on_429():
    codes = iter([429, 200])
    s = Recorder()

    def handler(request):
        if next(codes) == 429:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json={"ok": 1})

    c = make_client(handler, sleep=s, base_delay=0.1)
    assert c.get_json("/x") == {"ok": 1}
    assert s.waits == [7.0]


def test_client_invalid_json_is_permanent_and_not_retried():
    n = [0]

    def handler(request):
        n[0] += 1
        return httpx.Response(200, content=b"<html>maintenance</html>")

    with pytest.raises(PermanentError):
        make_client(handler).get_json("/x")
    assert n[0] == 1


# ---------- ex08 ResilientClient + pagination ------------------------------
def test_get_page_sends_cursor_only_when_given():
    queries = []

    def handler(request):
        queries.append(dict(request.url.params))
        return httpx.Response(200, json={"items": [], "next_cursor": None})

    c = make_client(handler)
    c.get_page()
    c.get_page("abc")
    assert queries == [{}, {"cursor": "abc"}]


def test_get_all_follows_the_cursor_over_http():
    data = {
        None: {"items": ["req-1", "req-2"], "next_cursor": "c2"},
        "c2": {"items": ["req-3"], "next_cursor": None},
    }

    def handler(request):
        assert request.url.path == "/v1/requests"
        return httpx.Response(200, json=data[request.url.params.get("cursor")])

    assert make_client(handler).get_all() == ["req-1", "req-2", "req-3"]


def test_get_all_retries_a_flaky_middle_page():
    state = {"flaked": False}

    def handler(request):
        cursor = request.url.params.get("cursor")
        if cursor is None:
            return httpx.Response(200, json={"items": [1], "next_cursor": "p2"})
        if not state["flaked"]:
            state["flaked"] = True
            return httpx.Response(503)
        return httpx.Response(200, json={"items": [2], "next_cursor": None})

    assert make_client(handler).get_all() == [1, 2]


def test_get_all_stops_on_a_server_that_repeats_its_cursor():
    calls = [0]

    def handler(request):
        calls[0] += 1
        assert calls[0] < 50, "kept requesting pages: no loop guard?"
        return httpx.Response(200, json={"items": [1], "next_cursor": "same"})

    with pytest.raises(PaginationError):
        make_client(handler).get_all()


def test_close_closes_the_underlying_client():
    c = make_client(lambda r: httpx.Response(200, json={}))
    c.close()
    assert c._http.is_closed
