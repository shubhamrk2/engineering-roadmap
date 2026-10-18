# python-lab

Exercises for weeks 1 to 4 of the Applied AI track. You write the functions; pytest tells you whether they are right.

Teaching material for each week is on **Sheet 23 (`ai-python.html`)**. The day-by-day schedule is on **Sheet 21 (`ai-daily.html`)**.

## The rule

Using an assistant to **explain** a concept or a traceback is fine. Using it to **write the function body** defeats the exercise: the
tests go green and you learn nothing. Gate 1 (end of week 4) is done with no assistance, so shortcuts here only delay the day you find out.

## One-time setup (Windows PowerShell, personal laptop)

```powershell
cd python-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell refuses to run `Activate.ps1`, that is a script-execution policy on your own machine. On your **personal** laptop you can
allow it for your user only: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Do not change this on an employer-managed machine.

macOS / Linux: `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt`

## Running the tests

```powershell
pytest week01              # one week
pytest week01 -k greeting  # only tests whose name contains "greeting"
pytest -x                  # stop at the first failure
pytest -q                  # shorter output
```

Every stub starts as `raise NotImplementedError`, so **every test fails at the start**. That is the starting line, not a problem.

## Layout

Folders are named after the week (weeks 1 to 9) or after the sheet that owns them (27 onwards). The planner tells you which to run each week.

| Folder | Sheet | You edit | Tests (do not edit) |
|---|---|---|---|
| `week01/` to `week04/` | 23 Python | `w01_basics.py`, `w02_collections.py`, `w03_files.py`, `w04_models.py` (+ your own `test_w04_mine.py`) | `test_w0N_*.py` |
| `week05/` | 24 HTTP | `w05_http.py` | `test_w05_http.py` |
| `week06/` | 25 FastAPI | `w06_api.py` | `test_w06_api.py` |
| `week07/`, `week08/` | 26 SQL | `w07_sql.py`, `w08_repo.py` | `test_w07_sql.py`, `test_w08_repo.py` |
| `week09/` | 28 Reliability | `w09_reliability.py` | `test_w09_reliability.py` |
| `week27/` | 27 Docker | `w27_config.py` | `test_w27_config.py` |
| `week29/` | 29 Testing | `w29_eval.py` | `test_w29_eval.py` |
| `week30/` | 30 LLM | `w30_llm.py` | `test_w30_llm.py` |
| `week31/` | 31 RAG | `w31_rag.py` | `test_w31_rag.py` |
| `week32/` | 32 Agents | `w32_agent.py` | `test_w32_agent.py` |
| `week33/` | 33 MCP | `w33_mcp.py` | `test_w33_mcp.py` |
| `week34/` | 34 DSA | `w34_dsa.py` | `test_w34_dsa.py` |
| `week35/` | 35 Interview | `w35_rounds.py` | `test_w35_rounds.py` |
| `week36/` | 36 Job search | `w36_*.py` | `test_w36_*.py` |
| `week37/` | 37 Projects | `w37_selfcheck.py` | `test_w37_selfcheck.py` |

Bare `pytest` runs every week. Run one folder at a time as you go (`pytest week05`).

`conftest.py` puts every `weekNN/` folder on the import path, so a later week can import an earlier one
(for example `from w02_collections import count_errors`).

## Reading a failure

```
FAILED week01/test_w01_basics.py::test_ex01_greeting_basic - NotImplementedError
```

Read the last line first. Then open the test named in the first line: the test is the specification. Put one `print()` in your function to see
what it returns, compare with what the test expects, change one thing, run again.

## What passing does and does not mean

Green means your code handles the cases the tests cover. It does not mean the code is correct for every input or ready for production.
Week 4 asks you to write tests of your own because the next bug will be in a case nobody listed.

## Capstone (week 4, Friday): `loganalyzer.py`

Not supplied. You build it, with tests of your own, in a new folder `loganalyzer/` and push it to a personal GitHub repository.

```
python loganalyzer.py app.log --top 3 --out report.json
```

Reads the log, skips and warns about malformed lines, counts `ERROR` lines per service, prints the top N, writes a JSON report.
Use only synthetic log data. Never use real employer logs.
