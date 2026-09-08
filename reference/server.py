"""Single-user loopback reference server, deliberately not an internet deployment."""
import argparse
import hmac
import json
import secrets
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .core import Store, Invalid, Conflict

ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/style.css": ("style.css", "text/css")}


def make_server(data_dir, port=4321):
    store = Store(data_dir)
    token = secrets.token_urlsafe(32)
    web = Path(__file__).parent / "web"

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_):
            pass  # Do not log request bodies or local source content.

        def reply(self, status, value, content_type="application/json", cookie=False):
            data = value if isinstance(value, bytes) else json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            if cookie:
                self.send_header("Set-Cookie", f"agentos_session={token}; HttpOnly; SameSite=Strict; Path=/")
            self.end_headers()
            self.wfile.write(data)

        def local(self):
            expected = f"127.0.0.1:{self.server.server_port}"
            return (self.headers.get("Host") == expected
                    and not any(k.lower() == "forwarded" or k.lower().startswith("x-forwarded-") for k in self.headers)
                    and self.headers.get("Sec-Fetch-Site", "none") in ("none", "same-origin"))

        def session(self):
            try:
                cookies = SimpleCookie(self.headers.get("Cookie", ""))
                supplied = cookies.get("agentos_session")
                return supplied is not None and hmac.compare_digest(supplied.value, token)
            except Exception:
                return False

        def do_GET(self):
            if not self.local():
                return self.reply(403, {"error": "Open the exact loopback address directly."})
            if self.path in ASSETS:
                asset, mime = ASSETS[self.path]
                return self.reply(200, (web / asset).read_bytes(), mime, cookie=self.path == "/")
            if not self.session():
                return self.reply(403, {"error": "Open the workspace to establish a local session."})
            if self.path == "/api/state":
                return self.reply(200, store.snapshot())
            if self.path == "/api/session":
                return self.reply(200, {"csrf": token})
            return self.reply(404, {"error": "Not found."})

        def do_POST(self):
            expected = f"http://127.0.0.1:{self.server.server_port}"
            if (not self.local() or not self.session() or self.headers.get("Origin") != expected
                    or not hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), token)):
                return self.reply(403, {"error": "Same-origin workspace session required."})
            if self.path not in ("/api/capture", "/api/draft", "/api/review"):
                return self.reply(404, {"error": "Unknown operation."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 64000 or self.headers.get("Content-Type") != "application/json":
                    raise Invalid("Expected a bounded JSON request.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise Invalid("Expected a JSON object.")
                keys = {"/api/capture": {"title", "body", "request_id"},
                        "/api/draft": {"source_id", "request_id"},
                        "/api/review": {"artifact_id", "expected_digest", "decision"}}[self.path]
                if set(data) != keys:
                    raise Invalid("Unexpected or missing fields.")
                method = {"/api/capture": store.capture, "/api/draft": store.draft, "/api/review": store.review}[self.path]
                return self.reply(200, method(**data))
            except Conflict as exc:
                return self.reply(409, {"error": str(exc)})
            except (Invalid, ValueError, TypeError, UnicodeDecodeError) as exc:
                return self.reply(400, {"error": str(exc)})
            except Exception:
                return self.reply(500, {"error": "Operation failed. Refresh recorded state before retrying."})

    return HTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4321)
    parser.add_argument("--data-dir", type=Path, default=Path(".agentos"))
    args = parser.parse_args()
    server = make_server(args.data_dir, args.port)
    print(f"AgentOS reference: http://127.0.0.1:{server.server_port}", flush=True)
    print("Deterministic planner; no LLM, external actions or scheduled work.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
