"""Crude keyword overlap between a job posting and your evidence file.

A keyword overlap is an aid for noticing gaps. It is not a verdict on whether you
should apply: it cannot read context, seniority or how deep your evidence goes.
"""
import re


def find_terms(text, vocab):
    """Return the sorted list of vocabulary terms that appear in text.

    Matching is case-insensitive and whole-term: 'rag' must not match 'storage',
    and 'c++' must be found next to punctuation. Terms may contain spaces
    ('vector database'). Duplicates in vocab are reported once.
    """
    raise NotImplementedError


def parse_evidence(text):
    """Parse 'term | link' lines into {term: link}.

    Blank lines and lines starting with '#' are ignored. Terms are lower-cased
    and stripped. A line with no '|' (or an empty link) keeps the term with the
    link '' : a claim without evidence.
    """
    raise NotImplementedError


def match_report(posting, evidence, vocab):
    """Compare the posting's vocabulary terms with an evidence dict.

    Returns a dict with:
      terms       sorted terms found in the posting
      matched     {term: link} for terms with a non-empty evidence link
      unevidenced sorted terms you listed but with no link (do not count as matched)
      gaps        sorted terms in the posting that are not in your evidence at all
      coverage    len(matched) / len(terms), rounded to 2 places; 0.0 if no terms
    """
    raise NotImplementedError
