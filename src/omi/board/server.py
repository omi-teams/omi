"""Read-only HTTP handler: JSON from board.data and static files from board/web; GET only."""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import data

WEB = Path(__file__).parent / "web"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}
API = re.compile(r"/api/projects(?:/([^/]+)(?:/tasks/([^/]+))?)?")


class Handler(BaseHTTPRequestHandler):
    web = WEB

    def do_GET(self) -> None:
        path = unquote(urlsplit(self.path).path)
        match = API.fullmatch(path)
        if match:
            name, id = match.groups()
            try:
                body = data.projects() if name is None else data.project(name) if id is None else data.task(name, id)
            except (ValueError, FileNotFoundError):
                return self.send(404, "text/plain; charset=utf-8", b"not found")
            return self.send(200, "application/json", json.dumps(body).encode("utf-8"))
        parts = path.lstrip("/").split("/") if path != "/" else ["index.html"]
        if any(p in ("", ".", "..") or "\\" in p or "\0" in p or ":" in p for p in parts):
            return self.send(404, "text/plain; charset=utf-8", b"not found")
        file = (self.web / Path(*parts)).resolve()
        if not file.is_relative_to(self.web.resolve()) or not file.is_file():
            return self.send(404, "text/plain; charset=utf-8", b"not found")
        self.send(200, TYPES.get(file.suffix, "application/octet-stream"), file.read_bytes())

    def send(self, code: int, kind: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def refuse(self) -> None:
        self.send_response(405)
        self.send_header("Allow", "GET")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = refuse

    def log_message(self, *args) -> None:
        pass


def make_server(port: int, web: Path = WEB) -> ThreadingHTTPServer:
    """Bind 127.0.0.1 only; port 0 picks a free port."""
    return ThreadingHTTPServer(("127.0.0.1", port), type("BoardHandler", (Handler,), {"web": Path(web)}))
