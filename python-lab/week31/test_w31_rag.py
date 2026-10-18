"""Tests for week 31. Do not edit. Each test name starts with the exercise number it marks.

Fakes only: no network, no model, no GPU. Run:  pytest week31
"""
import math

import pytest

from w31_rag import (
    REFUSAL_MESSAGE, FakeLLM, answer_with_citations, build_context, chunk_by_headings, chunk_text,
    cosine, embed, mrr, recall_at_k, reciprocal_rank_fusion, refuse_if_low_similarity, top_k,
    verify_citations,
)


# ---------------------------------------------------------------- ex01 cosine
def test_ex01_identical_vectors_score_one():
    assert cosine([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_ex01_orthogonal_vectors_score_zero():
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)


def test_ex01_opposite_vectors_score_minus_one():
    assert cosine([1, 2], [-1, -2]) == pytest.approx(-1.0)


def test_ex01_ignores_length_but_not_direction():
    assert cosine([1, 1], [10, 10]) == pytest.approx(1.0)
    assert cosine([3, 4], [4, 3]) == pytest.approx(24 / 25)


def test_ex01_zero_vector_is_zero_not_a_crash():
    assert cosine([0, 0, 0], [1, 2, 3]) == 0.0
    assert cosine([1, 2, 3], [0, 0, 0]) == 0.0


def test_ex01_length_mismatch_raises():
    with pytest.raises(ValueError):
        cosine([1, 2], [1, 2, 3])


# ---------------------------------------------------------------- ex02 chunk_text
def test_ex02_example_from_docstring():
    assert chunk_text("abcdefghij", 4, 1) == ["abcd", "defg", "ghij"]


def test_ex02_no_overlap():
    assert chunk_text("abcdefghij", 5) == ["abcde", "fghij"]
    assert chunk_text("abcdefg", 3) == ["abc", "def", "g"]


def test_ex02_text_shorter_than_size_is_one_chunk():
    assert chunk_text("abc", 10, 2) == ["abc"]


def test_ex02_empty_text():
    assert chunk_text("", 5, 1) == []


def test_ex02_no_chunk_that_is_only_overlap():
    # window 0 = "abcd" already... window 1 = "cdef" reaches the end; a third window "ef" would be pure overlap
    assert chunk_text("abcdef", 4, 2) == ["abcd", "cdef"]


def test_ex02_every_character_is_covered_in_order():
    text = "the quick brown fox jumps over the lazy dog" * 3
    chunks = chunk_text(text, 17, 5)
    rebuilt = chunks[0] + "".join(c[5:] for c in chunks[1:])
    assert rebuilt == text


@pytest.mark.parametrize("size, overlap", [(0, 0), (-1, 0), (4, 4), (4, 5), (4, -1)])
def test_ex02_bad_settings_raise(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("abcdef", size, overlap)


# ---------------------------------------------------------------- ex03 chunk_by_headings
DOC = """Intro line before any heading.

# Passwords
Use 14 characters.
Rotate every 180 days.

## MFA

## Contractors
Accounts expire after 90 days.
"""


def test_ex03_sections_ids_and_headings():
    chunks = chunk_by_headings(DOC, "pol.md")
    assert [c["heading"] for c in chunks] == ["", "Passwords", "Contractors"]
    assert [c["id"] for c in chunks] == ["pol.md#0", "pol.md#1", "pol.md#2"]
    assert all(c["source"] == "pol.md" for c in chunks)


def test_ex03_text_excludes_heading_line_and_is_stripped():
    chunks = chunk_by_headings(DOC, "pol.md")
    assert chunks[0]["text"] == "Intro line before any heading."
    assert chunks[1]["text"] == "Use 14 characters.\nRotate every 180 days."
    assert chunks[2]["text"] == "Accounts expire after 90 days."


def test_ex03_empty_section_is_skipped_and_does_not_use_a_number():
    chunks = chunk_by_headings("# A\nx\n## Empty\n# C\ny", "s")
    assert [(c["id"], c["heading"]) for c in chunks] == [("s#0", "A"), ("s#1", "C")]


def test_ex03_no_headings_is_one_chunk_and_empty_input_is_none():
    assert [c["text"] for c in chunk_by_headings("just text\nmore", "s")] == ["just text\nmore"]
    assert chunk_by_headings("", "s") == []


def test_ex03_a_hash_without_a_space_is_not_a_heading():
    chunks = chunk_by_headings("# Real\n#hashtag stays in the body", "s")
    assert len(chunks) == 1 and "#hashtag" in chunks[0]["text"]


# ---------------------------------------------------------------- ex04 top_k
def test_ex04_best_first_with_scores():
    vectors = [[0, 1], [1, 0], [1, 1]]
    result = top_k([1, 0], vectors, 3)
    assert [i for i, _ in result] == [1, 2, 0]
    assert result[0][1] == pytest.approx(1.0)
    assert result[1][1] == pytest.approx(1 / math.sqrt(2))


def test_ex04_k_limits_and_oversized_k_returns_all():
    vectors = [[1, 0], [0, 1], [1, 1]]
    assert len(top_k([1, 0], vectors, 2)) == 2
    assert len(top_k([1, 0], vectors, 99)) == 3
    assert top_k([1, 0], vectors, 0) == []


def test_ex04_ties_go_to_the_lower_index():
    vectors = [[1, 0], [2, 0], [0, 1]]
    assert [i for i, _ in top_k([1, 0], vectors, 2)] == [0, 1]


def test_ex04_works_with_the_toy_embedding():
    texts = ["reset your password", "lost laptop report", "vpn error 809"]
    vectors = [embed(t) for t in texts]
    assert top_k(embed("password reset"), vectors, 1)[0][0] == 0
    assert top_k(embed("vpn 809"), vectors, 1)[0][0] == 2


# ---------------------------------------------------------------- ex05 reciprocal_rank_fusion
def test_ex05_scores_follow_the_formula():
    fused = dict(reciprocal_rank_fusion([["a", "b"], ["b", "a"]], k=60))
    assert fused["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)


def test_ex05_agreement_beats_a_single_first_place():
    # "b" is second in both lists; "a" is first in only one list
    fused = reciprocal_rank_fusion([["a", "b"], ["c", "b"]], k=60)
    assert fused[0][0] == "b"


def test_ex05_id_missing_from_one_ranking_still_counts():
    fused = dict(reciprocal_rank_fusion([["a"], ["b", "a"]], k=10))
    assert fused["b"] == pytest.approx(1 / 11)
    assert fused["a"] == pytest.approx(1 / 11 + 1 / 12)


def test_ex05_default_k_is_60_and_ties_break_by_id():
    fused = reciprocal_rank_fusion([["z"], ["a"]])
    assert fused[0] == ("a", pytest.approx(1 / 61))
    assert fused[1][0] == "z"


def test_ex05_no_rankings():
    assert reciprocal_rank_fusion([]) == []


# ---------------------------------------------------------------- ex06 build_context
CHUNKS = [
    {"id": "a", "text": "one two three"},      # entry "[a] one two three" = 4 words
    {"id": "b", "text": "four five"},          # 3 words
    {"id": "c", "text": "six"},                # 2 words
]


def test_ex06_everything_fits():
    ctx, used = build_context(CHUNKS, 100)
    assert ctx == "[a] one two three\n\n[b] four five\n\n[c] six"
    assert used == CHUNKS


def test_ex06_budget_is_inclusive():
    _, used = build_context(CHUNKS, 7)          # 4 + 3 = 7 exactly
    assert [c["id"] for c in used] == ["a", "b"]


def test_ex06_stops_at_first_chunk_that_does_not_fit():
    # budget 5: a (4) fits, b (3) does not, c (2) WOULD fit but must not jump the queue
    ctx, used = build_context(CHUNKS, 5)
    assert [c["id"] for c in used] == ["a"]
    assert ctx == "[a] one two three"


def test_ex06_budget_too_small_for_the_first_chunk():
    assert build_context(CHUNKS, 3) == ("", [])


def test_ex06_counter_is_injectable_and_counts_the_whole_entry():
    seen = []

    def by_chars(text):
        seen.append(text)
        return len(text)

    ctx, used = build_context(CHUNKS, 20, count_tokens=by_chars)
    assert seen[0] == "[a] one two three"        # the counter sees the formatted entry
    assert [c["id"] for c in used] == ["a"]       # 17 chars; next entry (13) would make 30 > 20
    assert ctx == "[a] one two three"


# ---------------------------------------------------------------- ex07 answer_with_citations
SOURCES = [
    {"id": "pol#1", "text": "Contractor accounts expire after 90 days."},
    {"id": "pol#2", "text": "MFA is mandatory for VPN."},
]


def test_ex07_prompt_contains_instructions_sources_and_question():
    llm = FakeLLM("Contractors expire after 90 days [pol#1].")
    out = answer_with_citations("When do contractor accounts expire?", SOURCES, llm)
    p = out["prompt"]
    assert "Answer using ONLY the sources below and cite them like [id]." in p
    assert "If the sources do not contain the answer, say: I do not know." in p
    assert "[pol#1] Contractor accounts expire after 90 days." in p
    assert "[pol#2] MFA is mandatory for VPN." in p
    assert p.rstrip().endswith("Question: When do contractor accounts expire?")
    assert llm.prompts == [p]                      # the model was called once with exactly this prompt


def test_ex07_answer_is_returned_unchanged():
    out = answer_with_citations("q", SOURCES, FakeLLM("Ninety days [pol#1]."))
    assert out["answer"] == "Ninety days [pol#1]."


def test_ex07_citations_deduplicated_in_order_of_first_appearance():
    out = answer_with_citations("q", SOURCES, FakeLLM("A [pol#2]. B [pol#1]. C [pol#2]."))
    assert out["citations"] == ["pol#2", "pol#1"]


def test_ex07_no_citations_gives_empty_list():
    out = answer_with_citations("q", SOURCES, FakeLLM("I do not know."))
    assert out["citations"] == []


def test_ex07_citations_are_reported_even_if_fabricated():
    out = answer_with_citations("q", SOURCES, FakeLLM("Made up [ghost#9]."))
    assert out["citations"] == ["ghost#9"]          # verifying is ex08's job


# ---------------------------------------------------------------- ex08 verify_citations
def test_ex08_splits_valid_and_invalid_keeping_order():
    valid, invalid = verify_citations(["pol#2", "ghost#9", "pol#1", "x"], SOURCES)
    assert valid == ["pol#2", "pol#1"]
    assert invalid == ["ghost#9", "x"]


def test_ex08_empty_citations():
    assert verify_citations([], SOURCES) == ([], [])


def test_ex08_a_real_chunk_that_was_not_shown_is_invalid():
    # "pol#3" exists in the corpus but was not in the context given to the model
    assert verify_citations(["pol#3"], SOURCES) == ([], ["pol#3"])


# ---------------------------------------------------------------- ex09 refuse_if_low_similarity
def test_ex09_refuses_when_best_score_is_below_threshold():
    assert refuse_if_low_similarity([("a", 0.2), ("b", 0.1)], 0.3) == REFUSAL_MESSAGE


def test_ex09_answers_when_best_score_clears_threshold_in_any_order():
    assert refuse_if_low_similarity([("a", 0.1), ("b", 0.9), ("c", 0.2)], 0.5) is None


def test_ex09_exactly_equal_is_not_refused():
    assert refuse_if_low_similarity([("a", 0.5)], 0.5) is None


def test_ex09_no_candidates_is_a_refusal():
    assert refuse_if_low_similarity([], 0.0) == REFUSAL_MESSAGE


# ---------------------------------------------------------------- ex10 recall_at_k and ex11 mrr
RESULTS = [["a", "b", "c"], ["x", "y", "z"], ["q", "r", "s"], ["m", "n", "o"]]
EXPECTED = ["a", "z", "none", "n"]            # ranks 1, 3, absent, 2


def test_ex10_recall_at_1_2_3():
    assert recall_at_k(RESULTS, EXPECTED, 1) == pytest.approx(1 / 4)
    assert recall_at_k(RESULTS, EXPECTED, 2) == pytest.approx(2 / 4)
    assert recall_at_k(RESULTS, EXPECTED, 3) == pytest.approx(3 / 4)


def test_ex10_k_larger_than_the_lists_is_fine():
    assert recall_at_k(RESULTS, EXPECTED, 99) == pytest.approx(3 / 4)


def test_ex10_empty_and_mismatched():
    assert recall_at_k([], [], 3) == 0.0
    with pytest.raises(ValueError):
        recall_at_k([["a"]], ["a", "b"], 1)


def test_ex11_mrr_values():
    assert mrr(RESULTS, EXPECTED) == pytest.approx((1 + 1 / 3 + 0 + 1 / 2) / 4)


def test_ex11_empty_and_mismatched():
    assert mrr([], []) == 0.0
    with pytest.raises(ValueError):
        mrr([["a"]], [])
