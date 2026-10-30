"""Board server: routes, static confinement, headers, GET-only, localhost bind."""
import http.client
import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401
from omi.board import server
from test_board import fixture, write


def request(port, method, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(method, path)
    res = conn.getresponse()
    body = res.read()
    conn.close()
    return res.status, res, body


def test_server():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        home = Path(directory) / "state"
        web = Path(directory) / "web"
        fixture(home)
        write(web / "index.html", "<h1>board</h1>")
        write(web / "app.js", "1")
        write(Path(directory) / "secret.txt", "secret")
        os.environ["OMI_STATE"] = str(home)
        httpd = server.make_server(0, web)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        port = httpd.server_port
        try:
            assert httpd.server_address[0] == "127.0.0.1"
            status, res, body = request(port, "GET", "/api/projects")
            assert status == 200 and json.loads(body)[0]["name"] == "sample"
            assert res.getheader("Content-Type") == "application/json"
            assert res.getheader("X-Content-Type-Options") == "nosniff"
            assert res.getheader("Content-Security-Policy") == "default-src 'self'"
            assert json.loads(request(port, "GET", "/api/projects/sample")[2])["name"] == "sample"
            assert json.loads(request(port, "GET", "/api/projects/sample/tasks/TASK-002?x=1")[2])["id"] == "TASK-002"
            status, res, body = request(port, "GET", "/")
            assert status == 200 and body == b"<h1>board</h1>" and res.getheader("Content-Type").startswith("text/html")
            assert request(port, "GET", "/app.js")[1].getheader("Content-Type").startswith("text/javascript")
            for path in ("/api/projects/nope", "/api/projects/sample/tasks/TASK-999", "/api/projects/sample/tasks/..%2f..",
                         "/api/other", "/api/projects/sample/extra", "/missing.js", "/../secret.txt", "/..%2fsecret.txt",
                         "/%2e%2e/secret.txt", "/%2e%2e%2fsecret.txt", "//etc/passwd", "/etc/passwd/", "/%2fetc%2fpasswd",
                         "/..\\secret.txt", "/%00", "/app.js/", "/.", "/C:/Windows"):
                status, res, _ = request(port, "GET", path)
                assert status == 404, path
                assert res.getheader("X-Content-Type-Options") == "nosniff"
            for method in ("POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                status, res, _ = request(port, method, "/api/projects")
                assert status == 405 and res.getheader("Allow") == "GET", method
        finally:
            httpd.shutdown()
            httpd.server_close()


def main():
    test_server()


if __name__ == "__main__":
    main()
