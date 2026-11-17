import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from build_pages import build, package_site
from rules import ROUTES, all_questions, evaluate
from scorecards import totals, validate_selection

ROOT = Path(__file__).resolve().parents[1]


def all_answers(route):
    questions = all_questions(route)

    def visit(index, answers):
        if index == len(questions):
            yield answers
            return
        q = questions[index]
        if not all(answers.get(key) in allowed for key, allowed in q["when"].items()):
            yield from visit(index + 1, answers)
            return
        for option in q["options"]:
            yield from visit(index + 1, {**answers, q["id"]: option["value"]})

    return visit(0, {})


class PagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "site"
        cls.data = build(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_project_subpath_assets_and_private_data_exclusion(self):
        html = (self.output / "index.html").read_text()
        self.assertNotIn('href="/', html)
        self.assertNotIn('src="/', html)
        self.assertLess(html.index('src="./pages.js"'), html.index('src="./app.js"'))
        self.assertEqual(set(p.name for p in self.output.iterdir()),
                         {"index.html", "app.js", "pages.js", "pages-data.json", "styles.css", "favicon.svg", ".nojekyll"})
        self.assertEqual(self.data["catalog"]["hosting"]["mode"], "browser")
        archive = Path(self.temp.name) / "site.zip"
        package_site(self.output, archive)
        with zipfile.ZipFile(archive) as zipped:
            self.assertIsNone(zipped.testzip())
            self.assertIn("index.html", zipped.namelist())
            self.assertFalse(any("sqlite" in name or name.startswith("data/") for name in zipped.namelist()))

    @unittest.skipUnless(shutil.which("node"), "Node is needed for the browser-runtime parity test")
    def test_browser_matches_python_for_every_answer_combination(self):
        fixtures = []
        for route in ROUTES:
            route = route["id"]
            for answers in all_answers(route):
                result = evaluate(route, answers)
                result["selection"] = validate_selection(route)
                result["totals"] = totals(route) if result["scorecard"] else None
                canonical = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                fixtures.append({"route": route, "answers": answers,
                                 "digest": hashlib.sha256(canonical.encode()).hexdigest()})
        self.assertEqual(len(fixtures), self.data["compiled_combinations"])
        fixture_file = Path(self.temp.name) / "fixtures.json"
        fixture_file.write_text(json.dumps(fixtures))
        result = subprocess.run(["node", str(ROOT / "tests" / "pages_runtime.cjs"),
                                 str(self.output / "pages-data.json"), str(fixture_file)],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
