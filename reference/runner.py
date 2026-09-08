"""Execute one claimed job in a child with wall-time, output and cancellation bounds."""

import json
import os
import signal
import subprocess
import sys
import threading
import time
from . import jobs
from .providers import ROOT


def run_once(store, stop_event=None, *, job_id=None):
    claimed = jobs.claim(store, job_id)
    if not claimed:
        return None
    job, source, config = claimed
    cwd = store.directory / "provider-workspaces" / config["id"]
    if cwd.is_symlink():
        return jobs.finish(store, job, error="provider_workspace_symlink_rejected")
    cwd.mkdir(parents=True, exist_ok=True)
    env = {
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    # Only explicitly referenced keys cross into the process; do not inherit all provider credentials.
    names = set(config.get("env_refs", {}).values())
    if config.get("key_env"):
        names.add(config["key_env"])
    for key in names:
        if key in os.environ:
            env[key] = os.environ[key]
    if os.name == "nt" and "SYSTEMROOT" in os.environ:
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "reference.provider_worker"],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
        )
        payload = json.dumps({"config": config, "source": source}).encode()
        process.stdin.write(payload)
        process.stdin.close()
        chunks = []
        size = [0]
        overflow = threading.Event()

        def drain(pipe, keep):
            while block := pipe.read(4096):
                size[0] += len(block)
                if size[0] > 2_000_000:
                    overflow.set()
                elif keep:
                    chunks.append(block)

        readers = [
            threading.Thread(target=drain, args=(process.stdout, True), daemon=True),
            threading.Thread(target=drain, args=(process.stderr, False), daemon=True),
        ]
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + config["timeout_seconds"]
        reason = None
        interrupted = False
        while process.poll() is None:
            with store.connect() as db:
                current = jobs.read(db, job["id"])
            if (
                current["cancel_requested"]
                or (stop_event and stop_event.is_set())
                or overflow.is_set()
                or time.monotonic() > deadline
            ):
                interrupted = bool(stop_event and stop_event.is_set())
                reason = (
                    "output_limit"
                    if overflow.is_set()
                    else "deadline_or_cancel_requested"
                )
                break
            time.sleep(0.05)
        if reason:
            terminate(process)
        else:
            process.wait()
        for reader in readers:
            reader.join(3)
        if any(r.is_alive() for r in readers):
            reason = "provider_stream_did_not_close"
        if reason or process.returncode:
            return jobs.finish(
                store,
                job,
                error=reason or "provider_or_output_failure",
                interrupted=interrupted,
            )
        value = json.loads(b"".join(chunks))
        return jobs.finish(store, job, plan=value["plan"], usage=value.get("usage"))
    except Exception:
        return jobs.finish(
            store, job, error="worker_failed; inspect setup and retry explicitly"
        )
    finally:
        if process:
            terminate(process)
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe:
                    pipe.close()


def terminate(process):
    if process.poll() is not None and os.name != "posix":
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
    except ProcessLookupError:
        pass
