"""Week 37 self-check: are the basics of your portfolio repository in place?

Implement the four functions below. Nothing here needs the network, a model or Git: it only reads files.
Run the tests with:   pytest week37 -q     (every test fails until you implement the functions)

Then point it at a real project:

    python -c "from pathlib import Path; from w37_selfcheck import check_repo; print(check_repo(Path('../my-project')))"

An empty list means the basics are present. It does NOT mean the project is good or secure.
"""
from __future__ import annotations

from pathlib import Path

# Headings a README must contain. A heading matches when the required phrase appears in its text,
# ignoring case, at any heading level (# to ######).
REQUIRED_HEADINGS = ("what it is", "quick start", "run the tests", "architecture", "limitations", "ownership")

# Directories that are never scanned or searched.
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}

# Files named like .env.example hold placeholders and are meant to be committed.
ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template")


def readme_headings(text: str) -> list[str]:
    """Return the lower-cased text of every Markdown heading in `text`, in order.

    A heading is a line that starts with 1 to 6 '#' characters followed by at least one space,
    e.g. '## Quick start' gives 'quick start'. Strip surrounding spaces and any trailing '#' characters.
    Lines inside a fenced code block (between lines starting with three backticks) are NOT headings:
    a shell comment such as '# install' inside a fence must be ignored.
    A line such as '#hashtag' (no space) is not a heading. Seven or more '#' is not a heading.
    """
    raise NotImplementedError


def gitignore_covers(gitignore_text: str, name: str) -> bool:
    """Return True if a simple .gitignore line ignores a file or directory called `name`.

    Rules (a deliberately small subset of real gitignore):
      * ignore blank lines, lines starting with '#', and negations starting with '!'
      * strip whitespace; remove one leading '/' and one trailing '/' from a pattern
      * a pattern covers `name` if it equals `name` or matches it with fnmatch wildcards
        (so '.env*' and '*.env' style globs work: fnmatch.fnmatch(name, pattern))
    'name' is a bare file or directory name such as '.env' or '.venv', never a path.
    """
    raise NotImplementedError


def find_secrets(text: str) -> list[str]:
    """Return the names of obvious secret patterns found in `text`, in this fixed order, without duplicates.

    Names and rules:
      'aws-access-key'      the regex AKIA[0-9A-Z]{16}
      'private-key'         a line containing '-----BEGIN' and 'PRIVATE KEY-----'
      'openai-style-key'    the regex \bsk-[A-Za-z0-9]{20,}
      'assigned-secret'     an assignment or mapping, case-insensitive, whose name is one of
                            api_key, api-key, apikey, secret, password, passwd, token
                            (the name may be part of a longer word such as DB_PASSWORD or client_secret),
                            followed by '=' or ':' then optional quote, then a value of 16 or more characters
                            from [A-Za-z0-9/+_.-]. The value only counts if it contains at least one letter
                            AND at least one digit, and its lower-case form contains none of:
                            'example', 'changeme', 'your', 'placeholder', 'xxxx', 'environ', 'getenv'.
    A reference such as os.environ["DB_PASSWORD"] or password = "" is NOT a secret.
    Return [] when nothing matches.
    """
    raise NotImplementedError


def check_repo(repo: Path) -> list[str]:
    """Check the project-readiness basics of the repository directory `repo`.

    Return a sorted list of problem strings; an empty list means every check passed.

      'NO_README'                          no file named README.md (any letter case) in the top directory
      'README_MISSING:<phrase>'            one per phrase of REQUIRED_HEADINGS not found (only when a README exists)
      'NO_TESTS'                           no top-level 'tests' directory containing a file named test_*.py or *_test.py
                                           (searched recursively inside tests/)
      'NO_DEPENDENCY_FILE'                 none of requirements.txt, pyproject.toml, Pipfile in the top directory
      'GITIGNORE_MISSING_ENV'              .gitignore absent, or does not cover the name '.env'
      'GITIGNORE_MISSING_VENV'             .gitignore absent, or does not cover the name '.venv'
      'ENV_FILE_NOT_IGNORED:<relpath>'     a file named '.env' or '.env.<something>' (except names ending in
                                           .example, .sample or .template) exists anywhere outside SKIP_DIRS,
                                           and its own name is not covered by .gitignore
      'SECRET:<relpath>:<name>'            find_secrets() reports <name> for a text file (read as UTF-8, undecodable
                                           files skipped, files over 1 MB skipped) outside SKIP_DIRS whose
                                           name is not covered by .gitignore. <relpath> uses forward slashes.
                                           Files named .env.example/.sample/.template ARE scanned.
    Never modify anything under `repo`. Missing `repo` directory: raise FileNotFoundError.
    """
    raise NotImplementedError
