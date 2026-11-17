# Passport Agent — Project Plan

## Hosting change — 17 November 2026

The user requested GitHub hosting instead of PythonAnywhere. A GitHub Pages edition is prepared in `docs/`. Its decision graph is compiled from all valid answer combinations in the Python rules. Saved progress moves to browser storage; no Python or database server is required for Pages. Source, static upload archives, functional tests and deployment instructions are ready. Creating the GitHub repository and enabling Pages remain deployment steps; no GitHub site has yet been published.

## Development status — 20 October 2026

The initial local application is implemented with a responsive browser front end, Python back end, explicit checklist rules, and SQLite saved progress. Node.js was unavailable, so the proposed Next.js/PostgreSQL stack below was adapted for a dependency-free local version.

Implemented: route selection, conditional questions, review/edit, sourced preparation lists, readiness tracking, optional save/resume/delete, print/PDF via the browser, text download, and a source-reference page.

Outstanding: exhaustive naturalisation portal document review, broader routes, browser QA, and a content-editing admin interface. The application labels incomplete or unsupported coverage. See `README.md` for startup and `CONTENT_REVIEW.md` for evidence and research gaps.

The coding sandbox prevents binding a listening socket; run the app in a normal local terminal. Internet deployment remains deferred.

## Purpose

Passport Agent will help people choose an Irish citizenship route, answer relevant questions, and receive a personalised document checklist linked to official instructions.

The initial scope is Irish citizenship applications. Irish passport applications are a separate process that can be added later.

## Hosting

- Develop, run, and test the application locally.
- Run both the front end and back end on the local computer, with a local PostgreSQL database.
- Document setup, environment variables, database migrations, and startup commands.
- Keep configuration portable so the application can be hosted online later.
- Internet deployment is a future phase, after development and validation are complete and the user decides to publish.

## User journey

1. **Choose a route.** Present citizenship routes in plain language and offer an “I’m not sure” option.
2. **Answer relevant questions.** Ask only questions that affect the route or document requirements.
3. **Review answers.** Allow corrections before generating the checklist.
4. **Receive a checklist.** Separate required documents, conditional documents, and unresolved requirements.
5. **Track progress.** Mark documents as ready and print or download the checklist.

Check the selected route against the answers. If another route appears more appropriate, explain why and let the user review it.

For people who may already be citizens by birth or descent, explain the distinction and direct them to the appropriate next process.

## Front end

Build a responsive website suitable for phones and computers.

| Screen | Purpose |
| --- | --- |
| Welcome | Explain the service and start the process |
| Route selection | Describe the available routes and their coverage |
| Guided questions | Ask one clear question at a time, with back navigation and progress |
| Answer review | Show the information used to generate the checklist |
| Document checklist | Display personalised requirements and preparation instructions |
| Saved progress | Resume a checklist and track document readiness |
| Admin area | Review and maintain questions, rules, and requirements |

Each document entry should explain:

- What to provide and whose document it is.
- Why it is required for the applicant’s circumstances.
- Whether an original, copy, or certified copy is needed.
- Applicable translation, witness, validity, and date requirements.
- Accepted alternatives where official guidance permits them.
- The official source and the date the requirement was last reviewed.

Use accessible controls, clear error messages, keyboard navigation, and plain language.

## Back end

The back end will:

- Store routes, questions, document requirements, and decision rules.
- Return questions relevant to the route and previous answers.
- Validate answers and identify missing information.
- Generate checklists using explicit, versioned rules.
- Attach official sources to each requirement.
- Save progress when requested.
- Support checklist export.
- Support reviewed content updates through an admin interface.

The checklist must come from reviewed rules, not AI-generated guesses. An optional AI explanation feature can be considered later.

## Proposed architecture

| Layer | Approach |
| --- | --- |
| Front end | Next.js with TypeScript |
| Back end | TypeScript API in the same application, with separate rules and content modules |
| Database | Local PostgreSQL |
| Validation | Shared schemas for questions, answers, and API requests |
| Export | Printable checklist first; PDF export next |
| Accounts | Optional after the initial release |
| Hosting | Local development and use first; internet hosting later |

Keep the rules engine independent of the interface so it can be tested and reused.

### Core data records

- **Routes:** citizenship pathways and coverage status.
- **Questions:** prompts, answer types, options, and display conditions.
- **Rules:** conditions that determine questions and requirements.
- **Document requirements:** preparation instructions, alternatives, and applicability.
- **Official sources:** URLs, relevant sections, and review dates.
- **Rule versions:** published requirement sets and change history.
- **Saved checklists:** answers, document progress, and the rule version used.

When answers change, recalculate the checklist and remove requirements that no longer apply.

## Research and content preparation

Before implementing each route:

1. Read official guidance, current application forms, and document instructions.
2. Identify applicant circumstances that change the requirements.
3. Create a decision table linking those circumstances to documents.
4. Record a source for every requirement and decision rule.
5. Flag ambiguous or conflicting instructions for review.
6. Validate sample checklists against the official instructions.

Use official sources such as Immigration Service Delivery, the Department of Foreign Affairs, and applicable legislation.

Starting research links:

- [ISD citizenship guide](https://www.irishimmigration.ie/how-to-become-an-irish-citizen-guide/)
- [Foreign Births Registration](https://www.ireland.ie/en/dfa/citizenship/born-abroad/registering-a-foreign-birth/)
- [Irish descent or Irish associations](https://www.irishimmigration.ie/apply-for-irish-citizenship-by-irish-descent-or-irish-associations/)
- [Irish Nationality and Citizenship Act — revised text](https://revisedacts.lawreform.ie/eli/1956/act/26/revised/en/html)

These are starting points, not a completed or validated requirements dataset. Verify current instructions during content preparation.

The application must distinguish a complete checklist from one requiring clarification. It must not present an unsupported route or an unresolved requirement as fully covered.

## Initial release scope

Implement these routes first:

1. Foreign Births Registration.
2. Adult naturalisation through residence.
3. Naturalisation as the spouse or civil partner of an Irish citizen.

Start with one complete route, validate it, and then extend the shared system to the other two.

Add child applications, Irish associations, adoption, and other cases only after their requirements have been researched and validated.

### Outside the initial scope

- Submitting applications to government systems.
- Uploading or storing identity document scans.
- Automatically deciding or guaranteeing citizenship eligibility.
- Irish passport application checklists.
- Public internet hosting.

## Privacy and maintenance

- Allow checklist generation without an account.
- Avoid collecting document scans, passport numbers, or exact birth dates where less specific answers suffice.
- Make local saved progress explicit and allow users to delete it.
- Keep secrets in local environment configuration and out of version control.
- Give each requirement a review date and version.
- Review changes to official instructions before publishing updated rules.
- Indicate when a saved checklist uses an older version of the guidance.
- Review authentication, access controls, and deployment security before internet hosting.

## Delivery phases

| Phase | Deliverable |
| --- | --- |
| 1. Requirements research | Verified decision tables and document requirements for the first routes |
| 2. Product design | Screen layouts, question wording, and example checklists |
| 3. Local foundation | Application setup, local database, environment configuration, and startup instructions |
| 4. Back-end implementation | Data model, rules engine, APIs, and versioned content |
| 5. Front-end implementation | Questionnaire, answer review, checklist, progress tracking, and printing |
| 6. Validation | Scenario tests, source checks, accessibility checks, and local end-to-end verification |
| 7. Local release | Usable local application with setup and maintenance documentation |
| 8. Future internet deployment | Hosting selection and deployment after development is complete and publishing is requested |

## Validation approach

- Test representative applicant scenarios for each supported route.
- Cover conditional documents, name changes, minor applicants where supported, and missing answers.
- Confirm unsupported cases produce a clear explanation rather than an incomplete checklist presented as complete.
- Confirm every generated requirement has a source and preparation instructions.
- Verify answer changes update the checklist correctly.
- Verify saved progress, deletion, and printable output.
- Check the application can be started from the documented local setup.

## First milestone and success criteria

The first milestone is one complete citizenship route working locally from start to finish.

A user should be able to:

1. Choose the route.
2. Answer the relevant questions.
3. Review and correct their answers.
4. Receive a clear, personalised checklist.
5. Trace every document requirement to an official source.
6. Track readiness and print the checklist.

The milestone is complete when representative scenarios have been checked against official guidance and unresolved cases are clearly identified.
