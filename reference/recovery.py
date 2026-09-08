"""Consistent database backups and verified restore to a new directory only."""

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from .schema import SCHEMA_VERSION


def checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(store, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Backup destination must not exist.")
    destination = destination.resolve()
    if store.directory in destination.parents:
        raise ValueError("Keep backups outside the runtime directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".agentos-backup-", dir=destination.parent))
    try:
        target = sqlite3.connect(temp / "workspace.sqlite3")
        try:
            with store.connect() as source:
                source.backup(target)
        finally:
            target.close()
        names = ["workspace.sqlite3"]
        for name in ("workspace-marker.json", "providers.json"):
            path = store.directory / name
            if path.exists():
                if path.is_symlink():
                    raise ValueError("Backup metadata must not be a symbolic link.")
                shutil.copy2(path, temp / name)
                names.append(name)
        manifest = {
            "format": 1,
            "schema_version": SCHEMA_VERSION,
            "files": {n: checksum(temp / n) for n in names},
        }
        (temp / "backup.json").write_text(json.dumps(manifest, indent=2) + "\n")
        os.rename(temp, destination)
        return manifest
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def restore(source, destination):
    source = Path(source)
    destination = Path(destination)
    if source.is_symlink() or destination.exists() or destination.is_symlink():
        raise ValueError("Use a real backup and a new restore directory.")
    manifest_path = source / "backup.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_size > 10000:
        raise ValueError("Invalid backup manifest.")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("format") != 1 or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported backup format/schema.")
    files = manifest.get("files", {})
    if not {"workspace.sqlite3", "workspace-marker.json"} <= set(files) or set(
        files
    ) - {"workspace.sqlite3", "workspace-marker.json", "providers.json"}:
        raise ValueError("Unexpected backup files.")
    for name, expected in files.items():
        p = source / name
        if p.is_symlink() or checksum(p) != expected:
            raise ValueError("Backup checksum mismatch; restore was not attempted.")
    db = sqlite3.connect(
        f"file:{(source / 'workspace.sqlite3').resolve()}?mode=ro", uri=True
    )
    try:
        if (
            db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
            or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
        ):
            raise ValueError("Backup database validation failed.")
    finally:
        db.close()
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".agentos-restore-", dir=destination.parent))
    try:
        for name in files:
            shutil.copy2(source / name, temp / name)
        # Restores never restart saved provider jobs or routines automatically.
        db = sqlite3.connect(temp / "workspace.sqlite3")
        try:
            with db:
                for job_id, body in db.execute(
                    "SELECT id,body FROM jobs WHERE status IN ('queued','running')"
                ).fetchall():
                    job = json.loads(body)
                    job.update(
                        status="interrupted",
                        token=None,
                        error="restored_workspace; explicit new request required",
                    )
                    db.execute(
                        "UPDATE jobs SET status=?,body=? WHERE id=?",
                        ("interrupted", json.dumps(job), job_id),
                    )
                for routine_id, body in db.execute(
                    "SELECT id,body FROM routines"
                ).fetchall():
                    r = json.loads(body)
                    r.update(enabled=False, revision=r["revision"] + 1)
                    db.execute(
                        "UPDATE routines SET body=? WHERE id=?",
                        (json.dumps(r), routine_id),
                    )
        finally:
            db.close()
        os.rename(temp, destination)
        return {
            "restored": str(destination),
            "jobs": "interrupted",
            "routines": "paused",
        }
    finally:
        if temp.exists():
            shutil.rmtree(temp)
