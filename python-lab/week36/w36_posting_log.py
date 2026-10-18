"""A plain CSV log of the postings you track, with a summary and follow-up dates."""
import csv
import os
from datetime import date, timedelta

COLUMNS = ["date_added", "company", "role", "source", "url", "status",
           "fit", "applied_on", "follow_up_on", "notes"]
STATUSES = ["saved", "applied", "screen", "interview", "take-home",
            "offer", "rejected", "withdrawn", "ghosted"]
RESPONDED = {"screen", "interview", "take-home", "offer", "rejected"}


def add_row(path, row):
    """Append one posting to the CSV at path, writing the header if the file is new.

    Missing columns are written as ''. An unknown column name or a status that is
    not in STATUSES raises ValueError (and nothing is written). A missing or empty
    status is stored as 'saved'.
    """
    raise NotImplementedError


def read_rows(path):
    """Return the rows of the CSV as a list of dicts; [] if the file does not exist."""
    raise NotImplementedError


def next_follow_up(applied_on, days=7):
    """Return the follow-up date: applied_on plus days, moved to Monday if it lands on a weekend."""
    raise NotImplementedError


def summarise(rows):
    """Count rows per status.

    Returns a dict with every status in STATUSES order (zero when absent) plus
    'total'. A status outside STATUSES is counted under 'other' (only present
    when there is at least one).
    """
    raise NotImplementedError


def due_follow_ups(rows, today):
    """Return [(company, role)] for rows still 'applied' or 'screen' whose follow_up_on is today or earlier.

    Rows with an empty or unparseable follow_up_on are skipped. Sorted by
    follow_up_on, then company.
    """
    raise NotImplementedError


def response_rate(rows):
    """Share of applied postings that got any human response.

    Only rows with a non-empty applied_on count. Responded statuses: screen,
    interview, take-home, offer, rejected. Returns a float rounded to 2 places,
    or None when nothing has been applied to.
    """
    raise NotImplementedError
