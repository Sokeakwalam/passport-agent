"""Local-only Passport Agent HTTP API and static-file server."""
import argparse
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import secrets
import sqlite3
from urllib.parse import urlsplit

from rules import VERSION, catalog, clean_answers, evaluate
from scorecards import validate_selection, totals

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


def response_headers(new_cookie=None, secure=False):
    headers = [
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
        ("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"),
    ]
    if new_cookie:
        headers.append(("Set-Cookie", f"pa_session={new_cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000" + ("; Secure" if secure else "")))
    return headers


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS drafts (
                session TEXT PRIMARY KEY, payload TEXT NOT NULL, updated TEXT NOT NULL)""")

    def connect(self):
        return sqlite3.connect(self.path)

    def get(self, session):
        with self.connect() as db:
            row = db.execute("SELECT payload, updated FROM drafts WHERE session = ?", (session,)).fetchone()
        if not row:
            return None
        return {**json.loads(row[0]), "updated": row[1]}

    def put(self, session, payload):
        updated = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute("INSERT INTO drafts VALUES (?, ?, ?) ON CONFLICT(session) DO UPDATE SET payload=excluded.payload, updated=excluded.updated",
                       (session, json.dumps(payload), updated))
        return updated

    def delete(self, session):
        with self.connect() as db:
            db.execute("DELETE FROM drafts WHERE session = ?", (session,))


class Handler(BaseHTTPRequestHandler):
    server_version = "PassportAgent/0.1"

    def log_message(self, fmt, *args):
        # Do not log request payloads or answers.
        super().log_message(fmt, *args)

    def begin(self):
        expected = getattr(self.server, "allowed_hosts", {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"})
        if self.headers.get("Host", "") not in expected:
            self.respond(403, {"error": "Use the configured application address."})
            return False
        self.new_cookie = None
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        value = cookie["pa_session"].value if "pa_session" in cookie else ""
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            value = secrets.token_hex(32)
            self.new_cookie = value
        self.session = value
        return True

    def respond(self, status, payload, content_type="application/json; charset=utf-8"):
        body = json.dumps(payload).encode() if isinstance(payload, (dict, list)) else payload
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in response_headers(getattr(self, "new_cookie", None), getattr(self, "scheme", "http") == "https"):
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.begin():
            return
        path = urlsplit(self.path).path
        if path == "/api/catalog":
            data = catalog()
            data["hosting"] = {"mode": getattr(self.server, "mode", "local")}
            return self.respond(200, data)
        if path == "/api/health":
            return self.respond(200, {"status": "ok", "version": VERSION})
        if path == "/api/draft":
            draft = self.server.store.get(self.session)
            return self.respond(200, {"draft": draft, "outdated": bool(draft and draft.get("version") != VERSION)})
        files = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js",
                 "/styles.css": "styles.css", "/favicon.svg": "favicon.svg"}
        if path in files:
            file = STATIC / files[path]
            return self.respond(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        self.respond(404, {"error": "Not found."})

    def mutate(self, method):
        if not self.begin():
            return
        origin = self.headers.get("Origin")
        expected_origin = getattr(self, "scheme", "http") + "://" + self.headers["Host"]
        if self.headers.get("X-Passport-Agent") != "local" or (origin and origin != expected_origin):
            return self.respond(403, {"error": "Request must come from Passport Agent."})
        path = urlsplit(self.path).path
        if method == "DELETE" and path == "/api/draft":
            self.server.store.delete(self.session)
            return self.respond(200, {"deleted": True})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32768:
                raise ValueError("Request must be between 1 and 32768 bytes.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Use application/json.")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Expected an object.")
            route = data.get("route")
            if not isinstance(route, str):
                raise ValueError("Choose a route.")
            if method == "POST" and path == "/api/evaluate":
                result = evaluate(route, data.get("answers"))
                selected = validate_selection(route, data.get("selection"))
                result["selection"] = selected
                result["totals"] = totals(route, selected) if result.get("scorecard") else None
                return self.respond(200, result)
            if method == "PUT" and path == "/api/draft":
                answers = clean_answers(route, data.get("answers", {}))
                stage = data.get("stage", "questions")
                if stage not in {"questions", "review", "checklist"}:
                    raise ValueError("Invalid stage.")
                checked = data.get("checked", [])
                if not isinstance(checked, list) or any(not isinstance(x, str) for x in checked):
                    raise ValueError("Invalid document progress.")
                if len(checked) > 100:
                    raise ValueError("Too many document entries.")
                if stage in {"review", "checklist"}:
                    clean_answers(route, answers, complete=True)
                if stage == "checklist":
                    valid = {d["id"] for d in evaluate(route, answers)["documents"]}
                    checked = [x for x in checked if x in valid]
                else:
                    checked = []
                selected = validate_selection(route, data.get("selection"))
                updated = self.server.store.put(self.session, {
                    "route": route, "answers": answers, "checked": checked,
                    "stage": stage, "version": VERSION,
                    "selection": selected,
                })
                return self.respond(200, {"saved": True, "updated": updated})
            return self.respond(404, {"error": "Not found."})
        except (ValueError, TypeError, KeyError) as exc:
            return self.respond(400, {"error": str(exc)})
        except sqlite3.Error:
            return self.respond(500, {"error": "Could not save progress. Please try again."})

    def do_POST(self):
        self.mutate("POST")

    def do_PUT(self):
        self.mutate("PUT")

    def do_DELETE(self):
        self.mutate("DELETE")


def make_server(port=8000, database=None):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.store = Store(database or ROOT / "data" / "passport-agent.sqlite3")
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Passport Agent locally.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "passport-agent.sqlite3")
    args = parser.parse_args()
    app = make_server(args.port, args.database)
    print(f"Passport Agent is running at http://127.0.0.1:{app.server_port}", flush=True)
    print("Local access only. Press Ctrl+C to stop.", flush=True)
    try:
        app.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.server_close()
