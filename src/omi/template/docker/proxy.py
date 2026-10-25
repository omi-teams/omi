"""Egress allowlist proxy for omi workers: HTTP CONNECT only, never terminates TLS, never reads or logs headers.
Usage: python3 proxy.py <allow>...   (entries: host, *.suffix, host:port; a bare host means port 443)"""
import re
import select
import socket
import socketserver
import sys

PORT = 3128
ALLOW = []


def allowed(host, port, allow):
    host = host.lower().rstrip(".")
    for e in allow:
        e = e.lower()
        name, _, p = e.partition(":")
        if int(p or 443) != port:
            continue
        if name == host or (name.startswith("*.") and host.endswith(name[1:]) and len(host) > len(name) - 1):
            return True
    return False


def reply(sock, code, reason):
    body = reason + "\n"
    sock.sendall(f"HTTP/1.1 {code} {reason}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n{body}".encode())


def pipe(a, b):
    socks = [a, b]
    while True:
        r, _, _ = select.select(socks, [], [], 300)
        if not r:
            return
        for s in r:
            data = s.recv(65536)
            if not data:
                return
            (b if s is a else a).sendall(data)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        c = self.request
        c.settimeout(30)
        buf = b""
        while b"\r\n\r\n" not in buf and len(buf) < 65536:
            chunk = c.recv(4096)
            if not chunk:
                return
            buf += chunk
        parts = buf.split(b"\r\n", 1)[0].decode("latin-1").split()
        if len(parts) < 2 or parts[0].upper() != "CONNECT":
            return reply(c, 405, "omi proxy: CONNECT only")
        host, _, port = parts[1].rpartition(":")
        if not re.fullmatch(r"[A-Za-z0-9.-]+", host) or not port.isdigit():
            return reply(c, 400, "omi proxy: bad CONNECT target")
        port = int(port)
        if not allowed(host, port, ALLOW):
            print(f"BLOCKED {host}:{port}", flush=True)
            return reply(c, 403, f'omi blocked {host}: add it to "network_allow" in .omi/config.json')
        try:
            up = socket.create_connection((host, port), 15)
        except OSError:
            return reply(c, 502, f"omi proxy: cannot reach {host}:{port}")
        with up:
            c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            c.settimeout(None)
            try:
                pipe(c, up)
            except OSError:
                pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    ALLOW[:] = sys.argv[1:]
    with Server(("0.0.0.0", PORT), Handler) as srv:
        print("omi-proxy ready", flush=True)
        srv.serve_forever()
