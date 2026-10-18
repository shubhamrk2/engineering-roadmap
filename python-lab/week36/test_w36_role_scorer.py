"""Tests for w36_role_scorer. Roles and ratings are invented."""
import pytest

from w36_role_scorer import close_call, normalise_weights, rank, score

W = {"fit": 3, "pay": 1, "ready": 1}


def test_normalise_weights_sum_to_one():
    n = normalise_weights(W)
    assert n["fit"] == pytest.approx(0.6)
    assert sum(n.values()) == pytest.approx(1.0)


def test_normalise_weights_rejects_negative():
    with pytest.raises(ValueError):
        normalise_weights({"a": -1, "b": 2})


def test_normalise_weights_rejects_all_zero():
    with pytest.raises(ValueError):
        normalise_weights({"a": 0, "b": 0})


def test_zero_weight_is_allowed_alongside_positive():
    assert normalise_weights({"a": 0, "b": 2}) == {"a": 0.0, "b": 1.0}


def test_score_is_weighted_average_rounded():
    assert score({"fit": 5, "pay": 1, "ready": 1}, W) == 3.4  # 0.6*5 + 0.2 + 0.2
    assert score({"fit": 4, "pay": 3, "ready": 1}, W) == 3.2  # 2.4 + 0.6 + 0.2


def test_score_equal_weights_is_plain_mean():
    assert score({"a": 1, "b": 2, "c": 4}, {"a": 1, "b": 1, "c": 1}) == 2.33


def test_score_missing_rating_raises():
    with pytest.raises(ValueError):
        score({"fit": 5, "pay": 3}, W)


@pytest.mark.parametrize("bad", [0, 6, -1, 5.01])
def test_score_out_of_range_raises(bad):
    with pytest.raises(ValueError):
        score({"fit": bad, "pay": 3, "ready": 3}, W)


def test_score_boundaries_are_inclusive():
    assert score({"fit": 1, "pay": 5, "ready": 5}, W) == 2.6


def test_score_ignores_unweighted_ratings():
    assert score({"fit": 5, "pay": 5, "ready": 5, "vibes": 1}, W) == 5.0


def test_rank_sorts_desc_with_name_tiebreak():
    roles = {
        "zeta": {"fit": 3, "pay": 3, "ready": 3},
        "alpha": {"fit": 3, "pay": 3, "ready": 3},
        "best": {"fit": 5, "pay": 3, "ready": 3},
        "worst": {"fit": 1, "pay": 3, "ready": 3},
    }
    assert rank(roles, W) == [("best", 4.2), ("alpha", 3.0), ("zeta", 3.0), ("worst", 1.8)]


def test_changing_weights_can_change_the_order():
    roles = {"pays": {"fit": 2, "pay": 5, "ready": 3}, "fits": {"fit": 5, "pay": 2, "ready": 3}}
    assert rank(roles, {"fit": 5, "pay": 1, "ready": 1})[0][0] == "fits"
    assert rank(roles, {"fit": 1, "pay": 5, "ready": 1})[0][0] == "pays"


def test_close_call():
    assert close_call([("a", 3.5), ("b", 3.4)]) is True
    assert close_call([("a", 3.5), ("b", 3.0)]) is False
    assert close_call([("a", 3.5), ("b", 3.25)]) is False   # exactly the margin is not a close call
    assert close_call([("a", 3.5), ("b", 3.25)], margin=0.5) is True
    assert close_call([("a", 3.5)]) is False
    assert close_call([]) is False
