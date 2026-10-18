"""Week 3: files, JSON, exceptions, modules.

Replace each `raise NotImplementedError` with your own code.
Run:  pytest week03

Because conftest.py puts every week folder on the import path, you can reuse week 2:
    from w02_collections import count_errors, parse_log_line
"""


class ConfigError(Exception):
    """Raised when a configuration file is missing or is not valid JSON."""


def read_lines(path):
    """ex01. Return the lines of a UTF-8 text file as a list of strings.

    Strip whitespace from each line and leave out lines that are empty after stripping.
    If the file does not exist, let FileNotFoundError happen (do not catch it).
    Use a `with` block.
    """
    raise NotImplementedError


def load_json(path):
    """ex02. Read a JSON file and return the parsed value.

    Raise ConfigError (not FileNotFoundError, not json.JSONDecodeError) when the file is
    missing or contains invalid JSON. The error message must contain the file's name.
    """
    raise NotImplementedError


def safe_int(value, default=None):
    """ex03. Convert value to int. If that is not possible, return `default`.

    safe_int("12") -> 12     safe_int("12x") -> None     safe_int(None, -1) -> -1
    Catch only the exceptions int() can actually raise here, not a bare `except:`.
    """
    raise NotImplementedError


def write_report(counts, path):
    """ex04. Write `counts` (a dict) to `path` as JSON, indented by 2 spaces, keys sorted.

    Create the parent folder if it does not exist. UTF-8. Return None.
    """
    raise NotImplementedError


def analyze_file(input_path, output_path):
    """ex05. Count ERROR lines per service in a log file and write a JSON report.

    Read the log with read_lines, count with your week 2 count_errors.
    Write {"errors": <counts>, "skipped": <number of malformed non-blank lines>} to
    output_path (use write_report's formatting) and also return that same dict.
    A missing input file raises FileNotFoundError.
    """
    raise NotImplementedError
