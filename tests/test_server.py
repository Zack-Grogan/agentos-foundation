import http.client
import json
import tempfile
import threading
import unittest
from reference.server import make_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = make_server(self.tmp.name, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.cookie = None
        _, _, headers = self.call('GET', '/')
        self.cookie = headers['Set-Cookie'].split(';')[0]
        _, value, _ = self.call('GET', '/api/session')
        self.csrf = value['csrf']

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.tmp.cleanup()

    def call(self, method, path, body=None, headers=None):
        h = {'Cookie': self.cookie} if self.cookie else {}
        h.update(headers or {})
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        c.request(method, path, json.dumps(body) if body is not None else None, headers=h)
        r = c.getresponse(); raw = r.read(); status = r.status; hs = dict(r.getheaders()); c.close()
        return status, json.loads(raw) if hs.get('Content-Type', '').startswith('application/json') else raw, hs

    def auth(self):
        return {'Origin': f'http://127.0.0.1:{self.port}', 'X-CSRF-Token': self.csrf, 'Content-Type': 'application/json'}

    def test_real_http_flow(self):
        status, source, _ = self.call('POST', '/api/capture', {'title': 'Example', 'body': 'A useful brief', 'request_id': 'a'}, self.auth())
        self.assertEqual(status, 200)
        status, draft, _ = self.call('POST', '/api/draft', {'source_id': source['id'], 'request_id': 'b'}, self.auth())
        self.assertEqual(status, 200)
        status, _, _ = self.call('POST', '/api/review', {'artifact_id': draft['id'], 'expected_digest': draft['digest'], 'decision': 'accepted'}, self.auth())
        self.assertEqual(status, 200)
        self.assertEqual(len(self.call('GET', '/api/state')[1]['projects']), 1)

    def test_cross_origin_and_missing_csrf_denied(self):
        body = {'title': 'Example', 'body': 'brief', 'request_id': 'a'}
        for headers in [{}, {**self.auth(), 'Origin': 'https://untrusted.example'}, {**self.auth(), 'X-CSRF-Token': 'wrong'}]:
            self.assertEqual(self.call('POST', '/api/capture', body, headers)[0], 403)

    def test_host_and_forwarded_header_denied(self):
        for h in [{'Host': 'evil.example'}, {'X-Forwarded-For': '127.0.0.1'}, {'Sec-Fetch-Site': 'cross-site'}]:
            self.assertEqual(self.call('GET', '/', headers=h)[0], 403)

    def test_only_named_assets_and_operations(self):
        for path in ['/../README.md', '/.agentos/workspace.sqlite3', '/api/file?path=secret', '/%2e%2e/README.md']:
            self.assertEqual(self.call('GET', path)[0], 404)
        self.assertEqual(self.call('POST', '/api/shell', {}, self.auth())[0], 404)
        self.assertEqual(self.call('POST', '/api/capture', {'command': 'anything'}, self.auth())[0], 400)

    def test_untrusted_text_is_data(self):
        text = '<script>window.compromised=true</script>'
        status, value, _ = self.call('POST', '/api/capture', {'title': 'Example', 'body': text, 'request_id': 'a'}, self.auth())
        self.assertEqual(status, 200); self.assertEqual(value['body'], text)
        html = self.call('GET', '/')[1]
        self.assertNotIn(text.encode(), html)
