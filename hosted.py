"""WSGI adapter for PythonAnywhere; shares the local API and rules."""
from email.message import Message
from http import HTTPStatus
import json
from types import SimpleNamespace

from server import Handler, ROOT, Store, response_headers


class WSGIHandler(Handler):
    def __init__(self, environ, server):
        self.server = server
        self.scheme = environ.get("wsgi.url_scheme", "https")
        self.path = environ.get("PATH_INFO", "/")
        self.headers = Message()
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                self.headers[key[5:].replace("_", "-")] = value
        self.headers["Content-Type"] = environ.get("CONTENT_TYPE", "")
        self.headers["Content-Length"] = environ.get("CONTENT_LENGTH", "0") or "0"
        self.rfile = environ["wsgi.input"]
        self.result = None
        method = environ.get("REQUEST_METHOD", "GET")
        if method in {"GET", "POST", "PUT", "DELETE"}:
            getattr(self, "do_" + method)()
        else:
            self.respond(405, {"error": "Method not allowed."})

    def respond(self, status, payload, content_type="application/json; charset=utf-8"):
        body = json.dumps(payload).encode() if isinstance(payload, (dict, list)) else payload
        headers = [("Content-Type", content_type), ("Content-Length", str(len(body)))]
        headers.extend(response_headers(getattr(self, "new_cookie", None), self.scheme == "https"))
        if status == 405:
            headers.append(("Allow", "GET, POST, PUT, DELETE"))
        self.result = (f"{status} {HTTPStatus(status).phrase}", headers, body)


def create_application(allowed_hosts, database=None):
    hosts = set(allowed_hosts)
    if not hosts or any(not host or "/" in host for host in hosts):
        raise ValueError("Configure the website hostname without https:// or a path.")
    server = SimpleNamespace(allowed_hosts=hosts, server_port=443, mode="hosted",
                             store=Store(database or ROOT / "data" / "passport-agent.sqlite3"))

    def application(environ, start_response):
        status, headers, body = WSGIHandler(environ, server).result
        start_response(status, headers)
        return [body]

    return application
