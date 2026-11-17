"""Versioned citizenship preparation rules; no network or persistence dependencies."""
from copy import deepcopy
from scorecards import scorecard

VERSION = "2026-10-20.2"
REVIEWED = "2026-10-20"
SOURCES = {
    "legacy_scorecard": {"title": "ISD · Earlier residence scorecard (2024)", "url": "https://www.irishimmigration.ie/wp-content/uploads/2024/04/Citizenship-Guidance-Document-April-2024.pdf", "section": "Historical scores; URL now redirects to current guide. Confirm these alternatives with ISD."},
    "fbr": {
        "title": "DFA · Foreign Births Registration",
        "url": "https://www.ireland.ie/en/dfa/citizenship/born-abroad/registering-a-foreign-birth/",
        "section": "Adult applicant; photos; witnesses",
    },
    "guide": {
        "title": "ISD · Citizenship guide",
        "url": "https://www.irishimmigration.ie/how-to-become-an-irish-citizen-guide/",
        "section": "Adult applications; certification; spouse declarations",
    },
    "proofs": {
        "title": "ISD · Identity and residence evidence",
        "url": "https://www.irishimmigration.ie/how-to-become-a-citizen/become-an-irish-citizen-by-naturalisation/proofs-of-identity-and-residence/",
        "section": "Identity scorecard; residence scorecard; exceptions",
    },
    "marriage": {
        "title": "ISD · Naturalisation supporting documents",
        "url": "https://www.irishimmigration.ie/wp-content/uploads/2024/04/Citizenship-Guidance-Document-April-2024.pdf",
        "section": "Spouse / civil partner supporting documents (read with current ISD guide)",
    },
    "name": {
        "title": "ISD · Name changes",
        "url": "https://www.irishimmigration.ie/my-situation-has-changed-since-i-arrived-in-ireland/change-of-name-licence/",
        "section": "Evidence of change of name",
    },
    "birth": {
        "title": "ISD · Citizenship by birth or descent",
        "url": "https://www.irishimmigration.ie/how-to-become-a-citizen/check-if-you-are-an-irish-citizen-by-birth-or-descent/",
        "section": "Birth and descent eligibility",
    },
}
for source in SOURCES.values():
    source["reviewed"] = REVIEWED

ROUTES = [
    {"id": "fbr", "number": "01", "title": "Irish parent or grandparent",
     "subtitle": "Foreign Births Registration", "description": "For adults born abroad with an Irish-born grandparent or a qualifying Irish parent.", "tag": "Irish ancestry", "source": "fbr"},
    {"id": "residence", "number": "02", "title": "Living in Ireland",
     "subtitle": "Adult naturalisation", "description": "Prepare the evidence for an application based on your qualifying residence.", "tag": "Residence", "source": "guide"},
    {"id": "spouse", "number": "03", "title": "Married to an Irish citizen",
     "subtitle": "Spouse or civil partner", "description": "For adults applying through marriage or civil partnership with an Irish citizen.", "tag": "Irish partner", "source": "guide"},
]
YESNO = [("yes", "Yes"), ("no", "No")]
YESUNKNOWN = YESNO + [("unknown", "I’m not sure")]


def q(key, title, options, help_text="", when=None):
    return {"id": key, "title": title, "options": [{"value": v, "label": l} for v, l in options],
            "help": help_text, "when": when or {}}


COMMON = [
    q("adult", "Are you 18 or older?", YESNO, "This version prepares adult application checklists."),
]
FBR = [
    q("born_abroad", "Were you born outside the island of Ireland?", YESUNKNOWN,
      "The island of Ireland includes Northern Ireland."),
    q("connection", "Who in your family is Irish?", [
        ("grandparent", "A grandparent born on the island of Ireland"),
        ("parent_fbr", "My parent has a Foreign Birth Registration certificate"),
        ("parent_naturalised", "My parent has an Irish naturalisation certificate"),
        ("parent_irish_born", "An Irish citizen parent born on the island of Ireland"),
        ("other", "Another connection / I’m not sure")]),
    q("parent_before", "Did your parent become Irish before you were born?", YESUNKNOWN,
      "Compare their registration or naturalisation date with your birth date.",
      {"connection": ["parent_fbr", "parent_naturalised"]}),
    q("adoption", "Were you or the parent in this family line adopted?", YESUNKNOWN,
      "Adoption cases need additional checks outside this version’s coverage."),
    q("parent_alive", "Is this parent still alive?", YESNO),
    q("grandparent_alive", "Is your Irish-born grandparent still alive?", YESNO, when={"connection": ["grandparent"]}),
    q("parent_name", "Has that parent married or changed their name?", YESUNKNOWN),
    q("grandparent_name", "Has that grandparent married or changed their name?", YESUNKNOWN, when={"connection": ["grandparent"]}),
]
NAT = [
    q("special", "Does any of this apply to you?", [
        ("standard", "None of these"),
        ("dependent", "I am 18–23, in education, and financially dependent on my parents"),
        ("refugee", "I have refugee status or I am stateless"),
        ("association", "I am asking for an exception because of Irish family connections")],
      "These situations can need different documents."),
    q("nationality", "Are you a UK, EU, EEA or Swiss citizen?", [
        ("exempt", "Yes"), ("other", "No")],
      "This decides whether to include an Irish Residence Permit. EEA includes Iceland, Liechtenstein and Norway."),
    q("location", "Where have you lived during the years you want to include?", [
        ("state", "Republic of Ireland only"),
        ("ni", "Some or all of the time in Northern Ireland")],
      "The documents differ for Northern Ireland."),
]
SPOUSE = [
    q("partner_irish", "Is your spouse or civil partner an Irish citizen?", YESUNKNOWN),
    q("relationship", "Are you married or in a civil partnership?", [
        ("married", "Married"), ("civil", "Civil partnership"), ("other", "Neither")]),
]
END = [
    q("name_change", "Is your name different on any of your documents?", YESUNKNOWN,
      "For example, your birth certificate has your old surname and your passport has your married name."),
    q("language", "Are your documents written in English or Irish?", YESUNKNOWN,
      "Choose No if any document is in another language. Choose I’m not sure if you have not collected them yet."),
]


def all_questions(route):
    if route not in {r["id"] for r in ROUTES}:
        raise ValueError("Choose a supported route.")
    ending = deepcopy(END)
    if route == "fbr":
        ending[0]["title"] = "Have you ever married or changed your name?"
        ending[0]["help"] = "A marriage certificate may be needed even if your name stayed the same."
    return COMMON + (FBR if route == "fbr" else NAT + (SPOUSE if route == "spouse" else [])) + ending


def questions(route, answers):
    return [x for x in all_questions(route)
            if all(answers.get(k) in values for k, values in x["when"].items())]


def clean_answers(route, answers, complete=False):
    if not isinstance(answers, dict):
        raise ValueError("Answers must be an object.")
    known = {x["id"]: x for x in all_questions(route)}
    if any(k not in known for k in answers):
        raise ValueError("Unknown question.")
    for key, value in answers.items():
        if not isinstance(value, str) or value not in {o["value"] for o in known[key]["options"]}:
            raise ValueError("Invalid answer for " + key + ".")
    cleaned = {x["id"]: answers[x["id"]] for x in questions(route, answers) if x["id"] in answers}
    if complete and any(x["id"] not in cleaned for x in questions(route, cleaned)):
        raise ValueError("Answer every applicable question before generating a checklist.")
    return cleaned


def evaluate(route, answers):
    a = clean_answers(route, answers, complete=True)
    notices, blockers, docs = [], [], []

    def notice(text, source="guide", blocking=False):
        (blockers if blocking else notices).append({"text": text, "source": source})

    def doc(key, title, owner, form, detail, reason, source, conditional=False):
        docs.append({"id": key, "title": title, "owner": owner, "format": form,
                     "detail": detail, "reason": reason, "source": source,
                     "conditional": conditional, "requirement": "Confirm if needed" if conditional else "Required",
                     "points": None})

    if a["adult"] == "no":
        notice("Child applications are outside this version. Use the official minor-applicant instructions.", "fbr" if route == "fbr" else "guide", True)
    if route == "fbr":
        if a["born_abroad"] != "yes":
            notice("Check citizenship by birth before using Foreign Births Registration.", "birth", True)
        if a["connection"] == "parent_irish_born":
            notice("You may already be an Irish citizen through your Irish-born parent. Check the DFA guidance before applying for registration.", "fbr", True)
        if a["connection"] == "other":
            notice("Your family connection needs individual review with the DFA.", "fbr", True)
        if a.get("parent_before", "yes") != "yes":
            notice("Your parent’s citizenship date must be checked against your birth date before this route can be used.", "fbr", True)
        if a["adoption"] != "no":
            notice("Adoption in the family chain requires a separate document review with the DFA.", "fbr", True)
    else:
        if a["special"] != "standard":
            notice("This version does not cover the additional evidence for this applicant category. Consult the official guidance.", "guide", True)
        if a["location"] == "ni":
            notice("Northern Ireland residence requires a separate check of eligibility and evidence; this version covers Republic of Ireland evidence only.", "guide", True)
        if route == "spouse":
            if a["partner_irish"] != "yes" or a["relationship"] == "other":
                notice("The Irish citizenship and legal relationship conditions need confirmation before using this route.", "guide", True)
    if blockers:
        return {"version": VERSION, "route": route, "answers": a, "status": "needs_route_review",
                "documents": [], "notices": blockers, "reviewed": REVIEWED, "scorecard": None}

    if route == "fbr":
        doc("application", "Registration application", "You", "Signed and witnessed",
            "Complete the online form; print and sign with an eligible witness.", "Starts your registration.", "fbr")
        doc("photos", "Four colour photographs", "You", "Physical photographs",
            "Have two witnessed. Follow DFA photo specifications.", "Identifies the applicant.", "fbr")
        doc("address", "Two separate address proofs", "You", "Originals",
            "Provide evidence of your current address.", "Confirms where you live.", "fbr")
        people = [("you", "You"), ("parent", "Your parent")]
        if a["connection"] == "grandparent":
            people.append(("grandparent", "Your grandparent"))
        for key, owner in people:
            doc(key + "_birth", "Civil birth certificate", owner, "Original",
                "Must show parental details.", "Connects the family records.", "fbr")
            alive = key == "you" or a[key + "_alive"] == "yes"
            doc(key + "_identity", "Current government photo ID" if alive else "Civil death certificate",
                owner, "Certified copy" if alive else "Original",
                "Choose a current passport, driving licence or national identity card. Have an eligible witness certify the copy; do not send original photo ID." if alive else "Provide the civil record.",
                "Verifies this person’s identity.", "fbr")
            changed = a["name_change"] if key == "you" else a[key + "_name"]
            if changed != "no":
                doc(key + "_name", "Marriage or name-change record", owner, "Original",
                    "Provide the applicable civil record.", "Links the names across records.", "fbr", changed == "unknown")
        if a["connection"] != "grandparent":
            doc("parent_citizenship", "Foreign Birth Registration certificate" if a["connection"] == "parent_fbr" else "Irish naturalisation certificate",
                "Your parent", "Original", "Check the citizenship date.", "Establishes the parent’s citizenship.", "fbr")
    else:
        doc("birth", "Birth certificate", "You", "Certified copy",
            "Include the certification form required by ISD.", "Establishes your birth details.", "guide")
        doc("certification", "Document certification forms", "You", "Completed and signed",
            "Upload the relevant forms alongside certified documents.", "Records the certification.", "guide")
        doc("declaration", "Application and declarations", "You", "Online application",
            "Complete the application’s required declarations and witness instructions.", "Records your application.", "guide")
        notice("This naturalisation list covers the published guidance. The portal’s downloadable document checklist could not be fully reviewed for this edition. Compare it with your portal checklist before submission; this is not yet an exhaustive application list.")
        if a["nationality"] == "other":
            doc("irp", "Irish Residence Permit", "You", "Copy",
                "Include your current card and applicable residence permission evidence. A certified IRP can also supply 75 identity points if selected in the identity table; it supplies no residence points.", "Shows your immigration permission.", "guide")
            doc("permissions", "Residence permission history", "You", "Supporting records",
                "Check permission dates and the official residence calculator.", "Supports qualifying residence.", "guide")
        if a["name_change"] != "no":
            doc("name", "Marriage or name-change evidence", "You", "Supporting civil record",
                "Link your earlier and current names using the applicable marriage or deed-poll record. Confirm the upload format with ISD.",
                "Explains differences between identity records.", "name", a["name_change"] == "unknown")
        if route == "spouse":
            doc("relationship", "Marriage certificate" if a["relationship"] == "married" else "Civil partnership certificate", "You and your partner", "Certified copy",
                "Use the applicable certificate and current certification form.", "Documents your legal relationship.", "marriage")
            doc("partner_citizenship", "Partner’s Irish citizenship evidence", "Your partner", "Certified copy",
                "Provide ONE suitable certified record: Irish passport photo page; Irish birth certificate where it establishes citizenship; naturalisation certificate; Foreign Births Register certificate; or the parent’s Irish birth certificate where citizenship came through that parent.",
                "Establishes your partner’s citizenship.", "marriage")
            doc("joint_address", "Recent residence proofs for both partners", "You and your partner", "Copies",
                "Provide three different address proofs for EACH partner, covering the three months before applying. Options: utility bills, bank statements, rent/mortgage agreements, or employer/social-welfare letters. Show names, dates and the same address.",
                "Supports your shared residence.", "marriage")
            doc("spousal_declaration", "Spouse declaration" if a["relationship"] == "married" else "Civil partner declaration", "Your partner", "Signed before an authorised witness",
                "Use the correct ISD declaration for your relationship.", "Confirms the ongoing relationship.", "guide")
    if a["language"] != "yes":
        notice("Check translation requirements for each non-English/Irish document, including any accepted multilingual-form exception. Confirm with the receiving authority.", "fbr" if route == "fbr" else "guide")
        doc("translations", "Translations or accepted multilingual forms", "Supporting documents", "Confirm the applicable format",
            ("Provide a professionally certified translation and a copy of the original, with the translator’s signature and contact details. An accepted multilingual standard form can replace the translation where permitted." if route != "fbr" else "Check the DFA translation and multilingual-form rules for each affected civil record."),
            "Makes the records usable in the application.", "fbr" if route == "fbr" else "guide", True)
    for key in ("name_change", "parent_name", "grandparent_name"):
        if a.get(key) == "unknown":
            notice("Confirm whether a marriage or name-change record applies; it appears as conditional in your list.", "fbr" if route == "fbr" else "name")
            break
    for document in docs:
        document["points_label"] = "75 identity points if selected below" if document["id"] == "irp" else "Not scored"
    return {"version": VERSION, "route": route, "answers": a, "status": "needs_clarification" if notices else "preparation",
            "documents": docs, "notices": notices, "reviewed": REVIEWED, "scorecard": scorecard(route)}


def catalog():
    return {"version": VERSION, "reviewed": REVIEWED, "routes": deepcopy(ROUTES),
            "questions": {r["id"]: all_questions(r["id"]) for r in ROUTES},
            "sources": deepcopy(SOURCES)}
