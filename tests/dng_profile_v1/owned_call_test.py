"""Original injected lifecycle/close controls; no compiler, SDK or native clone."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from owned_call import execute
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership


def result(code=0):
    return {'returncode': code, 'stdout': 'fixed output\n', 'stderr': '',
            'capture_truncated': False,
            'client_cleanup': {'reaped': True,
                               'other_group_members_absent_before_reap': True}}


class OwnedCallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='unison-profile-owned-call-')
        self.root = Path(self.tmp.name)
        self.log = self.root / 'one.log'
        self.previous = Path.cwd()

    def tearDown(self):
        self.assertEqual(Path.cwd(), self.previous)
        self.tmp.cleanup()

    def run_call(self, observer):
        return execute(['inert-not-executed'], self.root, {}, self.log,
                       timeout=1, observer=observer)

    def test_runner_import_keeps_its_fixture_module_and_mutation_anchors(self):
        import runpy
        root = Path(__file__).resolve().parents[2]
        namespace = runpy.run_path(str(root / 'tests/dng_profile_v1/run.py'),
                                  run_name='qualification_source_control')
        self.assertEqual(namespace['Layout'].__module__, 'dng_profile_v1.fixtures')
        source = (root / 'src/dngSemantic.ml').read_text()
        self.assertEqual(namespace['mutate'](source, 'fixed'), source)
        for mode in ('wrong-CR-base', 'missing-CR-protection', 'widened-CR-pointer'):
            self.assertNotEqual(namespace['mutate'](source, mode), source)

    def test_success_preserves_actual_outcome_and_log(self):
        raw = result()
        actual = self.run_call(lambda *args: raw)
        self.assertIs(actual['outcome'], raw)
        self.assertEqual(self.log.read_text(), raw['stdout'])
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)

    def test_known_failure_preserves_exit_without_success_claim(self):
        actual = self.run_call(lambda *args: result(2))
        self.assertEqual(actual['exit_code'], 2)

    def test_observation_uncertainty_propagates_original_no_retry(self):
        error = UnresolvedOwnership('live owner', retained_fds=(1234567,))
        calls = []
        def observe(*args):
            calls.append(args)
            raise error
        with self.assertRaises(UnresolvedOwnership) as caught:
            self.run_call(observe)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(calls), 1)
        self.assertFalse(self.log.exists())

    def test_unsettled_group_refuses_log_and_keeps_outcome(self):
        raw = result()
        raw['client_cleanup']['other_group_members_absent_before_reap'] = False
        with self.assertRaises(UnresolvedOwnership) as caught:
            self.run_call(lambda *args: raw)
        self.assertIs(caught.exception.outcome, raw)
        self.assertFalse(self.log.exists())

    def test_truncated_capture_cannot_qualify(self):
        raw = result()
        raw['capture_truncated'] = True
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.run_call(lambda *args: raw)
        self.assertFalse(self.log.exists())

    def test_close_uncertainty_preserves_known_child_outcome_no_retry(self):
        raw = result()
        error = UnresolvedIOOwnership('injected close', retained_fds=(),
                                     uncertain_closes=({'fd': 1234567},))
        # The double closes its real descriptor once then raises a carrier.
        # It never leaves/retries a live number disguised as an uncertain FD.
        def close_then_unknown(fds):
            self.assertEqual(len(fds), 1)
            os.close(fds[0])
            raise error
        with patch('owned_call.close_descriptors', side_effect=close_then_unknown) as closer:
            with self.assertRaises(UnresolvedOwnership) as caught:
                self.run_call(lambda *args: raw)
        self.assertIs(caught.exception, error)
        self.assertIs(error.outcome, raw)
        self.assertEqual(closer.call_count, 1)

    def test_write_and_close_failures_keep_original_failure(self):
        original = OSError('injected write')
        uncertain = UnresolvedIOOwnership('injected close', retained_fds=(),
                                         uncertain_closes=({'fd': 1234567},),
                                         original_failure=original)
        def close_then_unknown(fds):
            os.close(fds[0])
            raise uncertain
        with patch('owned_call.os.write', side_effect=original), \
             patch('owned_call.close_descriptors', side_effect=close_then_unknown) as closer:
            with self.assertRaises(UnresolvedOwnership) as caught:
                self.run_call(lambda *args: result())
        self.assertIs(caught.exception.original_failure, original)
        self.assertEqual(closer.call_count, 1)


if __name__ == '__main__':
    unittest.main()
