"""Inert probe admission/source refusals; no canonical IO namespace access."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import canonical_io_probe as probe


class Controls(unittest.TestCase):
    def test_wrong_schema_before_pin_iteration(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'plan.json'
            p.write_text('{"schema":"wrong"}')
            with self.assertRaises(ValueError):
                probe.pinned_plan(p)

    def test_source_drift_refused(self):
        with tempfile.TemporaryDirectory() as t:
            data = Path(t) / 'data'
            data.write_bytes(b'fixed')
            p = Path(t) / 'plan.json'
            p.write_text(json.dumps({'schema': 'firstpair-canonical-io-probe/1',
                  'pins': [{'path': str(data), 'bytes': 5,
                            'sha256': hashlib.sha256(b'fixed').hexdigest()}]}))
            probe.pinned_plan(p)
            data.write_bytes(b'drift')
            with self.assertRaises(ValueError):
                probe.pinned_plan(p)

    def test_admission_exact_command_digest_deadline(self):
        import shared_io_pool
        admission = {'state': 'ROOT_ADMITTED_ONE_LOCK_ONLY_CANONICAL_IO_PROBE',
            'plan_sha256': 'digest', 'command': [probe.sys.executable,
            str(Path(probe.__file__).resolve()), '--plan', '/plan',
            '--admission', '/admission'], 'start_deadline_unix': 200}
        with patch.object(shared_io_pool, 'read_manifest', return_value=admission), \
             patch.object(probe, 'digest', return_value='digest'), \
             patch.object(probe.time, 'time', return_value=100):
            probe.check_admission('/plan', '/admission')
            for key, bad in [('state', 'old'), ('command', []),
                             ('plan_sha256', 'wrong'), ('start_deadline_unix', 99)]:
                before = admission[key]
                admission[key] = bad
                with self.assertRaises(ValueError):
                    probe.check_admission('/plan', '/admission')
                admission[key] = before

    def test_worker_admission_refusal_before_plan_or_lock_access(self):
        with patch.object(probe, 'check_admission', side_effect=ValueError('not admitted')), \
             patch.object(probe, 'pinned_plan') as planned:
            with self.assertRaises(ValueError):
                probe.worker('/plan', '/admission')
            planned.assert_not_called()


if __name__ == '__main__':
    unittest.main()
