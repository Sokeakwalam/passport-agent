"""Compile the existing Python checklist rules into a static GitHub Pages site.

The decision graph is generated from every valid answer combination, so browser
and Python hosting use the same content and decisions without parallel rule code.
Only public rules and assets are exported; saved journeys are never read.
"""
import argparse
import json
from pathlib import Path
import shutil
import zipfile

from rules import ROUTES, all_questions, catalog, evaluate
from scorecards import scorecard

ROOT = Path(__file__).resolve().parent


class Pool:
    def __init__(self):
        self.items = []
        self.keys = {}

    def add(self, value):
        key = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if key not in self.keys:
            self.keys[key] = len(self.items)
            self.items.append(value)
        return self.keys[key]


def compile_rules():
    documents, notices, results, nodes = Pool(), Pool(), Pool(), Pool()
    roots, combinations = {}, 0
    for route in ROUTES:
        route_id = route["id"]
        questions = all_questions(route_id)

        def visit(index, answers):
            nonlocal combinations
            if index == len(questions):
                outcome = evaluate(route_id, answers)
                combinations += 1
                value = {
                    "status": outcome["status"],
                    "documents": [documents.add(d) for d in outcome["documents"]],
                    "notices": [notices.add(n) for n in outcome["notices"]],
                    "scorecard": outcome["scorecard"] is not None,
                }
                return nodes.add({"result": results.add(value)})
            question = questions[index]
            if not all(answers.get(k) in allowed for k, allowed in question["when"].items()):
                return visit(index + 1, answers)
            branches = {}
            for option in question["options"]:
                branches[option["value"]] = visit(index + 1, {**answers, question["id"]: option["value"]})
            if len(set(branches.values())) == 1:
                return next(iter(branches.values()))
            return nodes.add({"question": question["id"], "branches": branches})

        roots[route_id] = visit(0, {})
    data = catalog()
    data["hosting"] = {"mode": "browser"}
    return {"catalog": data, "roots": roots, "nodes": nodes.items, "results": results.items,
            "documents": documents.items, "notices": notices.items,
            "scorecards": {r["id"]: scorecard(r["id"]) for r in ROUTES},
            "compiled_combinations": combinations}


def build(output=ROOT / "docs"):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = compile_rules()
    for name in ["app.js", "styles.css", "favicon.svg"]:
        shutil.copyfile(ROOT / "static" / name, output / name)
    shutil.copyfile(ROOT / "static" / "pages.js", output / "pages.js")
    html = (ROOT / "static" / "index.html").read_text()
    html = html.replace('href="/', 'href="./').replace('src="/', 'src="./')
    html = html.replace('<script src="./app.js" defer></script>',
                        '<script src="./pages.js" defer></script>\n  <script src="./app.js" defer></script>')
    html = html.replace("<i></i> Local edition", "<i></i> Irish citizenship")
    (output / "index.html").write_text(html)
    (output / "pages-data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    (output / ".nojekyll").write_text("")
    return data


def package_site(output, target):
    """Archive static assets only, with index.html directly at the ZIP root."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(Path(output).iterdir()):
            if file.is_file():
                archive.write(file, file.name)


def package_source(target):
    """Use an allowlist so databases, credentials and old archives cannot leak."""
    files = [ROOT / name for name in [
        "README.md", "DEPLOY_GITHUB.md", "CONTENT_REVIEW.md", "PLAN.md", ".gitignore",
        "requirements.txt", "build_pages.py", "rules.py", "scorecards.py", "server.py",
        "hosted.py", "pythonanywhere_wsgi.py", "DEPLOY_PYTHONANYWHERE.md",
    ]]
    for folder in ["docs", "static", "tests"]:
        files.extend(p for p in (ROOT / folder).iterdir() if p.is_file() and p.suffix != ".pyc")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(files):
            archive.write(file, file.relative_to(ROOT))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the GitHub Pages edition.")
    parser.add_argument("--output", type=Path, default=ROOT / "docs")
    parser.add_argument("--zip", action="store_true", help="Also create dist/passport-agent-github-pages.zip")
    parser.add_argument("--source-zip", action="store_true", help="Also create the source upload archive including docs/")
    args = parser.parse_args()
    data = build(args.output)
    print(f"Built {args.output}: {data['compiled_combinations']:,} answer combinations, {len(data['nodes']):,} shared decision nodes.")
    if args.zip:
        target = ROOT / "dist" / "passport-agent-github-pages.zip"
        package_site(args.output, target)
        print(f"Static upload archive: {target}")
    if args.source_zip:
        target = ROOT / "dist" / "passport-agent-github-source.zip"
        package_source(target)
        print(f"Full project archive: {target}")
