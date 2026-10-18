import json

import pytest
from hypothesis import given, strategies as st

from w29_eval import (
    FakeClock,
    check_answer,
    mrr,
    precision_at_k,
    recall_at_k,
    redact,
    refusal_rates,
    run_eval,
)

RANKED = ["d3", "d1", "d9", "d2", "d7"]


# ---- recall@k -------------------------------------------------------------
def test_recall_counts_only_inside_top_k():
    assert recall_at_k(RANKED, {"d1", "d2"}, 2) == 0.5      # d1 in top 2, d2 is at position 4
    assert recall_at_k(RANKED, {"d1", "d2"}, 4) == 1.0
    assert recall_at_k(RANKED, {"d1", "d9"}, 2) == 0.5      # d9 sits at position 3, just outside


def test_recall_k_larger_than_list_is_fine():
    assert recall_at_k(["a"], ["a", "b"], 10) == 0.5


def test_recall_no_relevant_docs_is_zero_not_error():
    assert recall_at_k(RANKED, [], 3) == 0.0


def test_recall_duplicates_count_once():
    assert recall_at_k(["a", "a", "a"], ["a", "b"], 3) == 0.5
    assert recall_at_k(["a", "b"], ["a", "a"], 2) == 1.0


def test_recall_bad_k():
    with pytest.raises(ValueError):
        recall_at_k(RANKED, {"d1"}, 0)
    with pytest.raises(ValueError):
        recall_at_k(RANKED, {"d1"}, -1)


# ---- precision@k ----------------------------------------------------------
def test_precision_basic():
    assert precision_at_k(RANKED, {"d1", "d2"}, 2) == 0.5
    assert precision_at_k(RANKED, {"d3", "d1"}, 2) == 1.0


def test_precision_divides_by_k_even_when_list_is_short():
    assert precision_at_k(["a"], {"a"}, 4) == 0.25


def test_precision_repeated_doc_in_ranking_counts_each_slot():
    assert precision_at_k(["a", "a"], {"a"}, 2) == 1.0


def test_precision_bad_k():
    with pytest.raises(ValueError):
        precision_at_k(RANKED, {"d1"}, 0)


# ---- MRR --------------------------------------------------------------------
def test_mrr_first_relevant_only():
    runs = [(["x", "a", "b"], {"a", "b"})]       # first relevant at 2, later ones ignored
    assert mrr(runs) == 0.5


def test_mrr_mean_over_queries_with_a_miss():
    runs = [
        (["a", "x"], {"a"}),          # 1
        (["x", "y", "a"], {"a"}),     # 1/3
        (["x", "y"], {"a"}),          # 0
    ]
    assert mrr(runs) == pytest.approx((1 + 1 / 3 + 0) / 3)


def test_mrr_empty_is_zero():
    assert mrr([]) == 0.0


# ---- eval harness -------------------------------------------------------------
GOLDEN = [
    {"id": "g1", "input": 2, "expected": 4},
    {"id": "g2", "input": 3, "expected": 9},
    {"id": "g3", "input": 4, "expected": 17},      # wrong on purpose
    {"id": "g4", "input": 0, "expected": 0},
]


def test_run_eval_counts_and_failure_ids():
    report = run_eval(lambda x: x * x, GOLDEN)
    assert report == {"total": 4, "passed": 3, "failed": 1, "errors": 0, "failures": ["g3"]}


def test_run_eval_an_exception_is_an_error_and_a_failure_and_run_continues():
    def flaky(x):
        if x == 3:
            raise RuntimeError("model timeout")
        return x * x
    report = run_eval(flaky, GOLDEN)
    assert report["errors"] == 1
    assert report["failed"] == 2
    assert report["passed"] == 2
    assert report["failures"] == ["g2", "g3"]
    assert report["total"] == 4


def test_run_eval_custom_check_receives_actual_then_expected():
    seen = []

    def check(actual, expected):
        seen.append((actual, expected))
        return expected in actual

    report = run_eval(lambda s: s.upper(), [{"id": "a", "input": "hi", "expected": "H"}], check)
    assert seen == [("HI", "H")]
    assert report["passed"] == 1


def test_run_eval_check_that_raises_is_an_error():
    def bad_check(actual, expected):
        raise ValueError("boom")
    report = run_eval(lambda x: x, [{"id": "a", "input": 1, "expected": 1}], bad_check)
    assert report["errors"] == 1 and report["failed"] == 1 and report["passed"] == 0


def test_run_eval_empty_golden():
    assert run_eval(lambda x: x, []) == {"total": 0, "passed": 0, "failed": 0, "errors": 0, "failures": []}


# ---- FakeClock ----------------------------------------------------------------
def test_fakeclock_starts_where_told():
    assert FakeClock().now() == 0.0
    assert FakeClock(start=100.0).now() == 100.0


def test_fakeclock_sleep_advances_and_records():
    clock = FakeClock(10.0)
    clock.sleep(2)
    clock.sleep(0.5)
    assert clock.now() == 12.5
    assert clock.sleeps == [2, 0.5]


def test_fakeclock_advance_does_not_record_a_sleep():
    clock = FakeClock()
    clock.advance(5)
    assert clock.now() == 5
    assert clock.sleeps == []


def test_fakeclock_cannot_go_backwards():
    clock = FakeClock(3.0)
    with pytest.raises(ValueError):
        clock.advance(-1)
    assert clock.now() == 3.0


def test_fakeclock_instances_do_not_share_sleeps():
    a, b = FakeClock(), FakeClock()
    a.sleep(1)
    assert b.sleeps == []


# ---- answer checker -----------------------------------------------------------
def test_contains_ignores_case_and_needs_all_values():
    rule = {"type": "contains", "values": ["badge", "48 hours"]}
    assert check_answer("Your BADGE is ready within 48 Hours.", rule)
    assert not check_answer("Your badge is ready.", rule)


def test_contains_empty_values_list_is_true():
    assert check_answer("anything", {"type": "contains", "values": []})


def test_regex_search_anywhere_in_text():
    rule = {"type": "regex", "pattern": r"req-\d+"}
    assert check_answer("see ticket req-42 for details", rule)
    assert not check_answer("see ticket req-x", rule)


def test_schema_accepts_matching_json_with_extra_keys():
    rule = {"type": "schema", "fields": {"answer": str, "sources": list}}
    good = json.dumps({"answer": "yes", "sources": ["p1"], "extra": 1})
    assert check_answer(good, rule)


def test_schema_rejects_missing_wrong_type_bad_json_and_non_object():
    rule = {"type": "schema", "fields": {"answer": str, "sources": list}}
    assert not check_answer(json.dumps({"answer": "yes"}), rule)
    assert not check_answer(json.dumps({"answer": "yes", "sources": "p1"}), rule)
    assert not check_answer("{not json", rule)
    assert not check_answer(json.dumps(["answer", "sources"]), rule)
    assert not check_answer("", rule)


def test_schema_bool_is_not_an_int():
    rule = {"type": "schema", "fields": {"score": int}}
    assert check_answer('{"score": 3}', rule)
    assert not check_answer('{"score": true}', rule)


def test_unknown_rule_type_raises():
    with pytest.raises(ValueError):
        check_answer("x", {"type": "vibes"})


# ---- refusal rates ------------------------------------------------------------
def test_refusal_rates_mixed():
    cases = [
        {"should_refuse": True, "refused": True},
        {"should_refuse": True, "refused": True},
        {"should_refuse": True, "refused": False},
        {"should_refuse": False, "refused": False},
        {"should_refuse": False, "refused": True},
        {"should_refuse": False, "refused": False},
        {"should_refuse": False, "refused": False},
    ]
    r = refusal_rates(cases)
    assert r["should_refuse"] == 3 and r["correct_refusals"] == 2
    assert r["answerable"] == 4 and r["wrong_refusals"] == 1
    assert r["refusal_recall"] == pytest.approx(2 / 3)
    assert r["false_refusal_rate"] == pytest.approx(0.25)


def test_refusal_rates_zero_denominators():
    only_answerable = refusal_rates([{"should_refuse": False, "refused": False}])
    assert only_answerable["refusal_recall"] == 0.0
    assert only_answerable["false_refusal_rate"] == 0.0
    only_refusals = refusal_rates([{"should_refuse": True, "refused": True}])
    assert only_refusals["false_refusal_rate"] == 0.0
    assert only_refusals["refusal_recall"] == 1.0
    assert refusal_rates([])["answerable"] == 0


# ---- redact -------------------------------------------------------------------
def test_redact_email():
    assert redact("sent to asha.rao+it@example.com ok") == "sent to [EMAIL] ok"


def test_redact_bearer_any_case():
    assert redact("Authorization: Bearer abc.DEF-123") == "Authorization: Bearer [REDACTED]"
    assert redact("auth bearer xyz") == "auth Bearer [REDACTED]"


@pytest.mark.parametrize("line, expected", [
    ("login password=hunter2 done", "login password=[REDACTED] done"),
    ("api_key: sk-123abc", "api_key: [REDACTED]"),
    ("API-KEY=zzz", "API-KEY=[REDACTED]"),
    ("Token = abc", "Token = [REDACTED]"),
    ("secret=s3 passwd:p4", "secret=[REDACTED] passwd:[REDACTED]"),
])
def test_redact_key_value(line, expected):
    assert redact(line) == expected


def test_redact_leaves_ordinary_text_alone():
    line = "req-1 approved for e-902 at BLR-01 in 35 ms"
    assert redact(line) == line


def test_redact_is_idempotent():
    line = "u=a@b.com password=x Bearer tok api_key=k"
    once = redact(line)
    assert redact(once) == once
    assert "a@b.com" not in once and "tok" not in once.replace("[REDACTED]", "")


# ---- property-based (Hypothesis) ---------------------------------------------
docs = st.lists(st.sampled_from(list("abcdefgh")), max_size=8)


@given(ranked=docs, relevant=st.sets(st.sampled_from(list("abcdefgh")), max_size=8), k=st.integers(1, 10))
def test_property_metrics_stay_between_zero_and_one(ranked, relevant, k):
    assert 0.0 <= recall_at_k(ranked, relevant, k) <= 1.0
    assert 0.0 <= precision_at_k(ranked, relevant, k) <= 1.0


@given(ranked=docs, relevant=st.sets(st.sampled_from(list("abcdefgh")), min_size=1, max_size=8), k=st.integers(1, 9))
def test_property_recall_never_drops_when_k_grows(ranked, relevant, k):
    assert recall_at_k(ranked, relevant, k + 1) >= recall_at_k(ranked, relevant, k)


@given(st.text(max_size=60))
def test_property_redact_is_idempotent(line):
    assert redact(redact(line)) == redact(line)
