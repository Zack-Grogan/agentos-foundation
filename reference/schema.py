"""Versioned additive storage migration with pre-migration recovery copies."""

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 2


def migrate(path):
    path = Path(path)
    existed = path.exists()
    if path.is_symlink():
        raise ValueError("Runtime database must not be a symbolic link.")
    db = sqlite3.connect(path, timeout=10)
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError(
                "This workspace needs a newer AgentOS version; no changes were made."
            )
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError(
                "Database integrity check failed; preserve files and restore a backup."
            )
        tables = {
            r[0]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        expected = {"records", "requests", "events", "jobs", "routines", "settings"}
        if version == SCHEMA_VERSION and not expected <= tables:
            raise ValueError(
                "Workspace tables are missing; restore a backup instead of recreating them."
            )
        if version == 0 and tables and not {"records", "requests", "events"} <= tables:
            raise ValueError("Unrecognized database; refusing to initialize over it.")
        if existed and tables and version < SCHEMA_VERSION:
            backup = path.with_name(f"{path.name}.before-v{SCHEMA_VERSION}.bak")
            if not backup.exists():
                with sqlite3.connect(backup) as copy:
                    db.backup(copy)
                copy.close()
        db.execute("BEGIN IMMEDIATE")
        for sql in [
            "CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result_id TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, target TEXT NOT NULL, at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL, status TEXT NOT NULL, body TEXT NOT NULL)",
            "CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status)",
            "CREATE TABLE IF NOT EXISTS routines (id TEXT PRIMARY KEY, body TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, body TEXT NOT NULL)",
        ]:
            db.execute(sql)
        db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
