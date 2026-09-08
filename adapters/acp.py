"""Small opt-in ACP v1 stdio client. Protocol denial is NOT an OS sandbox."""

import asyncio
import contextlib
import json
import os
import signal
from pathlib import Path


class ACPError(RuntimeError):
    pass


class ACPClient:
    """Caller owns executable trust, isolated profile, credentials and OS confinement.

    One client per provider instance/session. No auto-login, downloads, ambient
    environment copying, client filesystem tools, or approval grants.
    """

    def __init__(self, command, *, cwd, environment, timeout=30, event_limit=2000):
        if not command or not all(isinstance(a, str) and a for a in command):
            raise ACPError("Provide an explicit executable argument vector.")
        if not Path(command[0]).is_absolute() or not Path(cwd).is_absolute():
            raise ACPError("Executable and workspace must be absolute paths.")
        if (
            not isinstance(environment, dict)
            or not 0 < timeout <= 300
            or not 1 <= event_limit <= 10000
        ):
            raise ACPError("Invalid environment or limits.")
        self.command, self.cwd, self.environment = (
            list(command),
            str(cwd),
            dict(environment),
        )
        self.timeout, self.event_limit = timeout, event_limit
        self.pending, self.updates = {}, []
        self.update_bytes = 0
        self.counter, self.process, self.reader, self.stderr = 0, None, None, None
        self.capabilities = None

    async def start(self):
        if self.process is not None:
            raise ACPError("Client already started.")
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            cwd=self.cwd,
            env=self.environment,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1_000_000,
            start_new_session=os.name == "posix",
        )
        self.reader = asyncio.create_task(self._read())
        self.stderr = asyncio.create_task(self._drain_stderr())
        try:
            result = await self.request(
                "initialize",
                {
                    "protocolVersion": 1,
                    "clientCapabilities": {
                        "fs": {"readTextFile": False, "writeTextFile": False},
                        "terminal": False,
                    },
                    "clientInfo": {"name": "agentos-foundation", "version": "0.1.0"},
                },
            )
            if result.get("protocolVersion") != 1:
                raise ACPError("Unsupported negotiated ACP version.")
            self.capabilities = result
            return result
        except BaseException:
            await self.close()
            raise

    async def _send(self, message):
        if not self.process or self.process.returncode is not None:
            raise ACPError("ACP process is unavailable.")
        raw = json.dumps({"jsonrpc": "2.0", **message}).encode() + b"\n"
        if len(raw) > 1_000_000:
            raise ACPError("ACP request exceeds size limit.")
        self.process.stdin.write(raw)
        await self.process.stdin.drain()

    async def request(self, method, params):
        self.counter += 1
        request_id = self.counter
        future = asyncio.get_running_loop().create_future()
        self.pending[request_id] = future
        try:
            await self._send({"id": request_id, "method": method, "params": params})
            return await asyncio.wait_for(future, self.timeout)
        except asyncio.TimeoutError:
            raise ACPError(
                "ACP request timed out; do not infer a completed outcome."
            ) from None
        finally:
            self.pending.pop(request_id, None)

    async def _read(self):
        error = ACPError("ACP process disconnected.")
        try:
            while line := await self.process.stdout.readline():
                message = json.loads(line)
                if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                    raise ACPError("Malformed ACP envelope.")
                if "method" in message:
                    if "id" in message:
                        if message["method"] == "session/request_permission":
                            # ACP specifies cancellation when no permission decision is granted.
                            await self._send(
                                {
                                    "id": message["id"],
                                    "result": {"outcome": {"outcome": "cancelled"}},
                                }
                            )
                        else:
                            await self._send(
                                {
                                    "id": message["id"],
                                    "error": {
                                        "code": -32601,
                                        "message": "Client capability unavailable",
                                    },
                                }
                            )
                    elif message["method"] == "session/update":
                        self.update_bytes += len(line)
                        if (
                            len(self.updates) >= self.event_limit
                            or self.update_bytes > 4_000_000
                        ):
                            raise ACPError("ACP event limit exceeded.")
                        self.updates.append(message.get("params", {}))
                elif "id" in message:
                    future = self.pending.get(message["id"])
                    if future and not future.done():
                        if "error" in message:
                            future.set_exception(
                                ACPError(
                                    "ACP peer rejected request; inspect a redacted provider diagnostic."
                                )
                            )
                        else:
                            future.set_result(message.get("result", {}))
        except Exception:
            error = ACPError("ACP stream failed validation or exceeded limits.")
        finally:
            for future in list(self.pending.values()):
                if not future.done():
                    future.set_exception(error)

    async def _drain_stderr(self):
        while await self.process.stderr.read(8192):
            pass  # Drain to prevent deadlock; never echo unreviewed provider logs.

    async def new_session(self):
        if self.capabilities is None:
            raise ACPError("Initialize before creating a session.")
        return await self.request("session/new", {"cwd": self.cwd, "mcpServers": []})

    async def prompt(self, session_id, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 60000:
            raise ACPError("Expected bounded nonempty text.")
        return await self.request(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": text}]},
        )

    async def cancel(self, session_id):
        await self._send(
            {"method": "session/cancel", "params": {"sessionId": session_id}}
        )
        # Notification only: wait for prompt result/process outcome before showing stopped.

    async def close(self):
        if self.process:
            with contextlib.suppress(ProcessLookupError):
                if os.name == "posix":
                    os.killpg(self.process.pid, signal.SIGTERM)
                elif self.process.returncode is None:
                    self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), 2)
            except asyncio.TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    if os.name == "posix":
                        os.killpg(self.process.pid, signal.SIGKILL)
                    else:
                        self.process.kill()
                await self.process.wait()
        for task in (self.reader, self.stderr):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
