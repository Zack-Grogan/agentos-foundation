"""Single-user loopback reference server, deliberately not an internet deployment."""

import argparse
import hmac
import json
import secrets
import threading
from urllib.parse import urlsplit, parse_qs
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .core import Store, Invalid, Conflict
from . import jobs, layout, memory
from .providers import diagnostics
from .profile import profile
from .runner import run_once

ASSETS = {
    "/": ("index.html", "text/html"),
    "/app.js": ("app.js", "text/javascript"),
    "/style.css": ("style.css", "text/css"),
}


def make_server(data_dir, port=4321, *, run_jobs=True, run_routines=False):
    store = Store(data_dir)
    token = secrets.token_urlsafe(32)
    web = Path(__file__).parent / "web"
    current_profile = profile()
    stopping = threading.Event()

    class ManagedServer(HTTPServer):
        worker = None

        def service_actions(self):
            if run_routines:
                jobs.tick(store)
            if (
                run_jobs
                and not stopping.is_set()
                and (self.worker is None or not self.worker.is_alive())
            ):
                with store.connect() as db:
                    pending = db.execute(
                        "SELECT 1 FROM jobs WHERE status IN ('queued','running') LIMIT 1"
                    ).fetchone()
                if pending:
                    self.worker = threading.Thread(
                        target=run_once, args=(store, stopping), daemon=True
                    )
                    self.worker.start()

        def server_close(self):
            stopping.set()
            if self.worker:
                self.worker.join(8)
            super().server_close()

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
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            )
            if cookie:
                self.send_header(
                    "Set-Cookie",
                    f"agentos_session={token}; HttpOnly; SameSite=Strict; Path=/",
                )
            self.end_headers()
            self.wfile.write(data)

        def local(self):
            expected = f"127.0.0.1:{self.server.server_port}"
            return (
                self.headers.get("Host") == expected
                and not any(
                    k.lower() == "forwarded" or k.lower().startswith("x-forwarded-")
                    for k in self.headers
                )
                and self.headers.get("Sec-Fetch-Site", "none")
                in ("none", "same-origin")
            )

        def session(self):
            try:
                cookies = SimpleCookie(self.headers.get("Cookie", ""))
                supplied = cookies.get("agentos_session")
                return supplied is not None and hmac.compare_digest(
                    supplied.value, token
                )
            except Exception:
                return False

        def do_GET(self):
            if not self.local():
                return self.reply(
                    403, {"error": "Open the exact loopback address directly."}
                )
            if self.path in ASSETS:
                asset, mime = ASSETS[self.path]
                return self.reply(
                    200, (web / asset).read_bytes(), mime, cookie=self.path == "/"
                )
            if not self.session():
                return self.reply(
                    403, {"error": "Open the workspace to establish a local session."}
                )
            if self.path == "/api/state":
                value = store.snapshot()
                value.update(
                    jobs=jobs.snapshot(store),
                    routines=jobs.routines(store),
                    layout=layout.read_layout(store),
                    profile=current_profile,
                    providers=diagnostics(store)["instances"],
                    scheduler_active=run_routines,
                    workspace_id=json.loads(
                        (store.directory / "workspace-marker.json").read_text()
                    )["workspace_id"],
                )
                return self.reply(200, value)
            if urlsplit(self.path).path == "/api/skills":
                root = Path(__file__).resolve().parents[1] / ".agents" / "skills"
                if (
                    root.is_symlink()
                    or Path(__file__).resolve().parents[1] not in root.resolve().parents
                ):
                    return self.reply(
                        403,
                        {"error": "Project skill root must stay inside the project."},
                    )
                entries = []
                for path in sorted(root.glob("*/SKILL.md")):
                    if (
                        path.is_symlink()
                        or root.resolve() not in path.resolve().parents
                        or path.stat().st_size > 50000
                    ):
                        continue
                    text = path.read_text()
                    description = next(
                        (
                            line.removeprefix("description: ").strip()
                            for line in text.splitlines()
                            if line.startswith("description: ")
                        ),
                        "Project playbook",
                    )
                    entries.append(
                        {
                            "name": path.parent.name,
                            "description": description,
                            "text": text,
                        }
                    )
                requested = parse_qs(urlsplit(self.path).query).get("id", [None])[0]
                if requested is not None:
                    selected = next(
                        (e for e in entries if e["name"] == requested), None
                    )
                    return (
                        self.reply(200, selected)
                        if selected
                        else self.reply(404, {"error": "Unknown project skill."})
                    )
                return self.reply(
                    200, [{k: v for k, v in e.items() if k != "text"} for e in entries]
                )
            if urlsplit(self.path).path == "/api/memory":
                query = parse_qs(urlsplit(self.path).query).get("q", [""])[0][:200]
                return self.reply(200, memory.entries(store, query))
            if self.path == "/api/doctor":
                return self.reply(200, diagnostics(store))
            if self.path == "/api/session":
                return self.reply(200, {"csrf": token})
            return self.reply(404, {"error": "Not found."})

        def do_POST(self):
            expected = f"http://127.0.0.1:{self.server.server_port}"
            if (
                not self.local()
                or not self.session()
                or self.headers.get("Origin") != expected
                or not hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), token)
            ):
                return self.reply(
                    403, {"error": "Same-origin workspace session required."}
                )
            operations = {
                "/api/capture": (store.capture, {"title", "body", "request_id"}),
                "/api/draft": (store.draft, {"source_id", "request_id"}),
                "/api/review": (
                    store.review,
                    {"artifact_id", "expected_digest", "decision"},
                ),
                "/api/source/update": (
                    store.update_source,
                    {"source_id", "revision", "title", "body"},
                ),
                "/api/task": (
                    store.task_status,
                    {"project_id", "revision", "index", "status"},
                ),
                "/api/jobs": (
                    lambda **kw: jobs.enqueue(store, **kw),
                    {"source_id", "request_id", "provider_id"},
                ),
                "/api/jobs/cancel": (lambda **kw: jobs.cancel(store, **kw), {"job_id"}),
                "/api/layout": (
                    lambda **kw: layout.save_layout(store, **kw),
                    {"layout"},
                ),
                "/api/routines": (
                    lambda **kw: jobs.routine_create(store, **kw),
                    {"source_id", "interval_seconds", "next_due_at", "provider_id"},
                ),
                "/api/routines/enable": (
                    lambda **kw: jobs.routine_enable(store, **kw),
                    {"routine_id", "revision", "enabled"},
                ),
            }
            if self.path not in operations:
                return self.reply(404, {"error": "Unknown operation."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if (
                    not 0 < length <= 64000
                    or self.headers.get("Content-Type") != "application/json"
                ):
                    raise Invalid("Expected a bounded JSON request.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise Invalid("Expected a JSON object.")
                method, keys = operations[self.path]
                if set(data) != keys:
                    raise Invalid("Unexpected or missing fields.")
                value = method(**data)
                if isinstance(value, dict):
                    value.pop("token", None)
                return self.reply(200, value)
            except Conflict as exc:
                return self.reply(409, {"error": str(exc)})
            except (Invalid, ValueError, TypeError, UnicodeDecodeError) as exc:
                return self.reply(400, {"error": str(exc)})
            except Exception:
                return self.reply(
                    500,
                    {
                        "error": "Operation failed. Refresh recorded state before retrying."
                    },
                )

    return ManagedServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4321)
    parser.add_argument("--data-dir", type=Path, default=Path(".agentos"))
    parser.add_argument(
        "--routines",
        action="store_true",
        help="Tick explicitly enabled local interval routines while this server is running",
    )
    args = parser.parse_args()
    server = make_server(args.data_dir, args.port, run_routines=args.routines)
    print(f"AgentOS reference: http://127.0.0.1:{server.server_port}", flush=True)
    print(
        "Local planner by default. Configured providers run only when selected; routine ticking is opt-in.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
