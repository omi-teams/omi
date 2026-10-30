"""Board server: routes, static confinement, headers, GET-only, localhost bind."""
import http.client
import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401
from helpers import omi
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


def test_board_cli():
    def board(*args):
        with patch("omi.state.resolve.resolve") as resolve, patch("omi.board.server.make_server") as make, \
                patch("webbrowser.open") as opened:
            resolve.return_value.detached = True
            make.return_value.server_port = 8765
            with patch("omi.state.sync.pull") as pull:
                omi.app.cli.dispatch(["board", *args])
            return pull, make, opened

    pull, make, opened = board()
    assert make.call_args.args == (8765,) and pull.call_count == 1 and opened.call_count == 1
    pull, make, opened = board("--port", "9000", "--no-open")
    assert make.call_args.args == (9000,) and not opened.called
    for bad in (["--port"], ["--port", "x"], ["--bogus"], ["--port", "-1"]):
        try:
            board(*bad)
        except omi.state.resolve.StateError as exc:
            assert "usage: omi board" in str(exc)
        else:
            raise AssertionError(bad)
    for port, error in (("8765", OSError("in use")), ("99999", OverflowError("big"))):
        with patch("omi.state.resolve.resolve"), patch("omi.state.sync.pull"), \
                patch("omi.board.server.make_server", side_effect=error):
            try:
                omi.app.cli.dispatch(["board", "--port", port])
            except omi.state.resolve.StateError as exc:
                assert f"cannot bind 127.0.0.1:{port}" in str(exc)
            else:
                raise AssertionError(port)


def test_unreadable_task():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        httpd = server.make_server(0, Path(directory))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            with patch("omi.board.data.projects", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad")):
                status, res, _ = request(httpd.server_port, "GET", "/api/projects")
            assert status == 500 and res.getheader("Content-Security-Policy") == "default-src 'self'"
            with patch("omi.board.data.projects", side_effect=PermissionError("no")):
                assert request(httpd.server_port, "GET", "/api/projects")[0] == 500
        finally:
            httpd.shutdown()
            httpd.server_close()


def main():
    test_server()
    test_board_cli()
    test_unreadable_task()


if __name__ == "__main__":
    main()
