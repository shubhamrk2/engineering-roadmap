"""Week 29 lab: testing and evaluation helpers. Replace every `raise NotImplementedError`.

Run from python-lab/:   pytest week29 -q
Tests are the spec. Do not edit test_w29_eval.py.
"""


def recall_at_k(ranked, relevant, k):
    """Fraction of the relevant documents that appear in the first k results.

    ranked: list of doc ids, best first. relevant: any iterable of doc ids (duplicates count once).
    recall@k = |relevant docs found in ranked[:k]| / |relevant|. A doc repeated in ranked counts once.
    If there are no relevant docs return 0.0. If k <= 0 raise ValueError.
    """
    raise NotImplementedError


def precision_at_k(ranked, relevant, k):
    """Fraction of the first k slots that hold a relevant doc.

    precision@k = (relevant docs in ranked[:k]) / k. Divide by k even if ranked has fewer than k items
    (empty slots are not hits). If k <= 0 raise ValueError.
    """
    raise NotImplementedError


def mrr(runs):
    """Mean reciprocal rank over several queries.

    runs: list of (ranked, relevant) pairs. For each query the score is 1/position of the FIRST relevant
    doc in ranked (positions start at 1), or 0 if none appears. Return the mean over queries.
    An empty list of runs returns 0.0.
    """
    raise NotImplementedError


def run_eval(fn, golden, check=None):
    """Run fn over a golden set and report counts.

    golden: list of {"id": str, "input": ..., "expected": ...}.
    check(actual, expected) -> bool decides a pass; the default is plain equality.
    If fn or check raises, the case is an error AND a failure (it must not stop the run).
    Return {"total", "passed", "failed", "errors", "failures"} where failures is the list of failing
    case ids in golden order and failed includes the errors.
    """
    raise NotImplementedError


class FakeClock:
    """A clock a test controls. No real waiting.

    FakeClock(start=0.0). now() returns the current fake time (float).
    advance(seconds) moves time forward; negative raises ValueError.
    sleep(seconds) advances time by that amount AND records the requested value in self.sleeps (a list).
    """

    def __init__(self, start=0.0):
        raise NotImplementedError

    def now(self):
        raise NotImplementedError

    def advance(self, seconds):
        raise NotImplementedError

    def sleep(self, seconds):
        raise NotImplementedError


def check_answer(answer, rule):
    """Check one model answer (a string) against one rule (a dict). Return True/False.

    {"type": "contains", "values": [...]}  every value appears in the answer, ignoring case.
    {"type": "regex", "pattern": "..."}    re.search(pattern, answer) finds a match.
    {"type": "schema", "fields": {"answer": str, "sources": list}}
        the answer must parse as JSON, be a JSON object (dict), and contain every field with the right
        type. Extra keys are allowed. A JSON true/false must NOT count as an int.
        Invalid JSON returns False (does not raise).
    Any other type raises ValueError.
    """
    raise NotImplementedError


def refusal_rates(cases):
    """Summarise refusal behaviour.

    cases: list of {"should_refuse": bool, "refused": bool}.
    Return a dict with: should_refuse (count of cases that should be refused), correct_refusals (of those,
    how many were refused), answerable (cases that should NOT be refused), wrong_refusals (of those, how many
    were refused), refusal_recall = correct_refusals / should_refuse, false_refusal_rate =
    wrong_refusals / answerable. A ratio with a zero denominator is 0.0.
    """
    raise NotImplementedError


def redact(line):
    """Remove sensitive values from a log line. Must be idempotent (redacting twice changes nothing more).

    - email addresses become [EMAIL]
    - "Bearer <token>" (any case of the word Bearer) becomes "Bearer [REDACTED]"
    - key=value or key: value where key is password, passwd, token, secret, api_key or api-key (any case)
      keeps the key and separator and replaces the value with [REDACTED]
    Everything else (for example employee id e-902 or site BLR-01) is left alone.
    """
    raise NotImplementedError
