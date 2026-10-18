"""A transparent weighted scorer: you set the weights, you rate each criterion 1 to 5."""


def normalise_weights(weights):
    """Return the weights scaled to sum to 1.

    Raises ValueError if any weight is negative or the total is zero.
    """
    raise NotImplementedError


def score(ratings, weights):
    """Weighted average of ratings, rounded to 2 places.

    ratings and weights are dicts keyed by criterion. Every criterion that has a
    weight must have a rating between 1 and 5 inclusive; otherwise ValueError.
    Ratings for criteria with no weight are ignored.
    """
    raise NotImplementedError


def rank(roles, weights):
    """Return [(name, score)] sorted by score descending, ties broken by name A to Z."""
    raise NotImplementedError


def close_call(ranked, margin=0.25):
    """True when the top two scores differ by less than margin (a tie is a close call).

    Needs at least two entries; with fewer, return False.
    """
    raise NotImplementedError
