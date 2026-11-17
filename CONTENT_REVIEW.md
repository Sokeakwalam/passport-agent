# Citizenship content review

Review date: 2026-10-20  
Rules version: 2026-10-20.2

## Sources reviewed

- DFA Foreign Births Registration: https://www.ireland.ie/en/dfa/citizenship/born-abroad/registering-a-foreign-birth/
  - Direct fetching returned HTTP 403; the web search service provided the indexed adult-applicant sections.
  - Adult cases: Irish-born grandparent, parent naturalised before birth, parent entered on the register before birth.
  - Identity, family civil records, photographs, address evidence, and witnessed application.
  - Full minor/adoption cases are intentionally excluded.
- ISD citizenship guide: https://www.irishimmigration.ie/how-to-become-an-irish-citizen-guide/
  - Adult categories, certification, identity, residence, relationship evidence, translation guidance.
- ISD identity and residence proofs: https://www.irishimmigration.ie/how-to-become-a-citizen/become-an-irish-citizen-by-naturalisation/proofs-of-identity-and-residence/
  - Identity points, annual residence points, and document alternatives.
- ISD 2024 supporting evidence guide: https://www.irishimmigration.ie/wp-content/uploads/2024/04/Citizenship-Guidance-Document-April-2024.pdf
  - Supplementary spouse evidence; must be read alongside current guide and portal instructions.
- ISD name changes: https://www.irishimmigration.ie/my-situation-has-changed-since-i-arrived-in-ireland/change-of-name-licence/
  - Examples of records linking names; not a substitute for the application-specific upload instructions.
- ISD birth/descent guidance: https://www.irishimmigration.ie/how-to-become-a-citizen/check-if-you-are-an-irish-citizen-by-birth-or-descent/
  - Referral for applicants who may already be Irish or need a different route.

## Decision table

| Circumstance | Behaviour |
| --- | --- |
| Under 18 | No adult checklist; official minor guidance |
| Born on the island of Ireland, selecting FBR | Birth/descent review |
| Irish-born Irish citizen parent | Existing-citizenship guidance |
| Grandparent connection | Applicant, parent, and grandparent documents |
| Parent registered/naturalised before applicant birth | Applicant and parent records plus citizenship certificate |
| Parent citizenship after birth or unknown date | Route review, no checklist |
| Deceased parent/grandparent | Civil death certificate instead of photo ID |
| Marriage/name change | Relevant civil/name-change record |
| Unknown name-change applicability | Conditional document and clarification notice |
| Adoption in family chain | Separate review, no checklist |
| Standard adult residence application | Core identity, residence, application evidence |
| UK/EU/EEA/Swiss group | No IRP requirement generated |
| Spouse/civil partner route | Relationship certificate, citizenship evidence, recent residence proofs, declaration |
| Non-Irish partner or no qualifying legal relationship | Route review, no checklist |
| Refugee/stateless, dependent young adult, or Irish associations | Separate review, no checklist |
| Northern Ireland residence | Separate review, no standard Republic evidence list |
| No current passport | Explicit alternative-identity review |
| Non-English/Irish documents or unknown language status | Translation clarification and conditional checklist entry |
| Missing/inconsistent records | Explicit clarification notice |

## Outstanding before claiming complete naturalisation coverage

The web tool could not parse these Word files, and shell network access was restricted:

- https://www.irishimmigration.ie/wp-content/uploads/2023/09/Citizenship-Online-Adult-Documents-Guide-Residence.docx
- https://www.irishimmigration.ie/wp-content/uploads/2023/05/citizenship/Citizenship-Online-Adult-Documents-Guide-Marriage.docx

Review the current portal downloads and reconcile all upload categories, photographs, declarations, passport/residence-history details, certification forms, and exceptions. Until then, every naturalisation result has an explicit non-exhaustive notice.

Also verify the full DFA instructions directly before release, including photo dimensions, witness details, translations, legacy records, and country-specific document exceptions. The current list links to the authority for these procedural specifications.

No source review in this file constitutes legal approval or an exhaustive audit. Preserve incomplete coverage labels until the outstanding checks are resolved.


## Revision: explicit document choices and points

Rechecked the live ISD guide, including **Citizenship Identity Scorecard** and **Residency Scoring System**. `scorecards.py` contains all nine rows in the current identity table, all named current Type A / Type B categories (split into individual choices for readability), and additional residence examples with their provenance.

- Identity target: 150 once, separate from residence.
- Residence: one Type A (100) and one Type B (50) for each claimed year. Five periods for standard residence, three for the spouse route. Rows represent qualifying periods, not automatically the last consecutive calendar years.
- Multiple identity options remain selectable above 150 points. All selections are preserved, and the tracker adds every selected row. Overlapping passport categories trigger a separate acceptance note. Repeated identical document IDs and user-supplied point values are rejected.
- Mortgage statements and medical-practitioner employment history retain their historical 50-point labels with a clear confirmation warning. The old PDF URL now redirects to the guide. These are not included in the live calculator because the current table does not separately assign their points.
- General household/government examples without an explicit current individual score are displayed as unconfirmed, not zero and not guessed.
- Selecting evidence only plans the points. Certification, dates, legal eligibility and acceptance remain separate.
- Six factual questions for standard residence and eight for spouse applications replace the previous self-certification prompts. Old-version saved journeys restart the changed questionnaire, preserving their stored record until saved again.

The UI, text export, and print view show the evidence choices and point targets. Saved progress includes identity selections and independent year rows. The Word portal-checklist coverage limitation above remains unchanged.
