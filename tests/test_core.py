import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from reference.core import Store, Invalid, Conflict


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)

    def source(self):
        return self.store.capture('Synthetic research brief', 'Compare two proposed methods using cited evidence.', 'capture-1')

    def artifact(self):
        return self.store.draft(self.source()['id'], 'draft-1')

    def test_complete_loop_and_restart(self):
        a = self.artifact()
        self.assertEqual(a['review'], 'pending')
        self.assertEqual(len(self.store.snapshot()['projects']), 0)
        self.store.review(a['id'], a['digest'], 'accepted')
        state = Store(self.tmp.name).snapshot()
        self.assertEqual(len(state['projects']), 1)
        self.assertEqual(state['projects'][0]['source_id'], a['content']['source_id'])
        self.assertTrue(all(t['status'] == 'proposed' for t in state['projects'][0]['tasks']))
        self.assertEqual(len(state['events']), 3)

    def test_duplicates_and_changed_request(self):
        a = self.artifact()
        self.assertEqual(self.artifact()['id'], a['id'])
        self.store.review(a['id'], a['digest'], 'accepted')
        self.store.review(a['id'], a['digest'], 'accepted')
        self.assertEqual(len(self.store.snapshot()['projects']), 1)
        with self.assertRaises(Conflict):
            self.store.capture('Different input', 'Different body', 'capture-1')

    def test_competing_acceptances_create_one_project(self):
        a = self.artifact()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.store.review(a['id'], a['digest'], 'accepted'), range(2)))
        self.assertEqual(results[0]['project_id'], results[1]['project_id'])
        self.assertEqual(len(self.store.snapshot()['projects']), 1)

    def test_reject_does_not_activate(self):
        a = self.artifact()
        self.store.review(a['id'], a['digest'], 'rejected')
        self.assertEqual(self.store.snapshot()['projects'], [])
        with self.assertRaises(Conflict):
            self.store.review(a['id'], a['digest'], 'accepted')

    def test_invalid_and_missing_input(self):
        for value in ['', '   ', None, 'x' * 12001]:
            with self.assertRaises(Invalid):
                self.store.capture('Title', value, 'request')
        with self.assertRaises(Invalid):
            self.store.draft('missing', 'request')
        self.assertEqual(self.store.snapshot()['runs'], [])

    def test_stale_or_tampered_review(self):
        a = self.artifact()
        with self.assertRaises(Conflict):
            self.store.review(a['id'], 'bad-digest', 'accepted')
        with self.store.connect() as db:
            a['content']['objective'] = 'tampered'
            db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(a), a['id']))
        with self.assertRaises(Conflict):
            self.store.review(a['id'], a['digest'], 'accepted')
        self.assertEqual(self.store.snapshot()['projects'], [])

    def test_changed_source_and_failed_validation(self):
        a = self.artifact()
        with self.store.connect() as db:
            source = self.store._get(db, a['content']['source_id'])
            source['digest'] = 'changed'
            self.store._save(db, 'source', source)
        with self.assertRaises(Conflict):
            self.store.review(a['id'], a['digest'], 'accepted')
        with self.store.connect() as db:
            source['digest'] = a['content']['source_digest']
            self.store._save(db, 'source', source)
            a['validation'] = 'failed'
            self.store._save(db, 'artifact', a)
        with self.assertRaises(Conflict):
            self.store.review(a['id'], a['digest'], 'accepted')

    def test_backup_restore(self):
        import shutil
        a = self.artifact()
        self.store.review(a['id'], a['digest'], 'accepted')
        with tempfile.TemporaryDirectory() as restored:
            shutil.copy2(self.store.path, restored)
            before, after = self.store.snapshot(), Store(restored).snapshot()
            before.pop('as_of'); after.pop('as_of')
            self.assertEqual(before, after)
