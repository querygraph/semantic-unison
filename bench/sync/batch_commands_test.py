import unittest
from batch_commands import schedule
from batch_events import Events
from batch_artifacts_test import MemoryStore


class Contracts(unittest.TestCase):
    def test_endpoint_and_owner_budget_is_inside_eight(self):
        for workers in (1,2,3):
            out = schedule('/stock', '/ox', '/private/tmp/u-batch-x', mode='semantic', workers=workers)
            self.assertLessEqual(out['configured_endpoint_plus_owner_bound'], 8)
            self.assertEqual([r['stage'] for r in out['rows']], ['seed','update','noop'])
            for row in out['rows']:
                self.assertIn('-semanticdng', row['server_flags'])
                self.assertIn('copy', row['server_flags'])
                self.assertEqual(row['server_flags'].count('-debug'),2)
                self.assertEqual(row['server_flags'][row['server_flags'].index('-adobevalidate')+1], 'off')
            self.assertFalse(out['runtime_admitted'])
        with self.assertRaises(ValueError): schedule('/stock','/ox','/tmp/u',mode='semantic',workers=4)

    def test_ordered_events_shard_and_do_not_release(self):
        store = MemoryStore(); events = Events(store)
        events(dict(stage='seed-intent', planned_files=1024))
        events(dict(stage='seed-inventory', files=[dict(index=i) for i in range(4096)]))
        record = store.read_json(events.pins[-1]['name'], expected_sha256=events.pins[-1]['sha256'])
        self.assertEqual(record['value']['count'],4096)
        self.assertEqual(len(record['value']['shards']),4)
        self.assertFalse(record['resource_release_authorized'])
        with self.assertRaises(ValueError): events(dict(stage='seed-intent', planned_files=1))

    def test_uncertain_write_consumes_event_without_retry(self):
        from unittest.mock import patch
        events = Events(MemoryStore()); marker = RuntimeError('write uncertainty')
        with patch.object(events.store, 'write', side_effect=marker) as write:
            with self.assertRaises(RuntimeError): events(dict(stage='seed-intent', planned_files=1))
            with self.assertRaises(ValueError): events(dict(stage='seed-intent', planned_files=1))
            with self.assertRaises(ValueError): events(dict(stage='seed-inventory', files=[]))
            self.assertEqual(write.call_count,1)


if __name__ == '__main__': unittest.main()
