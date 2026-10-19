"""Original fake-child transport composition; no process or canonical IO."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from batch_artifacts_test import MemoryStore
from batch_transport import launch, restore


def pending(code=0):
    raw = b'\xfforiginal\x00'
    out = dict(command=['never-execute'], returncode=code, timed_out=False,
               capture_truncated=False, stdout=raw.decode('utf8', 'replace'), stderr='',
               client_cleanup=dict(pid=42, returncode=code, reaped=True, hard_kill_required=False,
                 other_group_members_absent_before_reap=True, group_cleanup_before_leader_reap=True),
               aggregate_or_parent_terminal_proved=False, io_cpu_release_authorized=False)
    capture = lambda raw: SimpleNamespace(thread=SimpleNamespace(is_alive=lambda: False),
        error=None, total=len(raw), limit=262144, chunks=[raw])
    return SimpleNamespace(finish=lambda deadline: out,
                           capture_owners=[capture(raw), capture(b'')])


class TransportTests(unittest.TestCase):
    def test_pins_roundtrip_without_lossy_reconstruction(self):
        store = MemoryStore(); child = pending()
        with patch('batch_transport.start', return_value=child) as start:
            call = launch(['never-execute'], {}, pass_fds=(7,), store=store, name='seed')
            pin = call.finish(100)
            self.assertEqual(restore(store, pin, ['never-execute']), call.outcome)
            start.assert_called_once_with(['never-execute'], {}, pass_fds=(7,), capture_limit=4*1048576)
            with self.assertRaises(ValueError): call.finish(101)
        self.assertNotIn('stdout', store.read_json(pin['name'], expected_sha256=pin['sha256'])['outcome'])

    def test_failed_exit_is_preserved_before_functional_refusal(self):
        store = MemoryStore()
        with patch('batch_transport.start', return_value=pending(1)):
            call = launch(['never-execute'], {}, pass_fds=(), store=store, name='failed')
            with self.assertRaises(ValueError): call.finish(100)
        self.assertIsNotNone(call.record)
        with self.assertRaises(ValueError): restore(store, call.record, ['never-execute'])

    def test_nested_uncertainty_identity_survives_without_finish_retry(self):
        marker = RuntimeError('simulated retained carrier')
        child = pending()
        def fail(deadline): raise marker
        child.finish = fail
        store = MemoryStore()
        with patch('batch_transport.start', return_value=child):
            call = launch(['never-execute'], {}, pass_fds=(), store=store, name='unknown')
            with self.assertRaises(RuntimeError) as got: call.finish(100)
            self.assertIs(got.exception, marker)
            self.assertIs(call.pending, child)
            self.assertEqual(store.files, {})
            with self.assertRaises(ValueError): call.finish(101)

    def test_capture_overflow_is_not_published_as_complete(self):
        child = pending(); child.capture_owners[0].total = 262145
        store = MemoryStore()
        with patch('batch_transport.start', return_value=child):
            call = launch(['never-execute'], {}, pass_fds=(), store=store, name='overflow')
            with self.assertRaises(ValueError): call.finish(100)
        self.assertEqual(store.files, {})


if __name__ == '__main__': unittest.main()
