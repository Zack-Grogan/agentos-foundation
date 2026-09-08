"""Durable single-owner jobs and interval routines; no blind external retries."""

import json
import uuid
from datetime import datetime, timezone, timedelta
from .core import Invalid, Conflict, bounded, digest, now
from .providers import selected

TERMINAL = {"succeeded", "failed", "cancelled", "interrupted"}


def utc(value):
    if not isinstance(value, str):
        raise Invalid("An ISO timestamp with timezone is required.")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Invalid("Invalid timestamp.") from None
    if d.tzinfo is None:
        raise Invalid("An explicit timezone is required.")
    return d.astimezone(timezone.utc)


def read(db, job_id):
    row = db.execute("SELECT body FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise Invalid("Job unavailable.")
    return json.loads(row[0])


def save(db, job):
    db.execute(
        "UPDATE jobs SET status=?,body=? WHERE id=?",
        (job["status"], json.dumps(job), job["id"]),
    )


def enqueue(
    store, source_id, request_id, provider_id="local", *, routine_id=None, db=None
):
    bounded(source_id, "Source ID", 100)
    bounded(request_id, "Request ID", 160)
    config = selected(store, provider_id)
    payload = {
        "source_id": source_id,
        "provider_id": provider_id,
        "routine_id": routine_id,
    }

    def insert(db):
        old = db.execute(
            "SELECT fingerprint,body FROM jobs WHERE request_id=?", (request_id,)
        ).fetchone()
        if old:
            if old[0] != digest(payload):
                raise Conflict("Request ID belongs to different job input.")
            return json.loads(old[1])
        source = store._get(db, source_id, "source")
        job = {
            "id": str(uuid.uuid4()),
            **payload,
            "request_id": request_id,
            "source_digest": source["digest"],
            "config_digest": digest(config),
            "status": "queued",
            "created_at": now(),
            "started_at": None,
            "finished_at": None,
            "deadline": None,
            "token": None,
            "cancel_requested": False,
            "artifact_id": None,
            "error": None,
            "attempts": 0,
        }
        db.execute(
            "INSERT INTO jobs VALUES (?,?,?,?,?)",
            (job["id"], request_id, digest(payload), "queued", json.dumps(job)),
        )
        store._event(db, "job.queued", job["id"])
        return job

    if db is not None:
        return insert(db)
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        return insert(db)


def claim(store, job_id=None):
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        instant = utc(now())
        for row in db.execute(
            "SELECT body FROM jobs WHERE status='running'"
        ).fetchall():
            job = json.loads(row[0])
            if instant <= utc(job["deadline"]) + timedelta(seconds=10):
                return None
            job.update(
                status="interrupted",
                error="worker_lost; retry requires a new request",
                finished_at=now(),
                token=None,
            )
            save(db, job)
            store._event(db, "job.interrupted", job["id"])
        rows = db.execute(
            "SELECT body FROM jobs WHERE status='queued'"
            + (" AND id=?" if job_id else "")
            + " ORDER BY rowid LIMIT 1",
            (job_id,) if job_id else (),
        ).fetchall()
        if not rows:
            return None
        job = json.loads(rows[0][0])
        try:
            config = selected(store, job["provider_id"])
            if digest(config) != job["config_digest"]:
                raise Invalid("Provider configuration changed; create a new job.")
            source = store._get(db, job["source_id"], "source")
            if source["digest"] != job["source_digest"]:
                raise Invalid("Source changed; create a new job.")
        except (Invalid, ValueError) as exc:
            job.update(status="failed", error=str(exc), finished_at=now())
            save(db, job)
            store._event(db, "job.failed", job["id"])
            return None
        job.update(
            status="running",
            token=str(uuid.uuid4()),
            attempts=1,
            started_at=now(),
            deadline=(
                instant + timedelta(seconds=config["timeout_seconds"])
            ).isoformat(),
        )
        save(db, job)
        store._event(db, "job.started", job["id"])
        return job, source, config


def finish(store, job, *, plan=None, usage=None, error=None, interrupted=False):
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = read(db, job["id"])
        if current["status"] != "running" or current["token"] != job["token"]:
            raise Conflict("Worker no longer owns this job.")
        current.update(finished_at=now(), token=None)
        if interrupted:
            current.update(status="interrupted", error="worker_shutdown")
        elif current["cancel_requested"]:
            current.update(status="cancelled", error=None)
        elif error:
            current.update(status="failed", error=bounded(error, "Error", 1000))
        elif utc(now()) > utc(job["deadline"]):
            current.update(
                status="failed",
                error="deadline_exceeded; provider outcome/usage may be unknown",
            )
        else:
            try:
                source = store._get(db, job["source_id"], "source")
                if (
                    source["digest"] != job["source_digest"]
                    or digest(selected(store, job["provider_id"]))
                    != job["config_digest"]
                ):
                    raise Invalid("Inputs or provider policy changed during the run.")
                artifact = store._artifact(
                    db, source, plan, job["provider_id"], job_id=job["id"], usage=usage
                )
                current.update(status="succeeded", artifact_id=artifact["id"])
            except (Invalid, ValueError) as exc:
                current.update(status="failed", error=str(exc))
        save(db, current)
        store._event(db, "job." + current["status"], job["id"])
        return current


def cancel(store, job_id):
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        job = read(db, job_id)
        if job["status"] not in TERMINAL:
            job["cancel_requested"] = True
            if job["status"] == "queued":
                job.update(status="cancelled", finished_at=now())
            save(db, job)
            store._event(db, "job.cancel_requested", job_id)
        return job


def snapshot(store):
    with store.connect() as db:
        return [
            {k: v for k, v in json.loads(row[0]).items() if k != "token"}
            for row in db.execute("SELECT body FROM jobs ORDER BY rowid DESC LIMIT 100")
        ]


def routine_create(
    store, source_id, interval_seconds, next_due_at, provider_id="local"
):
    if type(interval_seconds) is not int or not 60 <= interval_seconds <= 31536000:
        raise Invalid("Interval must be 60 seconds to 365 days.")
    due = utc(next_due_at)
    selected(store, provider_id)
    with store.connect() as db:
        store._get(db, source_id, "source")
        routine = {
            "id": str(uuid.uuid4()),
            "source_id": source_id,
            "provider_id": provider_id,
            "interval_seconds": interval_seconds,
            "next_due_at": due.isoformat(),
            "enabled": False,
            "revision": 1,
            "missed_run_policy": "latest",
            "last_error": None,
        }
        db.execute(
            "INSERT INTO routines VALUES (?,?)", (routine["id"], json.dumps(routine))
        )
        return routine


def routine_enable(store, routine_id, revision, enabled):
    if type(enabled) is not bool or type(revision) is not int:
        raise Invalid("Expected enabled boolean and integer revision.")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT body FROM routines WHERE id=?", (routine_id,)
        ).fetchone()
        if not row:
            raise Invalid("Routine unavailable.")
        routine = json.loads(row[0])
        if routine["revision"] != revision:
            raise Conflict("Routine changed; refresh first.")
        routine.update(enabled=enabled, revision=revision + 1)
        db.execute(
            "UPDATE routines SET body=? WHERE id=?", (json.dumps(routine), routine_id)
        )
        if not enabled:
            for item in db.execute(
                "SELECT body FROM jobs WHERE status='queued'"
            ).fetchall():
                job = json.loads(item[0])
                if job["routine_id"] == routine_id:
                    job.update(status="cancelled", finished_at=now())
                    save(db, job)
        return routine


def routines(store):
    with store.connect() as db:
        return [
            json.loads(r[0])
            for r in db.execute("SELECT body FROM routines ORDER BY rowid DESC")
        ]


def tick(store, at=None):
    instant = utc(at or now())
    created = []
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        for row in db.execute("SELECT body FROM routines").fetchall():
            r = json.loads(row[0])
            due = utc(r["next_due_at"])
            if not r["enabled"] or due > instant:
                continue
            # Do not build a backlog while any occurrence for this routine is active.
            active = any(
                json.loads(x[0])["routine_id"] == r["id"]
                for x in db.execute(
                    "SELECT body FROM jobs WHERE status IN ('queued','running')"
                )
            )
            if active:
                continue
            latest = due + timedelta(
                seconds=int((instant - due).total_seconds() // r["interval_seconds"])
                * r["interval_seconds"]
            )
            try:
                j = enqueue(
                    store,
                    r["source_id"],
                    f"routine:{r['id']}:{latest.isoformat()}",
                    r["provider_id"],
                    routine_id=r["id"],
                    db=db,
                )
                created.append(j)
                r.update(
                    last_error=None,
                    next_due_at=(
                        latest + timedelta(seconds=r["interval_seconds"])
                    ).isoformat(),
                )
            except (Invalid, ValueError) as exc:
                r.update(enabled=False, last_error=str(exc), revision=r["revision"] + 1)
            db.execute(
                "UPDATE routines SET body=? WHERE id=?", (json.dumps(r), r["id"])
            )
    return created
