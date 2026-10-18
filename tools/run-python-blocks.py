"""Execute the code blocks of a sheet so nothing is claimed that was not run.

Usage:
    python tools/run-python-blocks.py <sheet.html> [--python PATH_TO_PYTHON] [--only N]

Every  <div class="code" data-lang="python">  block is run in its own empty temp folder with the given
interpreter (default: this one). Attributes on that <div> change what happens:

    data-run="no"         do not run. REQUIRED for blocks that need Postgres, Docker, a network service,
                          a model, or anything else this machine may not have. Add data-why="needs PostgreSQL".
                          The sheet must also say, in visible text near the block, that it was not executed.
    data-run="pytest"     run the block as a test file with pytest; it must pass
    data-expect="fail"    with data-run="pytest": the block is meant to contain failing tests (a teaching example)
    data-run="sqlite"     (data-lang="sql") run the block with Python's sqlite3 to check it is valid SQL
    data-timeout="120"    seconds allowed (default 60)

Blocks in other languages (bash, powershell, text, ...) are not executed and are listed as such.
Exit code 1 if any runnable block fails.                                                                     """
import argparse, html, re, subprocess, sys, tempfile, pathlib, sqlite3

ap = argparse.ArgumentParser()
ap.add_argument('sheet')
ap.add_argument('--python', default=sys.executable)
ap.add_argument('--only', type=int)
a = ap.parse_args()

src = pathlib.Path(a.sheet).read_text(encoding='utf-8')
pat = re.compile(r'<div class="code"([^>]*)>\s*(?:<header>(.*?)</header>)?\s*<pre><code>(.*?)</code></pre>', re.S)

def attr(attrs, name):
    m = re.search(name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None

ran = failed = skipped = other = 0
for i, m in enumerate(pat.finditer(src), 1):
    attrs, header, code = m.group(1), re.sub(r'<[^>]+>', '', m.group(2) or ''), html.unescape(m.group(3))
    lang, run = attr(attrs, 'data-lang'), attr(attrs, 'data-run')
    expect, why = attr(attrs, 'data-expect'), attr(attrs, 'data-why')
    timeout = int(attr(attrs, 'data-timeout') or 60)
    name = f'#{i} {header or lang}'
    if a.only and i != a.only:
        continue
    if lang not in ('python', 'sql'):
        other += 1
        continue
    if run == 'no':
        skipped += 1
        print(f'SKIP  {name}  ({why or "no reason given - ADD data-why"})')
        if not why:
            failed += 1
        continue
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        try:
            if lang == 'sql':
                if run != 'sqlite':
                    print(f'WARN  {name}  SQL block neither data-run="sqlite" nor data-run="no"')
                    failed += 1
                    continue
                con = sqlite3.connect(':memory:')
                con.executescript(code)
                con.close()
                ran += 1
                print(f'ok    {name}  (sqlite)')
                continue
            f = td / ('test_block.py' if run == 'pytest' else 'block.py')
            f.write_text(code, encoding='utf-8')
            cmd = [a.python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', str(f)] if run == 'pytest' else [a.python, str(f)]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=td, timeout=timeout)
            good = (r.returncode != 0) if (run == 'pytest' and expect == 'fail') else (r.returncode == 0)
            ran += 1
            if good:
                print(f'ok    {name}' + ('  (expected failures present)' if expect == 'fail' else ''))
            else:
                failed += 1
                print(f'FAIL  {name}\n' + (r.stdout + r.stderr)[-900:])
        except subprocess.TimeoutExpired:
            failed += 1
            print(f'FAIL  {name}  timed out after {timeout}s')
        except Exception as e:  # sqlite3.Error etc.
            failed += 1
            print(f'FAIL  {name}  {type(e).__name__}: {e}')

print(f'\nran {ran}, skipped {skipped} (declared), non-python {other}, FAILED {failed}')
sys.exit(1 if failed else 0)
