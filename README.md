# Passport Agent

**Preferred hosting: GitHub Pages.** Follow [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md). The ready-to-host site is in `docs/`; optional saved progress stays in each visitor's browser. Python is only needed to rebuild the static rule data or run the local back end.

Build the site and upload archives with `python3 build_pages.py --zip --source-zip`. The static site uses the same rules as the Python application. All 36 tests pass, including parity for every valid answer combination. Browser layout has not been checked in a real browser for this migration.

The previous PythonAnywhere deployment is documented in [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md) for reference. It is no longer the intended hosting destination.

A local Irish citizenship document preparation app with a browser front end, Python HTTP back end, and SQLite persistence.

## Run locally

Requires Python 3.11 or newer. No package installation is needed.

```sh
cd /Users/sharonokeakwalam/projects/passport-agent
python3 server.py
```

Open **http://127.0.0.1:8000** in your browser. Keep the terminal running; press Ctrl+C to stop.

If port 8000 is occupied:

```sh
python3 server.py --port 8001
```

The server listens only on `127.0.0.1`. This is a local development server, not a production deployment. No website has been published.

## Features

- Three adult route selections: Foreign Births Registration, residence naturalisation, and spouse/civil partner naturalisation.
- Conditional questionnaire, answer review, and server-generated document lists.
- Family-chain records, deceased relatives, name changes, immigration registration, and spouse evidence.
- Explicit guidance for unsupported cases and unresolved answers.
- Original/copy instructions, explanations, and official source links.
- Document readiness tracking.
- Optional local saving, resuming, and deletion.
- Printable checklist, browser **Save as PDF**, and text download.
- Source reference page with review dates.
- Responsive layout, keyboard-accessible controls, and reduced-motion support.

## Coverage and limitations

This is the first development version, not a verified exhaustive application service.

The adult Foreign Births Registration requirements were checked against the DFA's published adult-applicant lists for an Irish-born grandparent, a parent registered in the Foreign Births Register, or a naturalised parent.

Naturalisation lists reflect published ISD guidance. The portal-specific Word document checklists could not be read in this development environment. The application therefore explicitly labels those lists as incomplete pending comparison with the portal. They must not be presented as exhaustive.

Children, adoption, dependent young adults, refugee/stateless applicants, Irish associations, Northern Ireland residence evidence, and unusual family connections are outside this version's personalised coverage.

The app does not calculate reckonable residence, confirm legal eligibility, inspect documents, upload files, or submit applications. Checking every item means the user has marked the documents ready; it does not mean an application has been approved or verified.

## Local data

Answers remain in memory until **Save for later** or **Save this checklist** is selected. Further edits to that journey then save automatically.

- Data file: `data/passport-agent.sqlite3`, created at first startup.
- A random, HttpOnly, SameSite cookie identifies the browser's saved journey.
- One saved journey per browser cookie; explicitly saving a new journey replaces it.
- Saved records are not encrypted. Anyone with filesystem access to the database can read them.
- Delete a saved journey from the home page.
- Clearing cookies loses access to a saved journey but does not remove its database record.
- To remove all saved data, stop the server and delete the database file.
- No analytics, external fonts, or third-party front-end dependencies.
- Official-source links open external websites when clicked.

## Architecture

```text
Browser (HTML / CSS / JavaScript)
              |
         Local HTTP API
              |
     Versioned Python rules
              |
      SQLite saved progress
```

| File | Responsibility |
| --- | --- |
| `server.py` | Local HTTP server, request validation, session cookies, persistence |
| `rules.py` | Routes, conditional questions, requirements, sources, version |
| `scorecards.py` | Evidence options, points, independent totals, selection validation |
| `static/index.html` | Accessible application shell |
| `static/app.js` | Questionnaire, review, checklist, saving, exports |
| `static/styles.css` | Responsive design and print styles |
| `tests/` | Rule scenarios, persistence, and HTTP-handler tests |
| `CONTENT_REVIEW.md` | Research notes and outstanding content checks |
| `PLAN.md` | Project plan and implementation status |

The proposed Next.js/PostgreSQL stack was adapted to Python/SQLite because Node.js was unavailable. This keeps the local application dependency-free. Public hosting and a production database remain future work.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service and rules version |
| GET | `/api/catalog` | Routes, questions, source metadata |
| POST | `/api/evaluate` | Validate answers and build a checklist |
| GET | `/api/draft` | Read the current browser's saved journey |
| PUT | `/api/draft` | Save answers, stage, and document progress |
| DELETE | `/api/draft` | Delete the current browser's saved journey |

Mutations require JSON and the `X-Passport-Agent: local` header. Host and Origin checks restrict browser access to the local app. Static file serving uses an explicit allowlist.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests exercise the real HTTP request handler through an in-memory transport, without binding a socket. They cover validation, static assets, source metadata, save/resume/delete, session separation, foreign-origin rejection, conditional requirements, unsupported cases, and persisted storage.

On macOS, a JavaScriptCore smoke test also checks JavaScript execution and rendering of the main screens using a minimal DOM stub. It does not test browser layout or interaction. All 31 tests passed in the development environment.

The coding sandbox denied binding a local listening socket, so a live-server browser test could not be completed there. Start the application in a normal local terminal and use the manual checks below.

### Manual browser checks

1. Select the family route and an adult born abroad through an Irish-born grandparent.
2. Mark that grandparent deceased; confirm the checklist asks for their death certificate.
3. Edit the route connection to a parent registered before your birth; confirm grandparent documents disappear.
4. Select an Irish-born parent; confirm the app gives route guidance rather than a registration checklist.
5. Save, reload, resume, mark a document ready, reload, and check that progress persists.
6. Print or save as PDF; confirm explanations and source URLs appear.
7. Delete the saved journey; refresh and confirm the resume banner disappears.
8. Repeat using residence and spouse routes; check the naturalisation coverage notice.
9. Test keyboard navigation and a narrow mobile viewport.

## Maintaining requirements

Edit `rules.py`, update the review notes and version, and run the tests. There is no content-editing admin interface yet. Existing saved journeys with an older rules version are prompted to review their answers.

Before public release: complete the portal checklist review, verify exceptional cases, perform browser/accessibility testing, and choose production hosting, database, authentication, and operational controls.


## Document and question improvements

The standard residence flow now asks six factual questions; the spouse flow asks eight. The app no longer asks whether the user has read government eligibility rules or already knows which records are missing.

The checklist separates required records from alternative identity and residence evidence. All published current scorecard rows are visible, with points, preparation conditions, and sources. Identity needs 150 points once; residence needs 100 + 50 for each qualifying year. Each year has its own evidence selector. Foreign Births Registration has no points system.

Historical or unclassified evidence is shown separately and excluded from the calculator until its current points are confirmed. A required IRP can also be selected for identity points, but marking the required copy ready does not add points automatically.

After updating the code, restart `python3 server.py` and refresh the browser. Older saved questionnaires need to be answered again because the question set changed.

Identity choices remain selectable above 150 points and are preserved when saved. The tracker adds every selected row. Multiple passport categories trigger a separate acceptance note.
