"""Published evidence choices. Keep identity and each residence year separate."""
from copy import deepcopy


def item(key, title, points, note, source="guide", family=None):
    return {"id": key, "title": title, "points": points, "note": note,
            "source": source, "family": family or key}


IDENTITY = [
    item("passport_valid", "Current passport", 150, "Certified colour copy of the photo page; include the certification form.", family="passport"),
    item("passport_recent", "Passport expired less than 365 days ago", 75, "Combine with other identity evidence.", family="passport"),
    item("passport_old", "Passport expired more than 365 days ago", 50, "Combine with other identity evidence. At exactly 365 days, confirm the category with ISD.", family="passport"),
    item("irp_identity", "Irish Residence Permit (IRP)", 75, "Certified copy."),
    item("driving", "Current driving licence with photograph", 10, "Certified copy."),
    item("psc", "Public Services Card", 25, "Certified copy."),
    item("pps", "PPS number letter from DSP or employer", 25, "Certified copy; not residence evidence."),
    item("national_id", "EU-regulation-compliant national identity card", 50, "Certified copy."),
    item("identity_certificate", "Certificate of Identity / Red Cross ID / UNHCR ID", 50, "Only for applicants to whom this alternative applies; confirm acceptance with ISD."),
]
TYPE_A = [
    item("eds", "Revenue Employment Detail Summary", 100, "Your own name and the claimed year.", "proofs"),
    item("p60", "P60", 100, "For an older year for which a P60 was issued."),
    item("revenue", "Revenue statement / tax-record letter", 100, "Must document the claimed year."),
    item("dsp", "DSP Annual Contribution Statement", 100, "Must show contributions or claims; an empty record is insufficient.", "proofs"),
    item("dsp_payment", "DSP Payment Statement", 100, "Accepted DSP alternative; child benefit alone is insufficient.", "proofs"),
    item("bank", "Bank statements", 100, "Show Irish point-of-sale activity and outlet addresses. The guide specifies at least 3 transactions per month for 3 months. Check the portal's requested coverage."),
    item("employer", "Employer letter confirming employment dates", 100, "Dates must cover the claimed period."),
]
TYPE_B = [
    item("utility", "Utility bill", 50, "Gas, electricity, water or broadband. Show your name, address and date."),
    item("phone", "Phone bill", 50, "Mobile or landline."),
    item("rent", "Rent agreement / tenancy letter", 50, "Must cover the claimed year."),
    item("medical", "Medical / hospital letter", 50, "Must confirm your address."),
    item("credit", "Credit card statement", 50, "For the claimed year."),
    item("school", "School / college letter", 50, "Show residence and relevant attendance dates; dependent applicants have separate rules."),
    item("housing", "Housing authority letter", 50, "Confirm your residence and dates."),
    item("ipas", "IPAS / Direct Provision letter", 50, "Proves where you lived; does not make asylum-waiting time count as qualifying residence."),
]
# Do not silently promote historical or unclassified examples into today's calculator.
OTHER_RESIDENCE = [
    item("mortgage", "Annual mortgage statement", 50, "50 points in the 2024 scorecard. Not separately listed in the current table; confirm with ISD before relying on it.", "legacy_scorecard"),
    item("doctor_history", "Medical Practitioner Employment History Summary", 50, "HSE / voluntary-hospital doctors: 50 in the 2024 scorecard; currently accepted, but the current page does not restate a score. Confirm with ISD.", "legacy_scorecard"),
    item("household", "Bin collection, TV licence, cable / satellite bill", None, "Listed as residence examples; the current proofs page does not give an individual score.", "proofs"),
    item("tenancy_board", "Tenancy-board correspondence", None, "Listed as evidence; confirm its category and points.", "proofs"),
    item("government", "Local property tax / other government or social-welfare correspondence", None, "Listed as evidence; confirm its category and points. DSP annual statements are listed separately above.", "proofs"),
]


def scorecard(route):
    if route == "fbr":
        return None
    years = 3 if route == "spouse" else 5
    return {"identity_target": 150, "residence_target": 150, "years": years,
            "identity": deepcopy(IDENTITY), "type_a": deepcopy(TYPE_A),
            "type_b": deepcopy(TYPE_B), "other_residence": deepcopy(OTHER_RESIDENCE),
            "period": "The 12 months before applying, plus 2 other years in the preceding 4 years." if years == 3 else
                      "The 12 months before applying, plus 4 other years in the preceding 8 years."}


def validate_selection(route, selection=None):
    """Never trust submitted point totals; accept document IDs only."""
    selection = {} if selection is None else selection
    if not isinstance(selection, dict) or set(selection) - {"identity", "years"}:
        raise ValueError("Invalid points selection.")
    identity, years = selection.get("identity", []), selection.get("years", [])
    if not isinstance(identity, list) or not isinstance(years, list):
        raise ValueError("Invalid points selection.")
    if route == "fbr":
        if identity or years:
            raise ValueError("Foreign Births Registration does not use points.")
        return {"identity": [], "years": []}
    card = scorecard(route)
    lookup = {d["id"]: d for d in IDENTITY}
    seen = set()
    for key in identity:
        if not isinstance(key, str) or key not in lookup:
            raise ValueError("Unknown identity document.")
        if key in seen:
            raise ValueError("Select each document option only once.")
        seen.add(key)
    if len(years) > card["years"]:
        raise ValueError("Too many residence years.")
    cleaned_years = []
    allowed = {"a": {d["id"] for d in TYPE_A}, "b": {d["id"] for d in TYPE_B}}
    for row in years:
        if not isinstance(row, dict) or set(row) - {"a", "b"}:
            raise ValueError("Invalid residence year.")
        clean = {}
        for key in ("a", "b"):
            value = row.get(key, "")
            if not isinstance(value, str) or (value and value not in allowed[key]):
                raise ValueError("Choose a document from the correct residence category.")
            clean[key] = value
        cleaned_years.append(clean)
    while len(cleaned_years) < card["years"]:
        cleaned_years.append({"a": "", "b": ""})
    return {"identity": list(identity), "years": cleaned_years}


def totals(route, selection=None):
    selected = validate_selection(route, selection)
    if route == "fbr":
        return None
    identity = sum(d["points"] for d in IDENTITY if d["id"] in selected["identity"])
    passport_count = sum(d["family"] == "passport" for d in IDENTITY if d["id"] in selected["identity"])
    year_totals = [(100 if row["a"] else 0) + (50 if row["b"] else 0) for row in selected["years"]]
    return {"identity": identity, "identity_met": identity >= 150,
            "passport_overlap": passport_count > 1,
            "years": year_totals, "residence_met": all(p == 150 for p in year_totals)}
