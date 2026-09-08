"""Canonical local records; no providers, external effects or scheduled workers."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class Invalid(ValueError):
    pass


class Conflict(Invalid):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def bounded(value, name, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise Invalid(f"{name} must contain 1–{limit} characters.")
    return value.strip()


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "workspace.sqlite3"
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL, target TEXT NOT NULL, at TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _get(self, db, key, kind=None):
        row = db.execute("SELECT kind,body FROM records WHERE id=?", (key,)).fetchone()
        if row is None or (kind and row[0] != kind):
            raise Invalid("Record is unavailable.")
        return json.loads(row[1])

    def _save(self, db, kind, record):
        db.execute("INSERT OR REPLACE INTO records VALUES (?,?,?)",
                   (record["id"], kind, json.dumps(record)))

    def _event(self, db, kind, target):
        db.execute("INSERT INTO events(kind,target,at) VALUES (?,?,?)", (kind, target, now()))

    def _request(self, db, request_id, payload):
        bounded(request_id, "Request ID", 100)
        row = db.execute("SELECT fingerprint,result_id FROM requests WHERE id=?", (request_id,)).fetchone()
        if row:
            if row[0] != digest(payload):
                raise Conflict("Request ID already belongs to different input.")
            return self._get(db, row[1])
        return None

    def _remember(self, db, request_id, payload, result_id):
        db.execute("INSERT INTO requests VALUES (?,?,?)", (request_id, digest(payload), result_id))

    def capture(self, title, body, request_id):
        title, body = bounded(title, "Title", 120), bounded(body, "Source text", 12000)
        payload = {"operation": "capture", "title": title, "body": body}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = self._request(db, request_id, payload)
            if prior:
                return prior
            record = {"id": str(uuid.uuid4()), "title": title, "body": body,
                      "revision": 1, "observed_at": now(), "digest": digest({"title": title, "body": body})}
            self._save(db, "source", record)
            self._event(db, "source.captured", record["id"])
            self._remember(db, request_id, payload, record["id"])
            return record

    def draft(self, source_id, request_id):
        source_id = bounded(source_id, "Source ID", 100)
        payload = {"operation": "draft", "source_id": source_id}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = self._request(db, request_id, payload)
            if prior:
                return prior
            source = self._get(db, source_id, "source")
            content = {"title": source["title"], "objective": source["body"],
                       "source_id": source["id"], "source_digest": source["digest"],
                       "assumptions": ["This is a generic deterministic scaffold, not model analysis."],
                       "questions": ["Which concrete deliverable and acceptance checks fit this brief?"],
                       "next_actions": ["Confirm scope and expected deliverable.",
                                        "Inspect the selected source and identify missing evidence.",
                                        "Define and review the smallest useful next step."]}
            artifact = {"id": str(uuid.uuid4()), "revision": 1, "content": content,
                        "digest": digest(content), "created_at": now(), "review": "pending",
                        "validation": "passed", "project_id": None}
            run = {"id": str(uuid.uuid4()), "skill": "capture-to-plan", "skill_revision": "reference-v1",
                   "provider": "deterministic-reference", "status": "succeeded", "started_at": artifact["created_at"],
                   "finished_at": now(), "artifact_id": artifact["id"], "source_id": source_id,
                   "usage": None}
            artifact["run_id"] = run["id"]
            self._save(db, "artifact", artifact)
            self._save(db, "run", run)
            self._event(db, "draft.created", artifact["id"])
            self._remember(db, request_id, payload, artifact["id"])
            return artifact

    def review(self, artifact_id, expected_digest, decision):
        artifact_id = bounded(artifact_id, "Artifact ID", 100)
        expected_digest = bounded(expected_digest, "Digest", 64)
        if decision not in ("accepted", "rejected"):
            raise Invalid("Choose accepted or rejected.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            artifact = self._get(db, artifact_id, "artifact")
            if artifact["digest"] != expected_digest or digest(artifact["content"]) != expected_digest:
                raise Conflict("This draft changed. Inspect its current revision before deciding.")
            if artifact["review"] != "pending":
                if artifact["review"] == decision:
                    return artifact
                raise Conflict("This draft already has a different review decision.")
            source = self._get(db, artifact["content"]["source_id"], "source")
            if source["digest"] != artifact["content"]["source_digest"]:
                raise Conflict("The source changed. Create a new draft.")
            if artifact["validation"] != "passed":
                raise Conflict("The draft has not passed validation.")
            if decision == "accepted":
                project = {"id": str(uuid.uuid4()), "title": artifact["content"]["title"],
                           "objective": artifact["content"]["objective"], "artifact_id": artifact_id,
                           "source_id": source["id"], "created_at": now(),
                           "tasks": [{"title": t, "status": "proposed"} for t in artifact["content"]["next_actions"]]}
                self._save(db, "project", project)
                artifact["project_id"] = project["id"]
            artifact["review"] = decision
            artifact["reviewed_at"] = now()
            self._save(db, "artifact", artifact)
            self._event(db, "draft." + decision, artifact_id)
            return artifact

    def snapshot(self):
        with self.connect() as db:
            # A single read transaction gives projections a consistent snapshot.
            db.execute("BEGIN")
            result = {key: [] for key in ("sources", "artifacts", "runs", "projects")}
            for kind, body in db.execute("SELECT kind,body FROM records ORDER BY rowid DESC"):
                result[kind + "s"].append(json.loads(body))
            result["events"] = [{"sequence": seq, "kind": kind, "target": target, "at": at}
                                for seq, kind, target, at in db.execute(
                                    "SELECT sequence,kind,target,at FROM events ORDER BY sequence DESC LIMIT 100")]
            result["as_of"] = now()
            result["provider"] = "deterministic-reference"
            return result
