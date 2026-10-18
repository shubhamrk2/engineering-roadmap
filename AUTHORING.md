# Authoring contract — BadgeDesk engineering drawing set

Read this in full before writing a sheet. `index.html` (Sheet 00) and `programming.html` (Sheet 02) are
the reference implementations. Match their density, tone and structure exactly.

---

## 1. The product every example belongs to

Every code sample, diagram, table and project on every sheet is a slice of **BadgeDesk** — a corporate
badge and site-access request platform. Never invent a different demo app. Never use `foo`, `bar`,
`TodoItem`, `User`, or a generic e-commerce example.

**What BadgeDesk does:** an employee requests access to a building; their manager approves it; a worker
provisions the badge into the physical access-control system (a slow, flaky third-party vendor API); a
nightly job reconciles what BadgeDesk believes against what the vendor actually has.

### Services (use these exact names)

| Service | Stack | Job |
|---|---|---|
| `web` | Next.js + React + Tailwind | Employee portal and manager approvals |
| `gateway` | NestJS (Node + TypeScript) | GraphQL BFF for the web app, auth edge |
| `core` | FastAPI (Python) | Requests, approvals, policy evaluation. Source of truth. |
| `provisioning-worker` | Python, Kafka consumer | Calls the vendor access-control API, retries |
| `notifier` | Node + Express | Email/Teams, outbound webhooks, inbound webhook receiver |
| `audit-reconciler` | AWS Lambda (Python), nightly | Compares BadgeDesk vs vendor, writes a report to S3 |
| `policy-indexer` | Python | Embeds access-policy documents into pgvector for "Ask BadgeDesk" |

### Data stores

- **PostgreSQL** — `employees`, `sites`, `access_requests`, `approvals`, `badges`, `policies`. Source of truth.
- **Redis** — session cache, `site_id → policy` cache, rate-limit counters, idempotency keys, distributed locks.
- **MongoDB** — `access_events` audit documents whose shape differs per vendor.
- **S3** — badge photos, nightly audit report exports.
- **pgvector / Qdrant** — embedded policy documents for RAG.

### Kafka topics

`badge.requests` · `badge.provisioned` · `access.events` · `badge.requests.dlq`

### Canonical identifiers

Employees `e-902`, sites `BLR-01` / `BLR-02` / `HYD-01`, requests `req-1`, statuses
`pending | approved | rejected`. Keep these consistent across sheets so a reader recognises them.

### The canonical fields of an access request

`id`, `employee_id`, `site_id`, `starts_on`, `ends_on`, `status`, `reason`, `created_at`.
Use snake_case in Python/SQL and camelCase in TS/Java — and point that out where relevant.

---

## 2. File skeleton — copy exactly

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sheet NN — TITLE — BadgeDesk Roadmap</title>
<link rel="stylesheet" href="assets/css/sheet.css">
</head>
<body data-sheet="NN">
<a class="skip" href="#main">Skip to sheet</a>
<div class="wrap">
<nav class="rail" aria-label="Sheet index"></nav>

<main id="main">

<header class="sheethead">
  <div>
    <div class="no">Sheet NN &middot; GROUP &middot; Weeks XX&ndash;YY</div>
    <h1>Title<span>.</span></h1>
    <p class="lede">Two or three sentences. What this sheet is for and the one idea that makes the rest
    of it click. Use <b>bold</b> for the load-bearing phrase.</p>
  </div>
  <div class="specs">
    <div><span>Weeks</span><span>…</span></div>
    <div><span>Hours</span><span>…</span></div>
    <div><span>Must know</span><span>…</span></div>
    <div><span>Nice to have</span><span>…</span></div>
    <div><span>Ships</span><span>…</span></div>
  </div>
</header>

<div class="sheetbody">
  <!-- content -->
</div><!-- /sheetbody -->
</main>

<aside class="toc" aria-label="Contents"></aside>
</div>

<script src="assets/js/nav-data.js"></script>
<script src="assets/js/sheet.js"></script>
</body>
</html>
```

Nothing else. No frameworks, no CDN scripts, no inline `<style>` or `<script>`. `sheet.js` builds the
left rail, the right contents panel, the title block, section numbers, syntax highlighting, copy
buttons, prev/next links and the sign-off tracker automatically.

---

## 3. Required structure inside `.sheetbody`

In this order:

1. **An opening `<h2>` with a hero drawing** — the mental model for the whole sheet, using
   `<figure class="dwg dwg--hero">`, followed by a `<div class="notes">` block whose numbers match the
   callout bubbles in the drawing.
2. **One `<h2>` per major subtopic.** Inside each, one `<h3>` per sub-subtopic.
3. Every subtopic must have: an explanation in prose, **at least one runnable code example**, and where
   the concept is spatial (a request path, a network layout, a storage layout, a lifecycle) **a diagram**.
4. Every subtopic ends with a `<div class="res">` resource list.
5. **A comparison section** using `.vs` and a `<table>` wherever two things are commonly confused
   (REST vs GraphQL, SQL vs NoSQL, Docker vs VM, Kafka vs RabbitMQ, AWS vs Azure, etc.).
6. **`<h2 id="connect">How the subtopics connect</h2>`** — a drawing that assembles every subtopic on the
   sheet into one working slice of BadgeDesk, plus what the reader ships that week.
7. **`<h2 id="drill">Drill book</h2>`** — 6–10 `<details>` questions with real answers.
8. **`<h2 id="signoff">Sign-off</h2>`** — 8–12 checkboxes.

Every `<h2>` and `<h3>` needs a unique `id`. `sheet.js` numbers the `<h2>`s and builds the contents rail
from them. Put a `<p class="sub">` immediately after each `<h2>`.

Target size: **1,000–1,400 lines** of HTML per sheet. This is a reference document, not a summary. Err
towards more worked detail, not less.

---

## 4. Component reference

### Panels — use all four, several times per sheet

```html
<div class="panel panel--why"><span class="ph">Why this exists</span><p>…</p></div>
<div class="panel panel--trap"><span class="ph">Red pencil</span><p>The mistake that fails interviews.</p></div>
<div class="panel panel--ask"><span class="ph">Interviewers ask</span><p>The question, then the answer.</p></div>
<div class="panel panel--real"><span class="ph">In production</span><p>What this looks like with real traffic.</p></div>
```

### Code blocks

```html
<div class="code" data-lang="python">
<header><b>badgedesk/core/models.py</b></header>
<pre><code>… source …</code></pre>
</div>
```

- `data-lang` drives highlighting. Supported: `python bash powershell sql javascript typescript tsx jsx
  java yaml json hcl terraform dockerfile graphql css html text`.
- The `<header><b>…</b></header>` is the file path or a short label. Always include it.
- **Escape `<`, `>` and `&` inside code as `&lt;` `&gt;` `&amp;`.** This is the single most common
  authoring bug. `List<String>` must be written `List&lt;String&gt;`, `=>` is fine, `->` is fine.
- Comment the interesting lines. Show output as a trailing comment: `# ['req-1']`.
- Code must be realistic and runnable, not pseudocode.

### Comparison of two things

```html
<div class="vs">
  <div><div class="vh">Left thing</div> …code or <div class="vb">prose</div>… </div>
  <div><div class="vh">Right thing</div> … </div>
</div>
```

Follow every `.vs` with a `<div class="tw"><table>…</table></div>` giving the dimension-by-dimension
breakdown, and finish with one sentence saying **which one to pick and when**.

### Cards, chips, tables

```html
<div class="grid g3"><div class="card"><span class="cm">Label</span><b class="ct">Title</b><p>…</p></div></div>
<div class="chips"><span class="chip on">brass</span><span class="chip cy">cyan</span><span class="chip">plain</span></div>
<div class="tw"><table><thead><tr><th>…</th></tr></thead><tbody><tr><td>…</td></tr></tbody></table></div>
```

### Drill questions

```html
<div class="drill">
  <div class="dh">Drill &mdash; topic</div>
  <details><summary>The question as an interviewer would say it.</summary>
    <div class="ans"><p>A real answer, 40–120 words. Include the follow-up they will ask next.</p></div></details>
</div>
```

### Resources

```html
<div class="res">
  <div class="rh">Watch when stuck &mdash; topic</div>
  <a class="r" href="…" target="_blank" rel="noopener"><span>Channel &mdash; video title<i>Why this one, in one sentence. What it covers.</i></span><span class="dur">26 min</span></a>
</div>
```

**Link policy — important.** Do not invent YouTube video IDs. Use one of:
- a channel URL you are confident exists, e.g. `https://www.youtube.com/@Fireship`,
  `@freecodecamp`, `@TechWorldwithNana`, `@hnasr`, `@ByteByteGo`, `@WebDevSimplified`, `@coreyms`,
  `@ArjanCodes`, `@KodeKloud`, `@NetworkChuck`, `@Telusko`, `@amigoscode`, `@AntonPutra`,
  `@DevOpsToolkit`, `@confluent`, `@javascriptmastery`, `@traversymedia`, `@academind`, `@gkcs`,
  `@ArpitBhayani`, `@NeetCode`, `@t3dotgg`, `@DaveGrayTeachesCode`, `@AndrejKarpathy`, `@jamesbriggs`;
- an official docs URL you are confident about;
- otherwise `https://www.youtube.com/results?search_query=<url-encoded channel + exact title>`.

5–7 resources per major subtopic. Mix: one short orientation video, one deep long-form course, one
official doc, one "when it breaks" resource.

### Sign-off

```html
<div class="signoff">
  <div class="sh"><span>Week XX</span><span>Sheet NN</span></div>
  <label><input type="checkbox"><span>A specific, verifiable thing they did — not "understood X".</span></label>
</div>
```

---

## 5. Diagrams

Diagrams are the point of this set. Every sheet needs **4–7** of them, hand-authored inline SVG.

```html
<figure class="dwg">
<svg viewBox="0 0 1200 420" role="img" aria-label="A full sentence describing what the diagram shows, for screen readers.">
  <defs>
    <marker id="sNN-ac" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#5fc4d8"/></marker>
    <marker id="sNN-ab" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e8b33c"/></marker>
    <marker id="sNN-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#ea5f42"/></marker>
  </defs>
  …
</svg>
<figcaption>Drawing NN-A &mdash; what it is. <b>Brass</b> = …</figcaption>
</figure>
```

**Marker ids must be unique per page** — prefix them with the sheet number (`s07-ac`). Reusing an id
across two `<svg>` elements on the same page breaks the arrowheads.

### SVG classes (defined in `sheet.css`, do not invent new ones)

| Class | Use |
|---|---|
| `.box` | neutral node |
| `.box-a` | brass-outlined node — the important one |
| `.box-c` | cyan-outlined node — data / request path |
| `.box-r` | red-outlined node — failure, deprecated, the wrong way |
| `.zone` | dashed enclosing region (a VPC, a cluster, a trust boundary) |
| `.ln` | plain rule/axis; add `.dash` for dashed |
| `.flow` | cyan arrow — synchronous, someone is waiting |
| `.flow-b` | brass arrow — asynchronous, event, background |
| `.flow-r` | red arrow — failure/retry path |
| `.lead` | thin leader line from a callout bubble |
| `.t` | node title text |
| `.m` | body text inside a diagram |
| `.mm` | small uppercase mono annotation |
| `.b` `.c` `.r` `.g` | recolour text: brass, cyan, red, graphite |
| `.mid` `.end` | text-anchor middle / end |
| `.bub` + `.bubt` | numbered callout circle and its number |

Colour discipline is a rule, not a suggestion: **cyan = synchronous, brass = asynchronous or "the answer",
red = the failure path.** State what the colours mean in the `<figcaption>`.

### Geometry rules

- `viewBox="0 0 1200 H"`. Choose `H` to fit; typical 220–700.
- Keep everything inside x 20–1180. Text does not auto-wrap in SVG — split long labels across multiple
  `<text>` elements 16–20px apart vertically.
- Node boxes: `height` 46–70, `rx="3"`. Title text at `y + 24`, mono subtitle at `y + 40`.
- Compute arrow endpoints so they stop 4–6px short of the target edge; the marker supplies the head.
- Do not overlap boxes with lines. Route around with `H`/`V` path segments.
- The hero drawing gets 5–7 numbered callout bubbles wired to a `<div class="notes">` list beneath.

### What to draw (pick what suits the sheet)

Request paths, layered architectures, network/trust boundaries, storage layouts (a B-tree, a page,
a partitioned log), lifecycles and state machines, timelines comparing two approaches (blocking vs
concurrent, blue/green vs rolling), decision trees ("which of these three do I pick"), and before/after
pairs. Prefer a drawing over a bullet list whenever the content has spatial or temporal structure.

---

## 6. Voice

- Write like a staff engineer explaining something to a colleague they respect. Direct, concrete, no hype.
- British-leaning spelling is used throughout (`behaviour`, `initialise`, `optimise`, `whilst` — no, not
  `whilst`). Match the existing sheets.
- **No emoji. Ever.**
- Prefer the specific number: "40 ms", "three retries", "5 GB", not "fast" and "several".
- Say what breaks and why, not only what works. The `panel--trap` blocks are the most valuable content
  on the sheet.
- Explain the *why* before the *how*. Assume the reader can read code but has not built this before.
- Never write "In this section we will learn about…". Start with the substance.
- Use `&mdash;` `&ndash;` `&middot;` `&rarr;` `&larr;` `&ldquo;` `&rdquo;` `&hellip;` rather than raw
  characters, to match the existing sheets.

---

## 7. Two-machine rule

The reader has a personal laptop (full admin, WSL2, Docker Desktop) and a corporate laptop (no admin, a
TLS-inspecting proxy, blocked registries, no Docker Desktop licence). Whenever a sheet requires
installing something, add a short note saying which machine to do it on and what the constrained
alternative is. Detailed instructions live on `setup.html`; link to it rather than repeating them.

---

## 8. Before you finish

- Every `<h2>`/`<h3>` has a unique `id`.
- Every `<svg>` has a `role="img"` and a descriptive `aria-label`.
- Marker ids are prefixed with the sheet number and are unique on the page.
- All `<` `>` `&` inside `<code>` are escaped.
- No unclosed tags. Open the file and read it back.
- The sheet links to at least two other sheets by filename (`<a href="databases.html">Sheet 06</a>`).

---

## 9. The Applied AI track (sheets 20 and up)

- Content sheets use `<body class="glass">` and link `assets/css/glass.css` after `sheet.css`. Everything in sections 2 to 8 still applies.
- Interactive pages (the daily planner and the skills tracker) set `data-kind="app"` on `<body>`. `check.mjs` skips only the content-sheet
  rules for them (code blocks, drills, sign-off, diagram count); duplicate ids, tag balance, dead links and emoji are still checked.
- These sheets do not use the BadgeDesk product as the running example. Examples are synthetic log lines, tickets and access requests.
- Python code blocks should run. Execute them before committing: extract each `data-lang="python"` block and run it.
- Diagram text is bumped up by `glass.css` because the column renders a 1200-wide viewBox at about 0.7x. Keep labels short enough to fit a box
  at 13px monospace (about 7.8px per character in viewBox units).


---

## 10. Rules for writing sheets 24 and up (Applied AI track)

These sheets are the learner's only teacher for their topic, and the learner is rebuilding the habit of **not trusting
code or links they have not seen work**. Hold the sheet to the same standard.

### 10.1 Your deliverables, and what you must not touch

You own: your sheet file(s); your lab folder `python-lab/weekNN/` if one is assigned; your resource file
`tools/resources/<sheet-file-without-ext>.json`. **Do not edit** any shared file: `nav-data.js`, `sheet.js`, `sheet.css`,
`glass.css`, `planner.js`, `tracker.js`, `daily-plan.js`, `check.mjs`, `README.md`, `AUTHORING.md`, `python-lab/requirements.txt`,
`python-lab/pytest.ini`, `python-lab/conftest.py`. If you need a change there, say so in your report. Other authors are
working in parallel; a collision silently loses someone's work.

### 10.2 Structure

Copy the skeleton in section 2 and follow section 3 and section 9. `<body data-sheet="NN" class="glass">`, link `sheet.css` then
`glass.css`. Reference implementation: `ai-python.html` (read it first: match its density, voice and components). Marker ids are
prefixed with the sheet number (`s26-ac`). Every sheet has: hero drawing + numbered notes, one `<h2>` per subtopic with a `<p class="sub">`,
runnable code, traps (`panel--trap`), interview panels (`panel--ask`), a resource list per subtopic, a comparison table where two things
are confused, `id="connect"`, `id="drill"` (8 to 12 real questions with answers), and `id="signoff"` (10 to 14 verifiable boxes).
Link at least two other sheets by filename. Diagram labels must fit their boxes at 13px monospace (about 7.8 viewBox units per character).

### 10.3 How to teach

- **Concept before framework.** Show the mechanism written by hand first, then the library, then say when the library is the wrong choice.
- **Predict, then reveal.** For the key ideas, ask a question in a `<details><summary>` block and put the answer inside it.
- **Say what to be able to defend.** Where a part of the code is interview material, label it ("You must be able to explain this line").
- **Say what breaks.** The trap panels are the most valuable content. Failure modes, not only happy paths.
- **The learner has C++ basics and ~4 years of enterprise integration (Power Platform, Dataverse, Zendesk/Azure Blob, MCP with an AI
  assistant) but weak independent Python.** Explain Python idioms when first used. Use C++ comparisons where they genuinely help.
- Never tell the learner a thing is production-ready because it ran once. Never claim a library behaves a way you did not check.

### 10.4 Code truthfulness (not optional)

1. Run every Python block: `python tools/run-python-blocks.py yourfile.html --python <venv python>`. Fix until it passes.
2. A block that cannot run here (needs PostgreSQL, Docker, a network service, a GPU or a model) must carry `data-run="no" data-why="..."`
   **and** the sheet must say in visible text next to it that it was not executed in the authoring environment, and what it was checked
   against instead (the library's documentation, with the version and page).
3. SQL that is portable should be `data-run="sqlite"` and executed. PostgreSQL-only SQL is `data-run="no"` with the reason.
4. Create a virtual environment in your own scratchpad, install the libraries, and record the exact versions. Put a visible
   line near the top of the sheet: `Tested with: python X.Y, fastapi A.B, ...  on <date>`.
5. Library APIs change (FastAPI, Pydantic v2, LangGraph, the MCP SDK, sentence-transformers, pgvector clients). Read the current
   documentation and run the installed version. If it disagrees with your memory, the installed version wins.
6. If you could not install or run something, say so on the sheet and in your report. Do not paper over it.

### 10.5 Resources: verified, relevant, free

Every link on the sheet and in your JSON must pass `node tools/verify-resources.mjs <file>`; then **read the printed titles** and
confirm each one teaches what you say it does. A link that loads but is the wrong topic is a failure.

- Prefer official documentation, deep-linked to the right page. Then free, reputable YouTube channels.
- A video link must be `https://www.youtube.com/watch?v=<id>` (optionally `&t=<seconds>`). Verify it with the tool (YouTube oEmbed),
  which prints the real title and channel. **Never invent an id. Never guess one from memory.** Find videos with a web search, then verify.
- No channel pages, playlists or search-result URLs standing in for a specific video.
- Free only. Avoid paywalled articles and anything that needs a paid plan. If a free tier might change, say "check current terms" rather than
  asserting it is free. Note the video length if you can establish it; do not guess a length.
- Prefer content that is not stale. If a video predates a breaking API change, say so in its note.

### 10.6 Per-day resource file

`tools/resources/<name>.json`, for the day numbers assigned to you (day 1 = Sun 1 Nov 2026; the dates and content for each day are in
`assets/js/daily-plan.js`). Read the day's theme, learn, do and done-when text so each resource fits that day.

```json
{ "days": {
    "29": {
      "text":  [ { "t": "Page title", "u": "https://...", "why": "what this gives today, 12 words max" } ],
      "video": [ { "t": "Video title", "u": "https://www.youtube.com/watch?v=ID", "by": "Channel", "why": "..." } ]
    } } }
```

Aim for at least one text and one video per day, including Saturdays and gate days. If no sound free video exists for a day,
leave `video` empty and explain in your report rather than padding with a weak one.

### 10.7 Labs (only if assigned)

`python-lab/weekNN/` with a stub file (every function `raise NotImplementedError`, with a docstring that is the specification) and a
test file. Write a reference solution in **your scratchpad** (never in the repo), then prove: (a) every test fails on the stubs, (b) every test
passes on the reference, (c) at least five deliberate mutations of the reference are each caught. Tests use fakes, never the network, a
paid API or a real model. List dependencies in `python-lab/weekNN/requirements-weekNN.txt`. Module names are unique across weeks
(`w05_...`) because `conftest.py` puts every week folder on the import path.

### 10.8 Constraints

Free tools only. Synthetic data only. No employer or client information anywhere. No emoji. British spelling. HTML entities
(`&mdash;`, `&middot;`). Say what the learner must do on a **personal** laptop versus anything needing admin rights. Adapt model-size
advice to unknown hardware instead of assuming a GPU.

### 10.9 Before you report

`node check.mjs` (your files must be clean; 32 failures in other, older sheets are pre-existing and not yours),
`python tools/run-python-blocks.py`, `node tools/verify-resources.mjs tools/resources/<name>.json`. Report: files created; versions
tested; blocks skipped and why; links dropped and why; anything you could not verify; any shared-file change you need.
