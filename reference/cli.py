"""AgentOS setup, source import, jobs, memory, routines and recovery."""

import argparse
import json
import sys
from pathlib import Path
from .core import Store, Invalid
from . import jobs, memory, recovery
from .providers import diagnostics
from .runner import run_once


def import_file(store, path):
    path = Path(path)
    if (
        path.is_symlink()
        or not path.is_file()
        or path.suffix.lower() not in (".md", ".txt")
        or path.stat().st_size > 48000
    ):
        raise Invalid(
            "Choose one regular .md/.txt source up to 48KB; symlinks are excluded."
        )
    body = path.read_text(encoding="utf-8")
    # Explicit file contents are imported; paths are not automatically published or crawled.
    import hashlib

    key = (
        "file:"
        + hashlib.sha256((str(path.resolve()) + "\0" + body).encode()).hexdigest()
    )
    return store.capture(path.stem[:120], body, key)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(".agentos"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("doctor")
    sub.add_parser("status")
    p = sub.add_parser("import")
    p.add_argument("path", type=Path)
    p = sub.add_parser("run")
    p.add_argument("source_id")
    p.add_argument("--request-id", required=True)
    p.add_argument("--provider", default="local")
    p.add_argument("--enqueue-only", action="store_true")
    sub.add_parser("work-once")
    p = sub.add_parser("cancel")
    p.add_argument("job_id")
    p = sub.add_parser("review")
    p.add_argument("artifact_id")
    p.add_argument("--digest", required=True)
    p.add_argument("--decision", choices=("accepted", "rejected"), required=True)
    p = sub.add_parser("memory")
    p.add_argument("query", nargs="?", default="")
    p = sub.add_parser("routine-create")
    p.add_argument("source_id")
    p.add_argument("--interval", type=int, required=True)
    p.add_argument("--first-run", required=True)
    p.add_argument("--provider", default="local")
    p = sub.add_parser("routine-enable")
    p.add_argument("routine_id")
    p.add_argument("--revision", type=int, required=True)
    p.add_argument("--paused", action="store_true")
    p = sub.add_parser("tick")
    p.add_argument("--at")
    p = sub.add_parser("backup")
    p.add_argument("destination", type=Path)
    p = sub.add_parser("restore")
    p.add_argument("backup", type=Path)
    p.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "restore":
            value = recovery.restore(args.backup, args.destination)
        else:
            store = Store(args.data_dir)
            if args.command == "init":
                root = Path(__file__).resolve().parents[1]
                baseline = root / ".foundation-baseline.json"
                if not baseline.exists():
                    template = json.loads((root / "template-manifest.json").read_text())
                    baseline.write_text(
                        json.dumps(
                            {
                                "format": 1,
                                "template_version": template["version"],
                                "files": template["files"],
                            },
                            indent=2,
                        )
                        + "\n"
                    )
                value = {
                    "workspace": str(store.directory),
                    "schema": 2,
                    "provider": "local",
                    "external_providers": "not configured",
                }
            elif args.command == "doctor":
                value = diagnostics(store)
            elif args.command == "status":
                value = {
                    "records": store.snapshot(),
                    "jobs": jobs.snapshot(store),
                    "routines": jobs.routines(store),
                }
            elif args.command == "import":
                value = import_file(store, args.path)
            elif args.command == "run":
                job = jobs.enqueue(
                    store, args.source_id, args.request_id, args.provider
                )
                if not args.enqueue_only and job["status"] == "queued":
                    run_once(store)
                with store.connect() as db:
                    value = jobs.read(db, job["id"])
            elif args.command == "work-once":
                value = run_once(store)
            elif args.command == "cancel":
                value = jobs.cancel(store, args.job_id)
            elif args.command == "review":
                value = store.review(args.artifact_id, args.digest, args.decision)
            elif args.command == "memory":
                value = memory.entries(store, args.query)
            elif args.command == "routine-create":
                value = jobs.routine_create(
                    store, args.source_id, args.interval, args.first_run, args.provider
                )
            elif args.command == "routine-enable":
                value = jobs.routine_enable(
                    store, args.routine_id, args.revision, not args.paused
                )
            elif args.command == "tick":
                value = jobs.tick(store, args.at)
            elif args.command == "backup":
                value = recovery.backup(store, args.destination)
        if isinstance(value, dict):
            value.pop("token", None)
        print(json.dumps(value, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
