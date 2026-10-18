"""Tests for w36_keyword_match. All postings here are invented."""
import pytest

from w36_keyword_match import find_terms, match_report, parse_evidence

VOCAB = ["python", "fastapi", "rag", "c++", "vector database", "kubernetes", "ci/cd"]

POSTING = """
Invented posting: Applied AI Engineer (not a real vacancy).
You will build RAG services in Python and FastAPI, store embeddings in a
vector database, and ship through CI/CD. Kubernetes is a plus.
"""


def test_find_terms_is_case_insensitive_and_sorted():
    assert find_terms("PYTHON and FastAPI", VOCAB) == ["fastapi", "python"]


def test_find_terms_requires_whole_term():
    # 'rag' must not match inside 'storage' or 'fragment'
    assert find_terms("storage fragment", VOCAB) == []


def test_find_terms_handles_punctuation_terms():
    assert find_terms("Some C++, some CI/CD.", VOCAB) == ["c++", "ci/cd"]


def test_find_terms_does_not_match_longer_token():
    assert find_terms("we use c++17 daily", VOCAB) == []


def test_find_terms_multi_word_and_dedupes_vocab():
    assert find_terms("a Vector Database", ["vector database", "Vector Database"]) == ["vector database"]


def test_find_terms_ignores_blank_vocab_entries():
    assert find_terms("anything", ["", "  "]) == []


def test_parse_evidence_basic_and_comments():
    text = """
    # my evidence
    Python | https://example.com/repo
    FastAPI | https://example.com/api

    RAG
    """
    assert parse_evidence(text) == {
        "python": "https://example.com/repo",
        "fastapi": "https://example.com/api",
        "rag": "",
    }


def test_parse_evidence_keeps_pipes_in_link_out_of_term():
    assert parse_evidence("ci/cd | https://x.test/a|b") == {"ci/cd": "https://x.test/a|b"}


def test_match_report_splits_matched_unevidenced_gaps():
    evidence = {"python": "https://example.com/p", "rag": "", "fastapi": "https://example.com/f"}
    rep = match_report(POSTING, evidence, VOCAB)
    assert rep["terms"] == ["ci/cd", "fastapi", "kubernetes", "python", "rag", "vector database"]
    assert rep["matched"] == {"fastapi": "https://example.com/f", "python": "https://example.com/p"}
    assert rep["unevidenced"] == ["rag"]
    assert rep["gaps"] == ["ci/cd", "kubernetes", "vector database"]
    assert rep["coverage"] == pytest.approx(0.33)


def test_match_report_coverage_zero_when_posting_has_no_vocab_terms():
    rep = match_report("We value teamwork.", {"python": "x"}, VOCAB)
    assert rep["terms"] == [] and rep["coverage"] == 0.0


def test_match_report_full_coverage():
    ev = {t: "link" for t in VOCAB}
    assert match_report(POSTING, ev, VOCAB)["coverage"] == 1.0


def test_find_terms_does_not_match_inside_a_longer_word_on_the_left():
    assert find_terms("cpython and ipython", VOCAB) == []
