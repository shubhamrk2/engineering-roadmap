# Engineering roadmap

This repository holds two things that share one design system and one runtime:

1. **The Applied AI track** (sheets 20 to 23, `ai-*.html`, glass theme): a day-by-day plan from 1 Nov 2026 to 31 Mar 2027 for
   moving into Applied AI / Forward Deployed engineering roles, with Python-from-zero material and a tested practice lab.
2. **BadgeDesk** (sheets 00 to 15): the earlier 12-week general full-stack drawing set. Still here as optional reference.

## Applied AI track

Open `ai-plan.html` first.

| Sheet | File | What it is |
|---|---|---|
| 20 | `ai-plan.html` | The plan: five phases, four gates, the honest view of the deadline, the week-by-week table |
| 21 | `ai-daily.html` | The daily planner: 151 days, each with what to learn, what to do, a pass/fail "done when", and verified text and video resources |
| 22 | `ai-tracker.html` | Fourteen skills on six levels. Levels 4 and 5 are locked until you write evidence. Weekly review form |
| 23 | `ai-python.html` | Python from zero, weeks 1 to 4 |
| 24 | `ai-http.html` | HTTP, curl, httpx, timeouts, retries, auth, pagination, rate limits (week 5) |
| 25 | `ai-fastapi.html` | FastAPI and Pydantic v2 (week 6) |
| 26 | `ai-sql.html` | SQL and PostgreSQL, psycopg, transactions (weeks 7 to 8) |
| 27 | `ai-docker.html` | Docker, Compose, config, CI basics (week 8) |
| 28 | `ai-reliability.html` | Auth, secrets, encryption, idempotency, webhooks, circuit breakers, audit (week 9) |
| 29 | `ai-testing.html` | pytest in depth, test doubles, evaluating LLM apps |
| 30 | `ai-llm.html` | LLM engineering: tokens, prompting, structured output, injection (week 10) |
| 31 | `ai-rag.html` | Embeddings, chunking, retrieval, hybrid search, RAG (weeks 11 to 12) |
| 32 | `ai-agents.html` | Tool calling, agent loop, workflows, approvals, LangGraph (weeks 14 to 15) |
| 33 | `ai-mcp.html` | Model Context Protocol (week 16) |
| 37 | `ai-projects.html` | Build guides for Project 1 and Project 2 (weeks 13, 17, 18) |
| 34 | `ai-dsa.html` | DSA in Python, daily from week 5 |
| 35 | `ai-interview.html` | Interview preparation for Applied AI roles (weeks 19 to 20) |
| 36 | `ai-jobsearch.html` | Job search method, offers, negotiation principles (weeks 21 to 22) |

`python-lab/` has the exercises: 924 tests across 19 lab folders. Every stub starts failing; your code turns the tests green. See `python-lab/README.md`.

**Where the plan lives.** All day-level content is data in `assets/js/daily-plan.js` (one source for the planner and the plan table). Per-day resources are
merged by `node tools/merge-resources.mjs` from `tools/resources/*.json` into `assets/js/day-resources.js`; verify any resource file with
`node tools/verify-resources.mjs <file>` and execute a sheet's code with `python tools/run-python-blocks.py <sheet.html>`.
`assets/js/planner.js` draws it and stores ticks and notes in the browser's `localStorage`. `assets/js/tracker.js` does the same for the skills tracker.
Use **Export progress** on sheet 21 to back up; clearing browser data erases progress.

**Theme.** `assets/css/glass.css` is an opt-in glassmorphism theme, active only on `<body class="glass">`. It falls back to solid surfaces
where `backdrop-filter` is unsupported or reduced transparency is requested. The BadgeDesk sheets are unchanged.

**Privacy.** Keep portfolio work, job-search notes and compensation research on a personal machine, not an employer-managed one.
This repository currently sits in an employer OneDrive folder; copy it to a personal machine before using it.

# BadgeDesk — a 12-week engineering drawing set

A study site covering Python, JavaScript, TypeScript, Java, React, Next.js, FastAPI, Node/Express,
NestJS, REST, GraphQL, webhooks, PostgreSQL, MongoDB, Redis, AWS, Azure, Git, GitHub Actions, Docker,
Kubernetes, Terraform, Kafka, RabbitMQ and LLM/RAG engineering.

Fifteen sheets, one system. Every example on every sheet is a slice of **BadgeDesk** — a corporate badge
and site-access request platform — so the technologies connect to each other instead of sitting in
fifteen unrelated tutorials.

## Open it

Double-click `index.html`. That is all it needs — no build step, no dependencies, no internet connection
except for the web fonts and the resource links.

To serve it properly (so relative links and `localStorage` behave consistently):

```bash
cd engineering-roadmap
python -m http.server 8899
# then open http://localhost:8899
```

## The sheets

| # | Sheet | File | Week |
|---|---|---|---|
| 00 | The Plan | `index.html` | 00 |
| 01 | Machine Setup | `setup.html` | 00 |
| 02 | Languages | `programming.html` | 01–02 |
| 03 | Frontend | `frontend.html` | 03–04 |
| 04 | Backend | `backend.html` | 05–06 |
| 05 | APIs | `apis.html` | 05–06 |
| 06 | Databases | `databases.html` | 07 |
| 07 | AWS | `aws.html` | 08–09 |
| 08 | Azure | `azure.html` | 09 |
| 09 | DevOps | `devops.html` | 10 |
| 10 | Terraform | `terraform.html` | 10 |
| 11 | Messaging | `messaging.html` | 11 |
| 12 | AI Engineering | `ai.html` | 11 |
| 13 | Projects | `projects.html` | 02–12 |
| 14 | Drill Book | `interview.html` | 12 |

Start at Sheet 00. It explains the conventions, the schedule and the system you are building.

## Conventions

Colour carries meaning in every diagram:

- **Cyan** — a synchronous call or a data read. Something is waiting for it.
- **Brass** — asynchronous work, an event, or the answer you should act on.
- **Red pencil** — the failure path, and the mistake that costs you an interview round.

Numbered circles in a drawing map one-to-one onto the numbered notes directly beneath it.

## Keyboard

| Key | Does |
|---|---|
| <kbd>/</kbd> | Focus the sheet search |
| <kbd>[</kbd> <kbd>]</kbd> | Previous / next sheet |
| <kbd>Esc</kbd> | Clear the search |

## Progress

Sign-off checkboxes are stored in the browser's `localStorage`, per browser and per machine. The title
block in the bottom-right corner shows the total across all fifteen sheets. Sheet 00 has a per-sheet
breakdown.

Because it is `localStorage`, progress does not sync between the personal and corporate laptops. That is
deliberate: tick a box only on the machine where you actually did the work.

## Layout

```
engineering-roadmap/
├── index.html              Sheet 00 and the entry point
├── *.html                  one file per sheet
├── assets/
│   ├── css/sheet.css       the whole design system
│   └── js/
│       ├── nav-data.js     the sheet index — single source of truth
│       └── sheet.js        nav, contents, title block, highlighting, progress
├── AUTHORING.md            the contract every sheet is written against
├── check.mjs               validator
└── README.md
```

`sheet.js` builds the left rail, the right contents panel, the title block, section numbers, syntax
highlighting, copy buttons, prev/next links and the sign-off tracker at run time. A sheet is just
content; it never has to wire any of that up.

## Adding or editing a sheet

1. Read `AUTHORING.md`. It is precise about structure, components, diagram conventions and voice.
2. Add or edit the entry in `assets/js/nav-data.js`.
3. Copy the skeleton from `AUTHORING.md` section 2, or start from `programming.html`.
4. Run the validator.

```bash
node check.mjs
```

It checks the page skeleton, duplicate element and SVG marker ids, missing heading ids, unescaped `<`
inside code blocks, dead internal links, unbalanced tags, missing `aria-label` on diagrams, and prints a
per-sheet summary of lines, drawings, sections, drill questions and sign-offs.

## Licence

Personal study material. The YouTube channels, documentation and tools it links to belong to their
respective owners.
