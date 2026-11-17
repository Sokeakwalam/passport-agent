import unittest

from rules import all_questions, evaluate
from scorecards import scorecard, totals, validate_selection
from tests.test_rules import answers


class ScorecardTests(unittest.TestCase):
    def test_identity_is_once_and_residence_years_are_independent(self):
        result = totals("residence", {"identity": ["passport_valid"], "years": [{"a": "bank", "b": "rent"}]})
        self.assertEqual(result["identity"], 150)
        self.assertTrue(result["identity_met"])
        self.assertEqual(result["years"], [150, 0, 0, 0, 0])
        self.assertFalse(result["residence_met"])

    def test_alternative_identity_combination(self):
        self.assertEqual(totals("spouse", {"identity": ["passport_recent", "irp_identity"]})["identity"], 150)

    def test_all_selected_rows_add_to_total_and_flag_passport_overlap(self):
        selected = {"identity": ["passport_valid", "passport_old", "irp_identity", "psc"]}
        self.assertEqual(len(validate_selection("residence", selected)["identity"]), 4)
        self.assertEqual(totals("residence", selected)["identity"], 300)
        for ids in [["irp_identity", "irp_identity"]]:
            with self.assertRaises(ValueError):
                totals("residence", {"identity": ids})

    def test_screenshot_selection_totals_235(self):
        selected = {"identity": ["passport_recent", "passport_old", "irp_identity", "driving", "psc"]}
        result = totals("residence", selected)
        self.assertEqual(result["identity"], 235)
        self.assertTrue(result["passport_overlap"])
        self.assertFalse(totals("residence", {"identity": ["passport_valid"]})["passport_overlap"])

    def test_type_b_alone_is_insufficient(self):
        value = totals("spouse", {"years": [{"b": "utility"}] * 3})
        self.assertEqual(value["years"], [50, 50, 50])
        self.assertFalse(value["residence_met"])
        with self.assertRaises(ValueError):
            totals("spouse", {"years": [{"a": "utility", "b": "phone"}]})

    def test_all_years_must_be_filled(self):
        self.assertTrue(totals("spouse", {"years": [{"a": "eds", "b": "phone"}] * 3})["residence_met"])
        self.assertFalse(totals("residence", {"years": [{"a": "eds", "b": "phone"}] * 3})["residence_met"])

    def test_reject_unknown_legacy_and_injected_totals(self):
        for selection in [{"identity": ["made_up"]}, {"identity": "passport_valid"},
                          {"years": [{"a": "bank", "b": "mortgage"}]},
                          {"years": [{"a": "bank", "points": 900}]},
                          {"points": 150}, {"years": [{}] * 6}]:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                validate_selection("residence", selection)

    def test_fbr_has_no_points(self):
        self.assertIsNone(evaluate("fbr", answers("fbr"))["scorecard"])
        with self.assertRaises(ValueError):
            totals("fbr", {"identity": ["passport_valid"]})

    def test_all_current_scorecard_rows_are_present(self):
        c = scorecard("residence")
        self.assertEqual(len(c["identity"]), 9)
        self.assertTrue({"eds", "p60", "revenue", "dsp", "dsp_payment", "bank", "employer"} <= {d["id"] for d in c["type_a"]})
        self.assertTrue({"utility", "phone", "rent", "medical", "credit", "school", "housing", "ipas"} <= {d["id"] for d in c["type_b"]})
        self.assertEqual({d["points"] for d in c["type_a"]}, {100})
        self.assertEqual({d["points"] for d in c["type_b"]}, {50})

    def test_questions_only_ask_for_personal_facts(self):
        questions = all_questions("residence")
        self.assertEqual(len(questions), 6)
        self.assertFalse({"residence_confirmed", "relationship_confirmed", "missing", "passport"} & {q["id"] for q in questions})
        self.assertFalse(any("Have you checked" in q["title"] for q in questions))

    def test_required_docs_do_not_force_every_scored_alternative(self):
        docs = evaluate("residence", answers("residence"))["documents"]
        self.assertNotIn("passport", [d["id"] for d in docs])
        self.assertTrue(all(d["points"] is None for d in docs))

