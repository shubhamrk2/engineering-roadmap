"""Week 2: lists, tuples, sets, dictionaries, strings.

Replace each `raise NotImplementedError` with your own code.
Run:  pytest week02
"""


def unique_in_order(items):
    """ex01. Return a new list with duplicates removed, keeping first-seen order.

    unique_in_order([3, 1, 3, 2, 1]) -> [3, 1, 2]
    Do not change the list that was passed in.
    """
    raise NotImplementedError


def word_counts(text):
    """ex02. Count words in text, ignoring upper/lower case. Words are separated by whitespace.

    word_counts("The the THE cat") -> {"the": 3, "cat": 1}
    Empty or whitespace-only text -> {}
    """
    raise NotImplementedError


def group_by_site(requests):
    """ex03. `requests` is a list of dicts like {"id": "req-1", "site": "BLR-01"}.

    Return a dict mapping each site to the list of request ids at that site,
    in the order the requests appeared.
    [] -> {}
    """
    raise NotImplementedError


def parse_log_line(line):
    """ex04. Split a log line into a dict, or return None if it is malformed.

    "2026-10-18 09:01:12 ERROR payments Timeout calling gateway" ->
        {"date": "2026-10-18", "time": "09:01:12", "level": "ERROR",
         "service": "payments", "message": "Timeout calling gateway"}

    A line is malformed (return None) when it has fewer than five whitespace-separated parts,
    including an empty or whitespace-only line. The message is everything after the service,
    joined back with single spaces.
    """
    raise NotImplementedError


def count_errors(lines):
    """ex05. The original diagnostic.

    `lines` is a list of log lines. Return a dict mapping each service name to the number of
    lines whose level is exactly "ERROR". Skip malformed lines. No lines -> {}.

    Hint: you already wrote parse_log_line. Using it is allowed and sensible.
    """
    raise NotImplementedError


def top_n(counts, n):
    """ex06. `counts` is a dict of name -> number. Return the n biggest as a list of
    (name, number) tuples, biggest first. Break ties by name, A to Z.

    top_n({"a": 2, "b": 5, "c": 2}, 2) -> [("b", 5), ("a", 2)]
    n larger than the dict returns everything; n of 0 returns [].
    """
    raise NotImplementedError
