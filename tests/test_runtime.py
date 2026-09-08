import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from reference.core import Store, Conflict, Invalid
from reference import jobs, layout, memory, recovery
from reference.cli import import_file
from reference.providers import configs, diagnostics
from reference.runner import run_once


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "data")
        self.source = self.store.capture(
            "Evidence intake",
            "Compare two mechanisms. Record uncertainties before choosing.",
            "capture",
        )

    def job(self, key="one"):
        return jobs.enqueue(self.store, self.source["id"], key)

    def test_real_child_worker_review_and_memory(self):
        job = self.job()
        result = run_once(self.store)
        self.assertEqual(result["status"], "succeeded", result)
        a = self.store.snapshot()["artifacts"][0]
        self.assertEqual(a["provider"], "local")
        self.store.review(a["id"], a["digest"], "accepted")
        found = memory.entries(self.store, "mechanisms")
        self.assertEqual({x["kind"] for x in found}, {"source", "decision"})
        self.assertEqual(
            jobs.enqueue(self.store, self.source["id"], "one")["id"], job["id"]
        )
        self.assertIsNone(run_once(self.store))
        self.assertEqual(len(self.store.snapshot()["projects"]), 1)

    def test_source_changes_invalidate_memory_and_active_result(self):
        self.job()
        job, source, config = jobs.claim(self.store)
        self.store.update_source(source["id"], 1, "Changed", "New evidence")
        result = jobs.finish(self.store, job, plan=Store.local_plan(source))
        self.assertEqual(result["status"], "failed")
        a = self.store.draft(source["id"], "manual")
        self.store.review(a["id"], a["digest"], "accepted")
        self.store.update_source(source["id"], 2, "Changed again", "Third revision")
        self.assertEqual(
            next(x for x in memory.entries(self.store) if x["kind"] == "decision")[
                "status"
            ],
            "stale",
        )
        with self.assertRaises(Conflict):
            self.store.update_source(source["id"], 1, "Oops", "Stale edit")

    def test_single_claim_fencing_and_cancellation(self):
        j = self.job()
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(lambda _: jobs.claim(self.store), range(2)))
        self.assertEqual(sum(x is not None for x in claims), 1)
        job, source, _ = next(x for x in claims if x)
        jobs.cancel(self.store, j["id"])
        result = jobs.finish(self.store, job, plan=Store.local_plan(source))
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(self.store.snapshot()["artifacts"], [])
        with self.assertRaises(Conflict):
            jobs.finish(self.store, job, plan=Store.local_plan(source))

    def test_queued_cancel_and_lost_worker(self):
        j = self.job()
        jobs.cancel(self.store, j["id"])
        self.assertIsNone(run_once(self.store))
        self.job("second")
        job, _, _ = jobs.claim(self.store)
        with self.store.connect() as db:
            job["deadline"] = "2020-01-01T00:00:00+00:00"
            jobs.save(db, job)
        self.assertIsNone(jobs.claim(self.store))
        self.assertEqual(jobs.snapshot(self.store)[0]["status"], "interrupted")

    def test_routine_due_missed_window_overlap_and_pause(self):
        r = jobs.routine_create(
            self.store, self.source["id"], 60, "2026-01-01T00:00:00+00:00"
        )
        self.assertEqual(jobs.tick(self.store, "2026-01-01T00:05:00+00:00"), [])
        r = jobs.routine_enable(self.store, r["id"], 1, True)
        self.assertEqual(len(jobs.tick(self.store, "2026-01-01T00:05:00+00:00")), 1)
        self.assertEqual(jobs.tick(self.store, "2026-01-01T00:08:00+00:00"), [])
        run_once(self.store)
        self.assertEqual(len(jobs.tick(self.store, "2026-01-01T00:08:00+00:00")), 1)
        jobs.routine_enable(self.store, r["id"], r["revision"], False)
        self.assertIsNone(run_once(self.store))
        self.assertEqual(jobs.tick(self.store, "2027-01-01T00:00:00+00:00"), [])
        with self.assertRaises(Invalid):
            jobs.routine_create(self.store, self.source["id"], 60, "2026-01-01")

    def test_layout_cas_registry_and_persistence(self):
        old = layout.read_layout(self.store)
        new = json.loads(json.dumps(old))
        new["widgets"][0].update(visible=False, collapsed=True, density="compact")
        saved = layout.save_layout(self.store, new)
        self.assertEqual(saved, layout.read_layout(Store(self.store.directory)))
        with self.assertRaises(Conflict):
            layout.save_layout(self.store, old)
        saved["widgets"].append(saved["widgets"][0])
        with self.assertRaises(Invalid):
            layout.save_layout(self.store, saved)
        self.assertEqual(len(self.store.snapshot()["sources"]), 1)

    def test_import_deduplicates_and_excludes_symlinks(self):
        p = self.root / "selected.md"
        p.write_text("A specifically selected local source.")
        self.assertEqual(
            import_file(self.store, p)["id"], import_file(self.store, p)["id"]
        )
        link = self.root / "link.md"
        link.symlink_to(p)
        with self.assertRaises(Invalid):
            import_file(self.store, link)

    def test_recovery_checksums_no_overwrite_and_pause(self):
        self.job()
        r = jobs.routine_create(
            self.store, self.source["id"], 60, "2026-01-01T00:00:00Z"
        )
        jobs.routine_enable(self.store, r["id"], 1, True)
        destination = self.root / "backup"
        recovery.backup(self.store, destination)
        recovery.restore(destination, self.root / "restored")
        restored = Store(self.root / "restored")
        self.assertFalse(jobs.routines(restored)[0]["enabled"])
        self.assertEqual(jobs.snapshot(restored)[0]["status"], "interrupted")
        self.assertEqual(
            restored.snapshot()["sources"], self.store.snapshot()["sources"]
        )
        with self.assertRaises(ValueError):
            recovery.restore(destination, self.root / "restored")
        with open(destination / "workspace.sqlite3", "ab") as f:
            f.write(b"tamper")
        with self.assertRaises(ValueError):
            recovery.restore(destination, self.root / "bad")
        self.assertFalse((self.root / "bad").exists())

    def test_migration_and_missing_database_fail_closed(self):
        old = self.root / "v1"
        old.mkdir()
        db = sqlite3.connect(old / "workspace.sqlite3")
        db.executescript(
            "CREATE TABLE records(id TEXT PRIMARY KEY,kind TEXT,body TEXT);CREATE TABLE requests(id TEXT PRIMARY KEY,fingerprint TEXT,result_id TEXT);CREATE TABLE events(sequence INTEGER PRIMARY KEY,kind TEXT,target TEXT,at TEXT);"
        )
        db.close()
        upgraded = Store(old)
        self.assertTrue((old / "workspace.sqlite3.before-v2.bak").exists())
        with upgraded.connect() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
        upgraded.path.rename(old / "saved.sqlite3")
        with self.assertRaises(Invalid):
            Store(old)

    def test_future_schema_and_unknown_db_not_modified(self):
        p = self.root / "future"
        p.mkdir()
        db = sqlite3.connect(p / "workspace.sqlite3")
        db.execute("PRAGMA user_version=99")
        db.close()
        with self.assertRaises(ValueError):
            Store(p)
        p = self.root / "foreign"
        p.mkdir()
        db = sqlite3.connect(p / "workspace.sqlite3")
        db.execute("CREATE TABLE unrelated (id INT)")
        db.close()
        with self.assertRaises(ValueError):
            Store(p)

    def test_provider_doctor_has_no_execution_or_secret_values(self):
        c = {
            "version": 1,
            "instances": [
                {
                    "id": "test",
                    "transport": "openai-chat",
                    "enabled": True,
                    "timeout_seconds": 2,
                    "base_url": "https://example.com/v1",
                    "model": "test",
                    "key_env": "FIXTURE_API_KEY",
                }
            ],
        }
        (self.store.directory / "providers.json").write_text(json.dumps(c))
        with patch.dict(os.environ, {"FIXTURE_API_KEY": "private-fixture-value"}):
            d = diagnostics(self.store)
        self.assertNotIn("private-fixture-value", json.dumps(d))
        self.assertEqual(d["instances"][1]["status"], "configured-unverified")
        c["instances"][0]["key"] = "not-allowed"
        (self.store.directory / "providers.json").write_text(json.dumps(c))
        with self.assertRaises(Invalid):
            configs(self.store)

    def test_real_configured_endpoint_through_job_runner(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer

        source = self.source
        received = []

        class Peer(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append(data)
                plan = Store.local_plan(source)
                plan["title"] = "Endpoint-produced fixture"
                body = {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": json.dumps(plan)},
                        }
                    ]
                }
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

        server = HTTPServer(("127.0.0.1", 0), Peer)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            c = {
                "version": 1,
                "instances": [
                    {
                        "id": "fixture-api",
                        "transport": "openai-chat",
                        "enabled": True,
                        "timeout_seconds": 5,
                        "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                        "model": "fixture",
                        "key_env": "FIXTURE_API_KEY",
                        "allow_loopback_http": True,
                    }
                ],
            }
            (self.store.directory / "providers.json").write_text(json.dumps(c))
            jobs.enqueue(self.store, source["id"], "api-job", "fixture-api")
            with patch.dict(os.environ, {"FIXTURE_API_KEY": "fixture-only"}):
                result = run_once(self.store)
            self.assertEqual(result["status"], "succeeded", result)
            self.assertEqual(
                self.store.snapshot()["artifacts"][0]["content"]["title"],
                "Endpoint-produced fixture",
            )
            self.assertIn(source["body"], received[0]["messages"][0]["content"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_configured_acp_full_job_path(self):
        import sys

        config = {
            "version": 1,
            "instances": [
                {
                    "id": "fixture-acp",
                    "transport": "acp",
                    "enabled": True,
                    "timeout_seconds": 5,
                    "command": [
                        sys.executable,
                        str(Path(__file__).with_name("fake_plan_acp.py").resolve()),
                    ],
                    "env_refs": {},
                    "scope_reviewed": True,
                    "auth_owned_by_user": True,
                }
            ],
        }
        (self.store.directory / "providers.json").write_text(json.dumps(config))
        jobs.enqueue(self.store, self.source["id"], "acp-job", "fixture-acp")
        result = run_once(self.store)
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual(
            self.store.snapshot()["artifacts"][0]["content"]["title"],
            "ACP fixture plan",
        )

    def test_wall_timeout_and_running_cancel(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        started = threading.Event()

        class Slow(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                started.set()
                time.sleep(2)
                try:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"{}")
                except (BrokenPipeError, ConnectionResetError):
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Slow)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            config = {
                "version": 1,
                "instances": [
                    {
                        "id": "slow",
                        "transport": "openai-chat",
                        "enabled": True,
                        "timeout_seconds": 1,
                        "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                        "model": "fixture",
                        "key_env": "FIXTURE_API_KEY",
                        "allow_loopback_http": True,
                    }
                ],
            }
            path = self.store.directory / "providers.json"
            path.write_text(json.dumps(config))
            jobs.enqueue(self.store, self.source["id"], "slow-one", "slow")
            with patch.dict(os.environ, {"FIXTURE_API_KEY": "fixture"}):
                result = run_once(self.store)
            self.assertEqual(result["status"], "failed")
            config["instances"][0]["timeout_seconds"] = 5
            path.write_text(json.dumps(config))
            job = jobs.enqueue(self.store, self.source["id"], "slow-two", "slow")
            started.clear()
            with (
                patch.dict(os.environ, {"FIXTURE_API_KEY": "fixture"}),
                ThreadPoolExecutor(max_workers=1) as pool,
            ):
                future = pool.submit(run_once, self.store)
                self.assertTrue(started.wait(3))
                jobs.cancel(self.store, job["id"])
                result = future.result(timeout=8)
            self.assertEqual(result["status"], "cancelled")
            self.assertEqual(self.store.snapshot()["artifacts"], [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_explicit_job_does_not_consume_unrelated_queue(self):
        first = self.job("first")
        second = self.job("second")
        result = run_once(self.store, job_id=second["id"])
        self.assertEqual(result["id"], second["id"])
        with self.store.connect() as db:
            self.assertEqual(jobs.read(db, first["id"])["status"], "queued")
