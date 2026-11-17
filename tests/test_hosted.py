import io
import json
from pathlib import Path
import tempfile
import unittest
from wsgiref.validate import validator

from hosted import create_application
from tests.test_rules import answers


class HostedTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "hosted.sqlite3"
        self.app = validator(create_application({"example.pythonanywhere.com"}, self.database))

    def request(self, method="GET", path="/", payload=None, cookie=None, origin=None, host="example.pythonanywhere.com"):
        raw = json.dumps(payload).encode() if payload is not None else b""
        environ = {"REQUEST_METHOD": method, "SCRIPT_NAME": "", "PATH_INFO": path,
                   "QUERY_STRING": "", "SERVER_NAME": host, "SERVER_PORT": "443",
                   "SERVER_PROTOCOL": "HTTP/1.1", "HTTP_HOST": host,
                   "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(raw)),
                   "HTTP_X_PASSPORT_AGENT": "local", "wsgi.version": (1, 0),
                   "wsgi.url_scheme": "https", "wsgi.input": io.BytesIO(raw),
                   "wsgi.errors": io.StringIO(), "wsgi.multithread": False,
                   "wsgi.multiprocess": False, "wsgi.run_once": False}
        if cookie:
            environ["HTTP_COOKIE"] = cookie
        if origin:
            environ["HTTP_ORIGIN"] = origin
        captured = {}

        def start_response(status, headers, exc_info=None):
            captured.update(status=int(status.split()[0]), headers=dict(headers))

        iterable = self.app(environ, start_response)
        try:
            captured["body"] = b"".join(iterable)
        finally:
            iterable.close()
        return captured

    def test_wsgi_serves_all_assets_and_hosted_catalog(self):
        for path in ["/", "/app.js", "/styles.css", "/favicon.svg", "/api/health"]:
            self.assertEqual(self.request(path=path)["status"], 200)
        result = self.request(path="/api/catalog")
        self.assertEqual(json.loads(result["body"])["hosting"]["mode"], "hosted")
        self.assertIn("; Secure", result["headers"]["Set-Cookie"])

    def test_https_generate_save_resume_delete(self):
        first = self.request(path="/api/draft")
        cookie = first["headers"]["Set-Cookie"].split(";")[0]
        payload = {"route": "residence", "answers": answers("residence"), "stage": "checklist",
                   "checked": ["birth"], "selection": {"identity": ["passport_valid", "psc"]}}
        generated = self.request("POST", "/api/evaluate", payload, cookie, "https://example.pythonanywhere.com")
        self.assertEqual(generated["status"], 200)
        self.assertEqual(json.loads(generated["body"])["totals"]["identity"], 175)
        self.assertEqual(self.request("PUT", "/api/draft", payload, cookie)["status"], 200)
        # A recreated WSGI application must read the same persisted journey.
        self.app = validator(create_application({"example.pythonanywhere.com"}, self.database))
        saved = json.loads(self.request(path="/api/draft", cookie=cookie)["body"])["draft"]
        self.assertEqual(saved["checked"], ["birth"])
        self.assertEqual(saved["selection"]["identity"], ["passport_valid", "psc"])
        self.assertIsNone(json.loads(self.request(path="/api/draft")["body"])["draft"])
        self.assertEqual(self.request("DELETE", "/api/draft", cookie=cookie)["status"], 200)
        self.assertIsNone(json.loads(self.request(path="/api/draft", cookie=cookie)["body"])["draft"])

    def test_host_origin_method_and_static_restrictions(self):
        self.assertEqual(self.request(host="other.example")["status"], 403)
        payload = {"route": "fbr", "answers": answers("fbr")}
        self.assertEqual(self.request("POST", "/api/evaluate", payload, origin="https://other.example")["status"], 403)
        self.assertEqual(self.request(path="/data/passport-agent.sqlite3")["status"], 404)
        self.assertEqual(self.request("PATCH")["status"], 405)
        self.assertEqual(self.request("POST", "/api/evaluate", {})["status"], 400)
