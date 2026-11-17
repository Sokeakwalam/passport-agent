import unittest

from rules import SOURCES, all_questions, clean_answers, evaluate


def answers(route, **changes):
    base = {
        "adult": "yes", "born_abroad": "yes", "connection": "grandparent",
        "adoption": "no", "parent_alive": "yes", "grandparent_alive": "no",
        "parent_name": "no", "grandparent_name": "yes", "name_change": "no",
        "language": "yes", "missing": "no", "special": "standard",
        "nationality": "other", "location": "state", "residence_confirmed": "yes",
        "passport": "yes", "partner_irish": "yes", "relationship": "married",
        "relationship_confirmed": "yes", "parent_before": "yes",
    }
    base.update(changes)
    keys = {q["id"] for q in all_questions(route)}
    return clean_answers(route, {k: v for k, v in base.items() if k in keys})


class RulesTests(unittest.TestCase):
    def test_grandparent_chain_and_deceased_relative(self):
        r = evaluate("fbr", answers("fbr"))
        docs = {d["id"]: d for d in r["documents"]}
        self.assertEqual(r["status"], "preparation")
        self.assertEqual(docs["grandparent_identity"]["title"], "Civil death certificate")
        self.assertEqual(docs["grandparent_identity"]["format"], "Original")
        self.assertIn("grandparent_name", docs)
        self.assertNotIn("you_name", docs)
        self.assertIn("parent_birth", docs)

    def test_parent_certificate_paths(self):
        for connection, title in [
            ("parent_fbr", "Foreign Birth Registration certificate"),
            ("parent_naturalised", "Irish naturalisation certificate"),
        ]:
            r = evaluate("fbr", answers("fbr", connection=connection))
            docs = {d["id"]: d for d in r["documents"]}
            self.assertEqual(docs["parent_citizenship"]["title"], title)
            self.assertNotIn("grandparent_birth", docs)

    def test_citizenship_timing_and_already_citizen_block_checklist(self):
        for changes in [
            {"connection": "parent_fbr", "parent_before": "no"},
            {"connection": "parent_fbr", "parent_before": "unknown"},
            {"connection": "parent_irish_born"}, {"born_abroad": "no"},
            {"adoption": "yes"}, {"adult": "no"},
        ]:
            with self.subTest(changes=changes):
                r = evaluate("fbr", answers("fbr", **changes))
                self.assertEqual(r["documents"], [])
                self.assertEqual(r["status"], "needs_route_review")

    def test_unknown_names_remain_conditional(self):
        r = evaluate("fbr", answers("fbr", parent_name="unknown"))
        d = next(d for d in r["documents"] if d["id"] == "parent_name")
        self.assertTrue(d["conditional"])
        self.assertEqual(r["status"], "needs_clarification")

    def test_changing_connection_removes_stale_answers(self):
        a = answers("fbr")
        a.update(connection="parent_fbr", parent_before="yes")
        cleaned = clean_answers("fbr", a)
        self.assertNotIn("grandparent_alive", cleaned)
        self.assertNotIn("grandparent_name", cleaned)

    def test_exempt_nationalities_do_not_get_irp_requirement(self):
        exempt = evaluate("residence", answers("residence", nationality="exempt"))
        other = evaluate("residence", answers("residence"))
        self.assertNotIn("irp", [d["id"] for d in exempt["documents"]])
        self.assertIn("irp", [d["id"] for d in other["documents"]])
        self.assertNotIn("partner_citizenship", [d["id"] for d in other["documents"]])

    def test_spouse_specific_evidence(self):
        r = evaluate("spouse", answers("spouse"))
        ids = {d["id"] for d in r["documents"]}
        self.assertTrue({"relationship", "partner_citizenship", "joint_address", "spousal_declaration"}.issubset(ids))

    def test_unsupported_naturalisation_cases(self):
        for changes in [{"special": "dependent"}, {"special": "refugee"}, {"location": "ni"}, {"partner_irish": "no"}]:
            r = evaluate("spouse", answers("spouse", **changes))
            self.assertEqual(r["status"], "needs_route_review")
            self.assertFalse(r["documents"])

    def test_translation_and_alternative_identity_are_visible(self):
        r = evaluate("residence", answers("residence", passport="no", language="no", missing="yes"))
        self.assertGreaterEqual(len(r["notices"]), 2)
        self.assertTrue(r["scorecard"]["identity"])
        self.assertIn("translations", [d["id"] for d in r["documents"]])

    def test_rejects_missing_unknown_and_invalid_answers(self):
        for a in [{}, {**answers("fbr"), "adult": True}, {**answers("fbr"), "injected": "yes"}]:
            with self.assertRaises(ValueError):
                evaluate("fbr", a)
        with self.assertRaises(ValueError):
            evaluate("not-a-route", {})

    def test_every_document_has_traceable_source_and_instructions(self):
        for route in ["fbr", "residence", "spouse"]:
            r = evaluate(route, answers(route))
            ids = [d["id"] for d in r["documents"]]
            self.assertEqual(len(ids), len(set(ids)))
            for d in r["documents"]:
                self.assertIn(d["source"], SOURCES)
                for key in ["format", "reason", "detail", "owner"]:
                    self.assertTrue(d[key])
                self.assertTrue(SOURCES[d["source"]]["url"].startswith("https://"))

    def test_naturalisation_is_explicitly_not_exhaustive(self):
        for route in ["residence", "spouse"]:
            r = evaluate(route, answers(route))
            self.assertEqual(r["status"], "needs_clarification")
            self.assertTrue(any("not yet an exhaustive" in n["text"] for n in r["notices"]))


if __name__ == "__main__":
    unittest.main()
