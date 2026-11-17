import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from server import Handler, Store
from tests.test_rules import answers


class PersistenceTests(unittest.TestCase):
    def test_saved_data_survives_reopen_and_is_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite3"
            Store(path).put("a", {"route": "fbr", "answers": {"adult": "yes"}})
            reopened = Store(path)
            self.assertEqual(reopened.get("a")["answers"], {"adult": "yes"})
            self.assertIsNone(reopened.get("b"))
            reopened.delete("a")
            self.assertIsNone(reopened.get("a"))


class APITests(unittest.TestCase):
    """Exercise the real HTTP handler without opening a listening socket."""
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.server = SimpleNamespace(
            server_port=8000,
            store=Store(Path(cls.directory.name) / "test.sqlite3"),
        )

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def request(self, method, path, payload=None, cookie=None, headers=None):
        h = {"Host": "127.0.0.1:8000", "Content-Type": "application/json", "X-Passport-Agent": "local"}
        if cookie:
            h["Cookie"] = cookie
        if headers:
            h.update(headers)
        body = b"" if payload is None else json.dumps(payload).encode()
        h["Content-Length"] = str(len(body))
        request = f"{method} {path} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in h.items()) + "\r\n"

        class MemorySocket:
            def __init__(self):
                self.output = io.BytesIO()

            def makefile(self, mode, buffering=None):
                return io.BytesIO(request.encode() + body)

            def sendall(self, data):
                self.output.write(data)

        connection = MemorySocket()
        Handler(connection, ("127.0.0.1", 12345), self.server)
        head, response_body = connection.output.getvalue().split(b"\r\n\r\n", 1)
        lines = head.decode().split("\r\n")
        status = int(lines[0].split()[1])
        response_headers = dict(line.split(": ", 1) for line in lines[1:])
        return status, response_headers, response_body

    def test_static_assets_and_source_catalog(self):
        for path in ["/", "/app.js", "/styles.css", "/favicon.svg", "/api/health", "/api/catalog"]:
            status, headers, body = self.request("GET", path)
            self.assertEqual(status, 200, path)
            self.assertTrue(body)
            self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(self.request("GET", "/../server.py")[0], 404)
        self.assertEqual(self.request("GET", "/data/passport-agent.sqlite3")[0], 404)

    def test_checklist_generation_rejects_invalid_answers(self):
        status, _, body = self.request("POST", "/api/evaluate", {"route": "fbr", "answers": answers("fbr")})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["documents"])
        self.assertEqual(self.request("POST", "/api/evaluate", {"route": "fbr", "answers": {}})[0], 400)

    def test_save_resume_delete_and_session_isolation(self):
        _, headers, _ = self.request("GET", "/api/draft")
        cookie = headers["Set-Cookie"].split(";")[0]
        payload = {"route": "fbr", "answers": answers("fbr"), "stage": "checklist", "checked": ["photos", "bogus"]}
        self.assertEqual(self.request("PUT", "/api/draft", payload, cookie)[0], 200)
        saved = json.loads(self.request("GET", "/api/draft", cookie=cookie)[2])
        self.assertEqual(saved["draft"]["checked"], ["photos"])
        self.assertFalse(saved["outdated"])
        isolated = json.loads(self.request("GET", "/api/draft")[2])
        self.assertIsNone(isolated["draft"])
        self.assertEqual(self.request("DELETE", "/api/draft", cookie=cookie)[0], 200)
        self.assertIsNone(json.loads(self.request("GET", "/api/draft", cookie=cookie)[2])["draft"])

    def test_cross_origin_and_foreign_host_requests_rejected(self):
        payload = {"route": "fbr", "answers": answers("fbr")}
        self.assertEqual(self.request("POST", "/api/evaluate", payload, headers={"Origin": "https://other.example"})[0], 403)
        self.assertEqual(self.request("POST", "/api/evaluate", payload, headers={"X-Passport-Agent": ""})[0], 403)
        self.assertEqual(self.request("GET", "/", headers={"Host": "other.example"})[0], 403)

    def test_incomplete_draft_allowed_but_not_completed_stage(self):
        payload = {"route": "fbr", "answers": {"adult": "yes"}, "stage": "questions"}
        self.assertEqual(self.request("PUT", "/api/draft", payload)[0], 200)
        payload["stage"] = "checklist"
        self.assertEqual(self.request("PUT", "/api/draft", payload)[0], 400)

    def test_points_selection_persists_and_server_recalculates_totals(self):
        _, headers, _ = self.request("GET", "/api/draft")
        cookie = headers["Set-Cookie"].split(";")[0]
        payload = {"route": "spouse", "answers": answers("spouse"), "stage": "checklist",
                   "selection": {"identity": ["passport_recent", "irp_identity"],
                                 "years": [{"a": "bank", "b": "rent"}] * 3}}
        self.assertEqual(self.request("PUT", "/api/draft", payload, cookie)[0], 200)
        saved = json.loads(self.request("GET", "/api/draft", cookie=cookie)[2])["draft"]
        self.assertEqual(saved["selection"], payload["selection"])
        status, _, body = self.request("POST", "/api/evaluate", payload)
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result["totals"]["identity"], 150)
        self.assertTrue(result["totals"]["residence_met"])
        payload["selection"]["identity"] = ["passport_valid", "passport_old", "irp_identity"]
        self.assertEqual(self.request("PUT", "/api/draft", payload, cookie)[0], 200)
        restored = json.loads(self.request("GET", "/api/draft", cookie=cookie)[2])["draft"]
        self.assertEqual(restored["selection"]["identity"], payload["selection"]["identity"])
        scored = json.loads(self.request("POST", "/api/evaluate", restored)[2])
        self.assertEqual(scored["totals"]["identity"], 275)


if __name__ == "__main__":
    unittest.main()
