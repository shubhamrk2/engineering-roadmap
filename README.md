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
