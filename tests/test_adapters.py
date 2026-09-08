import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from adapters.acp import ACPClient, ACPError
from adapters.http_models import (
    Endpoint,
    ProviderError,
    build_request,
    parse_response,
    complete,
)


class EndpointTests(unittest.TestCase):
    def config(self, dialect):
        return Endpoint(
            "https://provider.example/v1", dialect, "fixture-model", "AGENTOS_TEST_KEY"
        )

    @patch.dict(os.environ, {"AGENTOS_TEST_KEY": "fixture-not-a-real-key"})
    def test_three_explicit_request_dialects(self):
        for dialect, path in [
            ("openai-chat", "/chat/completions"),
            ("openai-responses", "/responses"),
            ("anthropic-messages", "/messages"),
        ]:
            r = build_request(
                self.config(dialect), "Selected text", "System instruction"
            )
            self.assertEqual(r.full_url, "https://provider.example/v1" + path)
            data = json.loads(r.data)
            self.assertFalse(data["stream"])
            if dialect == "anthropic-messages":
                self.assertEqual(data["system"], "System instruction")
                self.assertEqual(r.get_header("X-api-key"), "fixture-not-a-real-key")
            else:
                self.assertEqual(
                    r.get_header("Authorization"), "Bearer fixture-not-a-real-key"
                )

    def test_auth_url_and_dialect_validation(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ProviderError):
            build_request(self.config("openai-chat"), "prompt")
        for url in [
            "http://remote.example/v1",
            "https://user:password@example.com/v1",
            "https://example.com/v1?key=bad",
        ]:
            with self.assertRaises(ProviderError):
                Endpoint(url, "openai-chat", "model", "KEY").validate()
        with self.assertRaises(ProviderError):
            Endpoint("https://example.com/v1", "guess", "model", "KEY").validate()

    def test_output_normalization_and_incomplete(self):
        responses = {
            "openai-chat": {
                "choices": [{"finish_reason": "stop", "message": {"content": "Hello"}}]
            },
            "openai-responses": {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "Hello"}],
                    }
                ],
            },
            "anthropic-messages": {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "Hello"}],
            },
        }
        for dialect, response in responses.items():
            self.assertEqual(parse_response(dialect, response)["text"], "Hello")
            self.assertIsNone(parse_response(dialect, response)["usage"])
            with self.assertRaises(ProviderError):
                parse_response(dialect, {})
        with self.assertRaises(ProviderError):
            parse_response(
                "openai-chat",
                {
                    "choices": [
                        {"finish_reason": "length", "message": {"content": "partial"}}
                    ]
                },
            )
        with self.assertRaises(ProviderError):
            parse_response(
                "anthropic-messages", {"stop_reason": "tool_use", "content": []}
            )

    @patch.dict(os.environ, {"AGENTOS_TEST_KEY": "fixture-only"})
    def test_real_http_peer_and_redirect_refusal(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import threading

        seen = []

        class Peer(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                seen.append(
                    json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                )
                if self.path.startswith("/redirect"):
                    self.send_response(307)
                    self.send_header("Location", "/v1/chat/completions")
                    self.end_headers()
                    return
                response = {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": "Fixture output"},
                        }
                    ]
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

        server = HTTPServer(("127.0.0.1", 0), Peer)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            c = Endpoint(
                base + "/v1",
                "openai-chat",
                "fixture",
                "AGENTOS_TEST_KEY",
                allow_loopback_http=True,
            )
            self.assertEqual(complete(c, "Hello")["text"], "Fixture output")
            with self.assertRaisesRegex(ProviderError, "307"):
                complete(
                    Endpoint(
                        base + "/redirect",
                        "openai-chat",
                        "fixture",
                        "AGENTOS_TEST_KEY",
                        allow_loopback_http=True,
                    ),
                    "Hello",
                )
            self.assertEqual(len(seen), 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


class ACPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.client = ACPClient(
            [sys.executable, str(Path(__file__).with_name("fake_acp.py").resolve())],
            cwd=self.tmp.name,
            environment={},
            timeout=1,
        )
        await self.client.start()

    async def asyncTearDown(self):
        await self.client.close()
        self.tmp.cleanup()

    async def test_negotiate_prompt_updates_and_deny_permission(self):
        session = await self.client.new_session()
        result = await self.client.prompt(session["sessionId"], "Hello")
        self.assertEqual(result["stopReason"], "end_turn")
        self.assertEqual(
            self.client.updates[0]["update"]["content"]["text"],
            "Permission denied; fixture response.",
        )

    async def test_cancel_is_notification_until_prompt_confirms(self):
        session = await self.client.new_session()
        task = asyncio.create_task(self.client.prompt(session["sessionId"], "wait"))
        await asyncio.sleep(0.02)
        await self.client.cancel(session["sessionId"])
        self.assertEqual((await task)["stopReason"], "cancelled")

    async def test_timeout_and_malformed_peer(self):
        session = await self.client.new_session()
        self.client.timeout = 0.1
        with self.assertRaisesRegex(ACPError, "timed out"):
            await self.client.prompt(session["sessionId"], "wait")
        with self.assertRaises(ACPError):
            await self.client.prompt(session["sessionId"], "malformed")
