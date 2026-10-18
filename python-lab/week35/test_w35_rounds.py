import itertools

import pytest

from w35_rounds import (
    LRUCache,
    SlidingWindowLimiter,
    call_with_retry,
    count_errors_by_service,
    flatten_json,
    merge_records,
    parse_log_line,
    reconcile,
    top_k_frequent,
    top_k_largest,
    validate_config,
)


# ---------------------------------------------------------------- ex01 / ex02
def test_ex01_parses_a_normal_line():
    rec = parse_log_line("2027-03-07 09:01:12 ERROR payments Timeout calling gateway")
    assert rec == {"date": "2027-03-07", "time": "09:01:12", "level": "ERROR",
                   "service": "payments", "message": "Timeout calling gateway"}


def test_ex01_message_may_be_empty():
    assert parse_log_line("2027-03-07 09:01:12 INFO auth")["message"] == ""


def test_ex01_extra_spaces_are_tolerated():
    rec = parse_log_line("2027-03-07   09:01:12  WARN   auth   slow   response  ")
    assert rec["service"] == "auth" and rec["message"] == "slow   response"


@pytest.mark.parametrize("line", ["", "garbage", "2027-03-07 09:01:12 ERROR",
                                  "2027-03-07 09:01:12 FATAL payments boom",
                                  "2027-03-07 09:01:12 error payments lowercase"])
def test_ex01_malformed_returns_none(line):
    assert parse_log_line(line) is None


def test_ex02_counts_only_errors():
    lines = [
        "2027-03-07 09:01:12 ERROR payments Timeout",
        "2027-03-07 09:01:13 INFO auth ok",
        "2027-03-07 09:01:14 ERROR payments Timeout again",
        "2027-03-07 09:01:15 ERROR auth bad token",
    ]
    assert count_errors_by_service(lines) == {"payments": 2, "auth": 1}


def test_ex02_empty_and_malformed():
    assert count_errors_by_service([]) == {}
    assert count_errors_by_service(["junk", "", "a b c"]) == {}


def test_ex02_accepts_a_generator():
    gen = (f"2027-03-07 09:00:0{i} ERROR svc x" for i in range(3))
    assert count_errors_by_service(gen) == {"svc": 3}


# ---------------------------------------------------------------------- ex03
class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


def test_ex03_blocks_after_limit():
    clk = FakeClock()
    lim = SlidingWindowLimiter(2, 10, clock=clk)
    assert [lim.allow("a") for _ in range(3)] == [True, True, False]


def test_ex03_window_slides():
    clk = FakeClock()
    lim = SlidingWindowLimiter(2, 10, clock=clk)
    assert lim.allow("a")           # t=0
    clk.t = 5
    assert lim.allow("a")           # t=5
    clk.t = 9.9
    assert not lim.allow("a")
    clk.t = 10                      # the t=0 call is exactly 10s old: it no longer counts
    assert lim.allow("a")
    clk.t = 10.1
    assert not lim.allow("a")       # t=5 and t=10 are still inside the window


def test_ex03_rejected_calls_are_not_recorded():
    clk = FakeClock()
    lim = SlidingWindowLimiter(1, 10, clock=clk)
    assert lim.allow("a")           # t=0
    clk.t = 5
    assert not lim.allow("a")       # must not extend the block
    clk.t = 10
    assert lim.allow("a")


def test_ex03_keys_are_independent():
    clk = FakeClock()
    lim = SlidingWindowLimiter(1, 10, clock=clk)
    assert lim.allow("a") and lim.allow("b")
    assert not lim.allow("a") and not lim.allow("b")


@pytest.mark.parametrize("limit, window", [(0, 10), (-1, 10), (1, 0), (1, -5)])
def test_ex03_bad_arguments(limit, window):
    with pytest.raises(ValueError):
        SlidingWindowLimiter(limit, window)


def test_ex03_default_clock_works():
    lim = SlidingWindowLimiter(1, 60)
    assert lim.allow("x") and not lim.allow("x")


# ---------------------------------------------------------------------- ex04
def test_ex04_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert "a" not in c and "b" in c and "c" in c
    assert len(c) == 2


def test_ex04_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)                   # evicts b, not a
    assert c.keys() == ["a", "c"]


def test_ex04_update_refreshes_and_does_not_grow():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    assert len(c) == 2
    c.put("c", 3)                   # b is now the least recent, so b goes
    assert c.keys() == ["a", "c"]
    assert c.get("a") == 10


def test_ex04_missing_and_default():
    c = LRUCache(1)
    assert c.get("zzz") is None
    assert c.get("zzz", "dflt") == "dflt"


def test_ex04_falsy_values_are_real_values():
    c = LRUCache(2)
    c.put("a", 0)
    c.put("b", None)
    assert c.get("a", "missing") == 0
    assert c.get("b", "missing") is None


def test_ex04_contains_does_not_change_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c
    c.put("c", 3)                   # a is still the least recent
    assert c.keys() == ["b", "c"]


def test_ex04_capacity_one_and_invalid():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.keys() == ["b"]
    with pytest.raises(ValueError):
        LRUCache(0)


# ---------------------------------------------------------------------- ex05
def test_ex05_union_in_first_seen_order():
    old = [{"id": 1, "name": "Asha"}, {"id": 2, "name": "Ravi"}]
    new = [{"id": 3, "name": "Meera"}, {"id": 1, "name": "Asha K"}]
    assert merge_records(old, new) == [
        {"id": 1, "name": "Asha K"}, {"id": 2, "name": "Ravi"}, {"id": 3, "name": "Meera"}]


def test_ex05_none_never_overwrites():
    old = [{"id": 1, "email": "a@example.com", "site": "BLR-01"}]
    new = [{"id": 1, "email": None, "site": "HYD-01"}]
    assert merge_records(old, new) == [{"id": 1, "email": "a@example.com", "site": "HYD-01"}]


def test_ex05_none_is_kept_when_nothing_to_protect():
    assert merge_records([{"id": 1, "x": None}], [{"id": 1, "x": None}]) == [{"id": 1, "x": None}]


def test_ex05_new_fields_are_added():
    assert merge_records([{"id": 1}], [{"id": 1, "x": 5}]) == [{"id": 1, "x": 5}]


def test_ex05_duplicates_inside_one_list_are_merged():
    assert merge_records([{"id": 1, "a": 1}, {"id": 1, "a": 2}], []) == [{"id": 1, "a": 2}]


def test_ex05_does_not_mutate_inputs():
    old = [{"id": 1, "a": 1}]
    new = [{"id": 1, "a": 2}]
    merge_records(old, new)
    assert old == [{"id": 1, "a": 1}] and new == [{"id": 1, "a": 2}]


def test_ex05_custom_key_and_empty():
    assert merge_records([], []) == []
    assert merge_records([{"sku": "a", "n": 1}], [{"sku": "a", "n": 2}], key="sku") == [{"sku": "a", "n": 2}]


# ---------------------------------------------------------------------- ex06
class Flaky:
    def __init__(self, fail_times, exc=ConnectionError):
        self.fail_times, self.exc, self.calls = fail_times, exc, 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc(f"fail {self.calls}")
        return "ok"


def test_ex06_success_first_time_no_sleep():
    sleeps = []
    assert call_with_retry(Flaky(0), sleep=sleeps.append) == "ok"
    assert sleeps == []


def test_ex06_backoff_doubles():
    sleeps = []
    f = Flaky(2)
    assert call_with_retry(f, attempts=4, base_delay=0.5, sleep=sleeps.append) == "ok"
    assert f.calls == 3 and sleeps == [0.5, 1.0]


def test_ex06_gives_up_and_reraises_last_error_without_final_sleep():
    sleeps = []
    f = Flaky(10)
    with pytest.raises(ConnectionError, match="fail 3"):
        call_with_retry(f, attempts=3, base_delay=1, sleep=sleeps.append)
    assert f.calls == 3 and sleeps == [1, 2]


def test_ex06_other_exceptions_are_not_retried():
    sleeps = []
    f = Flaky(5, exc=ValueError)
    with pytest.raises(ValueError):
        call_with_retry(f, retry_on=(ConnectionError,), sleep=sleeps.append)
    assert f.calls == 1 and sleeps == []


def test_ex06_single_attempt_means_no_retry():
    f = Flaky(1)
    with pytest.raises(ConnectionError):
        call_with_retry(f, attempts=1, sleep=lambda s: None)
    assert f.calls == 1


def test_ex06_invalid_attempts():
    with pytest.raises(ValueError):
        call_with_retry(lambda: 1, attempts=0)


# ---------------------------------------------------------------------- ex07
def test_ex07_nested_dicts_and_lists():
    assert flatten_json({"a": {"b": 1}, "c": [10, {"d": 2}]}) == {"a.b": 1, "c.0": 10, "c.1.d": 2}


def test_ex07_custom_separator_and_order():
    out = flatten_json({"z": {"y": 1}, "a": 2}, sep="/")
    assert list(out.items()) == [("z/y", 1), ("a", 2)]


def test_ex07_empty_containers_and_none_are_leaves():
    assert flatten_json({"a": {}, "b": [], "c": None}) == {"a": {}, "b": [], "c": None}


def test_ex07_falsy_scalars_survive():
    assert flatten_json({"a": 0, "b": False, "c": ""}) == {"a": 0, "b": False, "c": ""}


def test_ex07_top_level_cases():
    assert flatten_json({}) == {"": {}}
    assert flatten_json(5) == {"": 5}
    assert flatten_json([1, [2, 3]]) == {"0": 1, "1.0": 2, "1.1": 3}


def test_ex07_does_not_share_state_between_calls():
    flatten_json({"a": 1})
    assert flatten_json({"b": 2}) == {"b": 2}


# ---------------------------------------------------------------------- ex08
def test_ex08a_basic_and_tie_break():
    assert top_k_frequent("bbaaccd", 3) == [("a", 2), ("b", 2), ("c", 2)]
    assert top_k_frequent(["x", "y", "y", "z", "z", "z"], 2) == [("z", 3), ("y", 2)]


def test_ex08a_edges():
    assert top_k_frequent([], 3) == []
    assert top_k_frequent(["a"], 5) == [("a", 1)]
    assert top_k_frequent(["a", "b"], 0) == []
    assert top_k_frequent(["a", "b"], -2) == []


def test_ex08b_basic_and_duplicates():
    assert top_k_largest([5, 1, 9, 3, 9, 7], 3) == [9, 9, 7]
    assert top_k_largest([1, 2], 5) == [2, 1]
    assert top_k_largest([1, 2], 0) == []


def test_ex08b_negative_numbers_and_ties_at_boundary():
    assert top_k_largest([-5, -1, -3, -1], 2) == [-1, -1]
    assert top_k_largest([4, 4, 4], 2) == [4, 4]


def test_ex08b_single_pass_over_a_generator():
    consumed = []

    def stream():
        for i in range(1000):
            consumed.append(i)
            yield (i * 7919) % 1000

    assert top_k_largest(stream(), 3) == [999, 998, 997]
    assert len(consumed) == 1000


def test_ex08b_works_on_a_bounded_slice_of_an_endless_stream():
    assert top_k_largest(itertools.islice(itertools.count(), 50), 2) == [49, 48]


# ---------------------------------------------------------------------- ex09
SCHEMA = {
    "port": {"type": int, "required": True, "min": 1, "max": 65535},
    "host": {"type": str, "required": True},
    "mode": {"type": str, "choices": ["prod", "dev"]},
    "debug": {"type": bool},
}


def test_ex09_valid_config():
    assert validate_config({"port": 8080, "host": "localhost", "mode": "dev", "debug": False}, SCHEMA) == []


def test_ex09_missing_required_and_optional_absent_is_fine():
    assert validate_config({"host": "h"}, SCHEMA) == ["port: missing"]


def test_ex09_wrong_type_and_bool_is_not_int():
    assert validate_config({"port": "80", "host": "h"}, SCHEMA) == ["port: expected int, got str"]
    assert validate_config({"port": True, "host": "h"}, SCHEMA) == ["port: expected int, got bool"]


def test_ex09_range_checks():
    assert validate_config({"port": 0, "host": "h"}, SCHEMA) == ["port: must be >= 1"]
    assert validate_config({"port": 70000, "host": "h"}, SCHEMA) == ["port: must be <= 65535"]
    assert validate_config({"port": 1, "host": "h"}, SCHEMA) == []
    assert validate_config({"port": 65535, "host": "h"}, SCHEMA) == []


def test_ex09_choices_message_is_sorted():
    assert validate_config({"port": 1, "host": "h", "mode": "qa"}, SCHEMA) == ["mode: must be one of ['dev', 'prod']"]


def test_ex09_unknown_keys_and_sorted_output():
    errs = validate_config({"zzz": 1, "port": "x"}, SCHEMA)
    assert errs == ["host: missing", "port: expected int, got str", "zzz: unknown key"]


def test_ex09_no_range_check_after_type_error():
    assert validate_config({"port": "abc", "host": "h"}, SCHEMA) == ["port: expected int, got str"]


def test_ex09_empty_schema():
    assert validate_config({}, {}) == []
    assert validate_config({"a": 1}, {}) == ["a: unknown key"]


# ---------------------------------------------------------------------- ex10
def test_ex10_all_three_buckets():
    ours = {"b-1": "active", "b-2": "active", "b-3": "revoked"}
    theirs = {"b-2": "revoked", "b-3": "revoked", "b-9": "active"}
    assert reconcile(ours, theirs) == {
        "missing_in_theirs": ["b-1"], "missing_in_ours": ["b-9"], "mismatched": ["b-2"]}


def test_ex10_identical_and_empty():
    empty = {"missing_in_theirs": [], "missing_in_ours": [], "mismatched": []}
    assert reconcile({}, {}) == empty
    assert reconcile({"a": 1}, {"a": 1}) == empty


def test_ex10_results_are_sorted():
    r = reconcile({"c": 1, "a": 1, "b": 1}, {})
    assert r["missing_in_theirs"] == ["a", "b", "c"]


def test_ex10_none_value_is_a_value():
    assert reconcile({"a": None}, {"a": 0})["mismatched"] == ["a"]
