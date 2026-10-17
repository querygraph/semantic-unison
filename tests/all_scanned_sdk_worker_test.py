import copy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import all_scanned_sdk_worker as worker
import all_scanned_sdk_parent_test as parent_controls
from all_scanned_sdk_plan import plan
from all_scanned_sdk_audit_test import input_frame


class Worker(unittest.TestCase):
    def run_case(self, *, mutation=None, fail_persist=False, proxy_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model, contract, _ = parent_controls.Parent().fixture()
            contract['workspace'] = str(root)
            contract['transport_source_sha256'] = {}
            saved, raw, calls = [], {}, []
            def persist(value):
                if fail_persist and value['invocations'] and value['invocations'][-1]['state'] == 'OUTCOME':
                    raise OSError('original injected output save failure')
                saved.append(copy.deepcopy(value))
            def prepare(directory, label):
                for side in ('left', 'right'):
                    (directory / side / 'image.dng').write_bytes(b'original tiny fixture')
                return dict(modeled_source_identity_only=True)
            def verify(directory, _, *, source):
                for side in ('left', 'right'):
                    self.assertEqual((directory / side / 'image.dng').read_bytes(), b'original tiny fixture')
            class Invoke:
                def __init__(self, directory, *, binary, tool, phase, journal, **kwargs):
                    self.directory, self.binary, self.phase, self.journal = Path(directory), binary, phase, journal
                def __call__(self):
                    index = len(calls)
                    out = copy.deepcopy(model['invocations'][index]['outcome'])
                    proposal = plan(self.binary, contract['tool'], self.directory)[self.phase]
                    argv = proposal['argv']; out['command'] = argv
                    out['proxy']['server_command'] = [argv[0], '-server', *proposal['server_flags']]
                    out['stdout'] = '\n'.join(line for line in out['stdout'].splitlines() if 'validation-input]' not in line) + '\n'
                    if self.phase == 'validate':
                        out['stdout'] += input_frame('client', 200 + index * 2, 10 + index, self.directory)
                        out['stdout'] += input_frame('server', 201 + index * 2, 100 + index, self.directory)
                    if mutation is not None: mutation(index, out)
                    self.journal.begin(dict(label=self.binary['label'], mode='validation', workers=3,
                                            directory=str(self.directory), stage=self.phase), argv)
                    raw[str(self.directory / (self.phase + '-proxy.json'))] = copy.deepcopy(out['proxy'])
                    calls.append(out); self.journal.finish(out)
                    return out
            def read_proxy(path):
                if proxy_error is not None: raise proxy_error
                return raw[str(path)]
            with patch.object(worker, 'prepare_scripts', return_value={}), \
                 patch.object(worker, 'Invoker', Invoke), patch.object(worker, 'verify_roots', side_effect=verify):
                try:
                    result = worker.execute(contract, root, time.monotonic() + 600,
                        prepare_sources=prepare,
                        read_proxy=read_proxy, persist=persist, check_sources=lambda: None)
                    return result, saved, calls, None
                except BaseException as error:
                    return None, saved, calls, error

    def test_complete_four_call_worker_preserves_intent_and_narrow_parent_audit(self):
        result, saved, calls, error = self.run_case()
        self.assertIsNone(error)
        self.assertTrue(result['complete']); self.assertEqual(len(calls), 4)
        self.assertEqual(result['parent_audit']['helper_calls'], 4)
        self.assertFalse(result['parent_audit']['resource_release_authorized'])
        self.assertTrue(any(v['invocations'] and v['invocations'][-1]['state'] == 'INTENT' for v in saved))

    def test_missing_helper_retains_and_stops_before_next_compiler(self):
        def missing(index, out):
            if index == 1: out['stdout'] = 'Nothing to do: replicas have not changed since last sync.\n'
        _, saved, calls, error = self.run_case(mutation=missing)
        self.assertIsInstance(error, worker.UnresolvedOwnership)
        self.assertEqual(len(calls), 2)
        self.assertNotIn('failure', saved[-1])

    def test_settled_invalid_sdk_verdict_is_known_failure_not_unknown(self):
        def invalid(index, out):
            if index == 1:
                out['stdout'] = out['stdout'].replace(b'errors 0'.hex(), b'errors 1'.hex())
        _, saved, calls, error = self.run_case(mutation=invalid)
        self.assertIsInstance(error, ValueError)
        self.assertNotIsInstance(error, worker.UnresolvedOwnership)
        self.assertEqual(len(calls), 2)
        self.assertIn('failure', saved[-1])
        self.assertEqual(saved[-1]['cases'][0]['calls'][1]['helpers_settled']['sdk_helpers'], 2)

    def test_outcome_save_failure_retains_possible_call_without_retry(self):
        _, _, calls, error = self.run_case(fail_persist=True)
        self.assertIsInstance(error, worker.UnresolvedOwnership)
        self.assertEqual(len(calls), 1)

    def test_nested_proxy_close_uncertainty_keeps_exact_carrier(self):
        held = worker.UnresolvedOwnership('original proxy descriptor close',
                                         retained_fds=(987650,), uncertain_fd=987651)
        _, _, calls, error = self.run_case(proxy_error=held)
        self.assertIs(error, held)
        self.assertEqual(error.retained_fds, (987650,))
        self.assertEqual(error.uncertain_fd, 987651)
        self.assertEqual(len(calls), 1)

    def test_server_leader_reap_without_group_fence_remains_unknown(self):
        def missing(index, out):
            out['proxy']['server_cleanup'].pop('other_group_members_absent_before_reap')
        _, saved, calls, error = self.run_case(mutation=missing)
        self.assertIsInstance(error, worker.UnresolvedOwnership)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('failure', saved[-1])


if __name__ == '__main__': unittest.main()
