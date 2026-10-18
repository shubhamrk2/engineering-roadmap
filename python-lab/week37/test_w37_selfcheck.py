"""Tests for w37_selfcheck. Read them: they are the specification. Do not edit them."""
from pathlib import Path

import pytest

from w37_selfcheck import (
    REQUIRED_HEADINGS,
    check_repo,
    find_secrets,
    gitignore_covers,
    readme_headings,
)

GOOD_README = """# Knowledge Assistant

## What it is
A thing.

## Quick start
```bash
# install
pip install -r requirements.txt
```

## Run the tests
pytest

### Architecture
Boxes.

## Known limitations
Many.

## Ownership note
I wrote X.
"""

# Built by concatenation so this test file does not itself look like a leaked key.
FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_SK = "sk-" + "abcdefghijklmnopqrstuvwx1234"
FAKE_KEY_VALUE = "q8Zk2" + "Lm9Xp4Rt7Vb1Nc3"      # 20 chars, letters and digits


def make_repo(root: Path, **over) -> Path:
    """Build a fake repo that passes every check; `over` maps relative path -> text, or None to delete."""
    files = {
        "README.md": GOOD_README,
        "requirements.txt": "fastapi\n",
        ".gitignore": ".venv/\n.env\n__pycache__/\n",
        "tests/test_app.py": "def test_ok():\n    assert True\n",
        "app/main.py": "print('hi')\n",
    }
    for rel, text in over.items():
        if text is None:
            files.pop(rel, None)
        else:
            files[rel] = text
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def repo_with(tmp_path, files):
    """Same as make_repo but takes a dict, so keys may contain dots and slashes."""
    return make_repo(tmp_path / "r", **files)


# ---------------------------------------------------------------- readme_headings
def test_headings_basic_levels_lowercased():
    assert readme_headings("# One\n## Two Words\n###### Six\n") == ["one", "two words", "six"]


def test_headings_ignore_fenced_code():
    text = "# Real\n```bash\n# not a heading\n## also not\n```\n## After\n"
    assert readme_headings(text) == ["real", "after"]


def test_headings_need_a_space_and_max_six_hashes():
    assert readme_headings("#hashtag\n####### seven\n## ok\n") == ["ok"]


def test_headings_strip_trailing_hashes_and_spaces():
    assert readme_headings("##   Spaced   ##\n") == ["spaced"]


def test_headings_empty_text():
    assert readme_headings("") == []


# ---------------------------------------------------------------- gitignore_covers
def test_gitignore_exact_and_directory_forms():
    assert gitignore_covers(".venv/\n", ".venv")
    assert gitignore_covers("/.venv\n", ".venv")
    assert gitignore_covers("node_modules\n.env\n", ".env")


def test_gitignore_wildcards():
    assert gitignore_covers(".env*\n", ".env")
    assert gitignore_covers("*.env\n", "prod.env")
    assert not gitignore_covers("*.log\n", ".env")


def test_gitignore_comments_blanks_and_negation_do_not_count():
    assert not gitignore_covers("# .env\n\n", ".env")
    assert not gitignore_covers("!.env\n", ".env")


def test_gitignore_empty_and_unrelated():
    assert not gitignore_covers("", ".env")
    assert not gitignore_covers(".env.local\n", ".env")


# ---------------------------------------------------------------- find_secrets
def test_secret_aws_key():
    assert find_secrets(f"key = {FAKE_AWS}") == ["aws-access-key"]


def test_secret_private_key_header():
    assert find_secrets("-----BEGIN RSA PRIVATE KEY-----\nabc") == ["private-key"]
    assert find_secrets("-----BEGIN PRIVATE KEY-----") == ["private-key"]
    assert find_secrets("BEGIN something") == []
    assert find_secrets("-----BEGIN CERTIFICATE-----") == []        # a public certificate is not a secret


def test_short_akia_prefix_is_not_a_key():
    assert find_secrets("AKIA" + "ABCDEFGHIJ") == []


def test_secret_openai_style():
    assert find_secrets(f"x {FAKE_SK}") == ["openai-style-key"]
    assert find_secrets("sk-short") == []


@pytest.mark.parametrize("line", [
    f'API_KEY = "{FAKE_KEY_VALUE}"',
    f"password: {FAKE_KEY_VALUE}",
    f"DB_PASSWORD={FAKE_KEY_VALUE}",
    f'{{"client_secret": "{FAKE_KEY_VALUE}"}}',
    f"TOKEN = '{FAKE_KEY_VALUE}'",
    f"apikey={FAKE_KEY_VALUE}",
    f"passwd = {FAKE_KEY_VALUE}",
])
def test_secret_assignment_forms(line):
    assert find_secrets(line) == ["assigned-secret"]


@pytest.mark.parametrize("line", [
    'DB_PASSWORD = os.environ["DB_PASSWORD"]',
    'password = ""',
    "api_key = your-api-key-goes-here1",
    "SECRET=changeme12345678901",
    "token = abcdefghijklmnopqrstuvwxyz",     # letters only
    "token = 12345678901234567890",           # digits only
    "api_key = short1",                       # under 16 characters
    "password = abc12345678",                 # 11 characters: still under 16
    "api_key = xxxx1234xxxx1234xxxx",
    "api_key = PLACEHOLDER_value_1234567",
    "api_key = EXAMPLE_value_12345678",
    "secret = getenv_value_1234567890",
])
def test_not_secrets(line):
    assert find_secrets(line) == []


def test_secret_order_and_no_duplicates():
    text = f'password = "{FAKE_KEY_VALUE}"\n{FAKE_SK}\n{FAKE_AWS}\n{FAKE_AWS}\ntoken = "{FAKE_KEY_VALUE}"'
    assert find_secrets(text) == ["aws-access-key", "openai-style-key", "assigned-secret"]


def test_clean_text():
    assert find_secrets("def add(a, b):\n    return a + b\n") == []


# ---------------------------------------------------------------- check_repo
def test_good_repo_has_no_problems(tmp_path):
    assert check_repo(make_repo(tmp_path / "r")) == []


def test_missing_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        check_repo(tmp_path / "nope")


def test_no_readme(tmp_path):
    assert check_repo(repo_with(tmp_path, {"README.md": None})) == ["NO_README"]


def test_readme_name_is_case_insensitive(tmp_path):
    repo = repo_with(tmp_path, {"README.md": None, "readme.md": GOOD_README})
    assert check_repo(repo) == []


def test_each_missing_heading_is_reported(tmp_path):
    repo = repo_with(tmp_path, {"README.md": "# T\n## What it is\n## Architecture\n"})
    assert check_repo(repo) == sorted([
        "README_MISSING:quick start", "README_MISSING:run the tests",
        "README_MISSING:limitations", "README_MISSING:ownership",
    ])


def test_headings_inside_code_fence_do_not_satisfy_readme(tmp_path):
    fenced = "```\n" + "\n".join("## " + h for h in REQUIRED_HEADINGS) + "\n```\n"
    problems = check_repo(repo_with(tmp_path, {"README.md": fenced}))
    assert sorted(problems) == sorted(f"README_MISSING:{h}" for h in REQUIRED_HEADINGS)


def test_heading_match_is_a_phrase_inside_the_heading(tmp_path):
    # 'Known limitations' contains 'limitations'; 'Ownership note' contains 'ownership' (both in GOOD_README)
    assert check_repo(make_repo(tmp_path / "r")) == []


def test_no_tests_directory(tmp_path):
    assert check_repo(repo_with(tmp_path, {"tests/test_app.py": None})) == ["NO_TESTS"]


def test_tests_directory_without_test_files(tmp_path):
    repo = repo_with(tmp_path, {"tests/test_app.py": None, "tests/helpers.py": "x = 1\n"})
    assert check_repo(repo) == ["NO_TESTS"]


def test_tests_found_recursively_and_by_suffix(tmp_path):
    repo = repo_with(tmp_path, {"tests/test_app.py": None, "tests/unit/deep/chunker_test.py": "x = 1\n"})
    assert check_repo(repo) == []


def test_test_file_outside_tests_dir_does_not_count(tmp_path):
    repo = repo_with(tmp_path, {"tests/test_app.py": None, "test_top.py": "x = 1\n"})
    assert check_repo(repo) == ["NO_TESTS"]


@pytest.mark.parametrize("keep", ["requirements.txt", "pyproject.toml", "Pipfile"])
def test_any_one_dependency_file_is_enough(tmp_path, keep):
    repo = repo_with(tmp_path, {"requirements.txt": None, keep: "x\n"})
    assert check_repo(repo) == []


def test_no_dependency_file(tmp_path):
    assert check_repo(repo_with(tmp_path, {"requirements.txt": None})) == ["NO_DEPENDENCY_FILE"]


def test_missing_gitignore_reports_both(tmp_path):
    repo = repo_with(tmp_path, {".gitignore": None})
    assert check_repo(repo) == ["GITIGNORE_MISSING_ENV", "GITIGNORE_MISSING_VENV"]


def test_gitignore_missing_only_venv(tmp_path):
    repo = repo_with(tmp_path, {".gitignore": ".env\n"})
    assert check_repo(repo) == ["GITIGNORE_MISSING_VENV"]


def test_gitignore_missing_only_env(tmp_path):
    repo = repo_with(tmp_path, {".gitignore": ".venv/\n"})
    assert check_repo(repo) == ["GITIGNORE_MISSING_ENV"]


def test_env_file_not_ignored_is_flagged_even_in_subfolder(tmp_path):
    repo = repo_with(tmp_path, {".gitignore": ".venv/\n", "deploy/.env": "A=1\n", ".env.local": "B=2\n"})
    assert check_repo(repo) == sorted([
        "ENV_FILE_NOT_IGNORED:.env.local", "ENV_FILE_NOT_IGNORED:deploy/.env", "GITIGNORE_MISSING_ENV",
    ])


def test_env_file_that_is_ignored_is_fine(tmp_path):
    repo = repo_with(tmp_path, {".env": "A=1\n"})
    assert check_repo(repo) == []


@pytest.mark.parametrize("name", [".env.example", ".env.sample", ".env.template"])
def test_env_templates_are_allowed(tmp_path, name):
    assert check_repo(repo_with(tmp_path, {name: "API_KEY=\n"})) == []


def test_secret_in_source_file_is_reported_with_relative_posix_path(tmp_path):
    repo = repo_with(tmp_path, {"app/config.py": f'API_KEY = "{FAKE_KEY_VALUE}"\n'})
    assert check_repo(repo) == ["SECRET:app/config.py:assigned-secret"]


def test_secret_in_env_example_is_scanned(tmp_path):
    repo = repo_with(tmp_path, {".env.example": f"OPENAI={FAKE_SK}\n"})
    assert check_repo(repo) == ["SECRET:.env.example:openai-style-key"]


def test_secret_in_ignored_env_file_is_not_reported(tmp_path):
    repo = repo_with(tmp_path, {".env": f"OPENAI={FAKE_SK}\n"})
    assert check_repo(repo) == []


def test_secret_inside_skipped_dirs_is_ignored(tmp_path):
    repo = repo_with(tmp_path, {
        ".venv/lib/x.py": f"password = '{FAKE_KEY_VALUE}'\n",
        "node_modules/a/b.js": f"{FAKE_SK}\n",
        ".git/config": f"{FAKE_AWS}\n",
    })
    assert check_repo(repo) == []


def test_secret_in_ignored_file_name_is_skipped(tmp_path):
    repo = repo_with(tmp_path, {".gitignore": ".venv/\n.env\nlocal.cfg\n", "local.cfg": f"token = {FAKE_KEY_VALUE}\n"})
    assert check_repo(repo) == []


def test_binary_and_huge_files_are_skipped_without_crashing(tmp_path):
    repo = make_repo(tmp_path / "r")
    (repo / "blob.bin").write_bytes(b"\xff\xfe\x00\x80" * 100)
    (repo / "huge.txt").write_text(f"{FAKE_SK}\n" + "a" * 1_100_000, encoding="utf-8")
    assert check_repo(repo) == []


def test_multiple_problems_are_sorted(tmp_path):
    repo = repo_with(tmp_path, {"README.md": None, "requirements.txt": None, "tests/test_app.py": None})
    assert check_repo(repo) == ["NO_DEPENDENCY_FILE", "NO_README", "NO_TESTS"]


def test_check_does_not_modify_the_repo(tmp_path):
    repo = repo_with(tmp_path, {"app/config.py": f'API_KEY = "{FAKE_KEY_VALUE}"\n'})
    before = sorted((p.relative_to(repo).as_posix(), p.stat().st_mtime_ns) for p in repo.rglob("*") if p.is_file())
    check_repo(repo)
    after = sorted((p.relative_to(repo).as_posix(), p.stat().st_mtime_ns) for p in repo.rglob("*") if p.is_file())
    assert before == after
