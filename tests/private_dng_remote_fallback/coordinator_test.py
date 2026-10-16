"""Fixed mocked owner controls. No canonical lock or transport is acquired."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import coordinator as c


class Retained(Exception):
    pass


class Lease:
    def __init__(self, label, events, fail=False):
        self.label, self.events, self.closed, self.fail = label, events, False, fail
        self.fds = (19,) if label == 'io' else tuple(range(20, 28))

    def close_after_verified_settlement(self, **proof):
        if not all(proof.get(k) is True for k in
                   ('owner_reaped', 'groups_settled', 'external_children_settled')):
            raise AssertionError('missing actual closure attestation')
        self.events.append(self.label+'-close'); self.closed = True
        if self.fail:
            raise c.UnresolvedOwnership('uncertain close', retained_fds=(21,), uncertain_fd=20)


class OwnerControls(unittest.TestCase):
    def exercise(self, *, busy=False, terminal=True, remote_error=False,
                 worker_code=0, source_changed=False, cpu_close_error=False,
                 report_error=False, prelaunch_error=False, acquisition_error=False):
        with tempfile.TemporaryDirectory() as name, ExitStack() as stack:
            base = Path(name); workspace = base/'workspace'; plan = base/'plan.json'
            plan.write_text('{}')
            events = []
            io = Lease('io', events); cpu = Lease('cpu', events, cpu_close_error)
            rows = [{'pair': ['stock', 'stock'], 'stage': 'seed', 'settled': True}]
            admission = dict(state='ROOT_ADMITTED_ONE_SYNTHETIC_REMOTE_FALLBACK',
                             plan_sha256=c.hashlib.sha256(b'{}').hexdigest(),
                             workspace=str(workspace), start_deadline_unix=c.time.time()+60)
            admission['launch_argv_without_admission_sha256'] = [c.sys.executable,
                str(Path(c.__file__)), '--plan', str(plan), '--admission', '/fixed/fake-admission']
            def retain(record):
                events.append('retained'); record(); raise Retained()
            class Child:
                pid = 999
                def __init__(self, argv, **kwargs):
                    events.append('spawn')
                    self.reaped = False
                    self.inherited = kwargs['pass_fds']
                    self_test.assertEqual(self.inherited, io.fds+cpu.fds)
                    (workspace/'REMOTE-SETTLED.json').write_text(json.dumps({
                        'worker_finished_starting_calls': True, 'calls': rows}))
                    (workspace/'WORKER-RESULT.json').write_text('{}')
                def await_terminal(self, timeout):
                    events.append('observe-terminal'); return terminal
            self_test = self
            def remote(path):
                events.append('remote-audit')
                if remote_error: raise ValueError('pending intent')
                return rows
            def settle(child, deadline):
                events.append('worker-reap')
                return dict(reaped=True, other_group_members_absent_before_reap=True,
                            returncode=worker_code)
            original_write = c.exclusive_json
            def write(path, value):
                if report_error and path.name == 'AGGREGATE-CLOSED.json':
                    raise OSError('fixed final-report failure')
                return original_write(path, value)
            def bundle(*args):
                events.append('io-cpu-acquire')
                if acquisition_error:
                    raise c.UnresolvedOwnership('partial acquisition uncertain', retained_fds=(18,))
                return None if busy else (io, cpu)
            mocks = {
                'require_ownership_support': lambda: None,
                'checked_plan': lambda value: workspace,
                'read_manifest': lambda *args: admission,
                'authorized_unison_tokens': lambda raw: tuple(range(8)),
                'try_io_cpu_bundle': bundle,
                'check_binaries': (lambda value: (_ for _ in ()).throw(ValueError('binary changed')))
                                  if prelaunch_error else lambda value: None,
                'OwnedGroup': Child, 'remote_settlement': remote, 'settle': settle,
                'source_pins': lambda: {'changed': True} if source_changed else {},
                'functional_evidence': lambda result, path: events.append('functional-audit'),
                'retain_after_record': retain, 'exclusive_json': write}
            # checked_plan is mocked above; source comparison still uses this
            # exact in-memory plan value after the worker closes.
            plan.write_text(json.dumps({'execution_source_sha256': {}}))
            admission['plan_sha256'] = c.hashlib.sha256(plan.read_bytes()).hexdigest()
            for key, value in mocks.items(): stack.enter_context(patch.object(c, key, value))
            stack.enter_context(patch.object(c.Pool, 'read', return_value=object()))
            stack.enter_context(patch.object(c.GlobalPool, 'read', return_value=object()))
            stack.enter_context(patch.object(c.os, 'fstat', return_value=types.SimpleNamespace(st_dev=1, st_ino=2)))
            try:
                code = c.owner(plan, '/fixed/fake-admission', '0'*64)
            except (Retained, OSError) as error:
                code = type(error).__name__
            unknown = json.loads((workspace/'OWNER-UNKNOWN.json').read_text()) if (
                workspace/'OWNER-UNKNOWN.json').exists() else None
            return code, events, unknown

    def test_success_order(self):
        code, events, _ = self.exercise()
        self.assertEqual(code, 0)
        self.assertEqual(events, ['io-cpu-acquire', 'spawn', 'observe-terminal',
            'remote-audit', 'worker-reap', 'functional-audit', 'cpu-close', 'io-close'])

    def test_busy_never_spawns(self):
        code, events, _ = self.exercise(busy=True)
        self.assertEqual((code, events), (2, ['io-cpu-acquire']))

    def test_prelaunch_refusal_rolls_back(self):
        code, events, _ = self.exercise(prelaunch_error=True)
        self.assertEqual((code, events), (2, ['io-cpu-acquire', 'cpu-close', 'io-close']))

    def test_deadline_unknown_never_kills_or_reaps(self):
        code, events, unknown = self.exercise(terminal=False)
        self.assertEqual(code, 'Retained')
        self.assertNotIn('worker-reap', events); self.assertNotIn('cpu-close', events)
        self.assertEqual(unknown['worker_pid'], 999)
        self.assertEqual(unknown['known_io_fds'], [19])

    def test_pending_remote_retains_before_worker_reap(self):
        code, events, _ = self.exercise(remote_error=True)
        self.assertEqual(code, 'Retained')
        self.assertNotIn('worker-reap', events); self.assertNotIn('io-close', events)

    def test_failed_but_settled_worker_releases_without_pass(self):
        code, events, _ = self.exercise(worker_code=1)
        self.assertEqual(code, 1); self.assertNotIn('functional-audit', events)
        self.assertEqual(events[-2:], ['cpu-close', 'io-close'])

    def test_source_change_retains(self):
        code, events, _ = self.exercise(source_changed=True)
        self.assertEqual(code, 'Retained'); self.assertNotIn('cpu-close', events)

    def test_close_uncertainty_keeps_io_and_carrier(self):
        code, events, unknown = self.exercise(cpu_close_error=True)
        self.assertEqual(code, 'Retained'); self.assertNotIn('io-close', events)
        self.assertEqual(unknown['retained_fds'], [21]); self.assertEqual(unknown['uncertain_fd'], 20)
        self.assertEqual(unknown['known_io_fds'], [19])

    def test_acquisition_uncertainty_retains(self):
        code, events, unknown = self.exercise(acquisition_error=True)
        self.assertEqual(code, 'Retained'); self.assertNotIn('spawn', events)
        self.assertEqual(unknown['retained_fds'], [18])

    def test_known_closed_report_error_does_not_claim_live_owner(self):
        code, events, unknown = self.exercise(report_error=True)
        self.assertEqual(code, 'OSError'); self.assertIsNone(unknown)
        self.assertEqual(events[-2:], ['cpu-close', 'io-close'])


class EvidenceControls(unittest.TestCase):
    def test_saved_outcome_binding(self):
        # Fabricated success shape supplied to a mocked functional audit;
        # this tests binding, not correctness of the transport audit itself.
        with tempfile.TemporaryDirectory() as name, patch.object(c, 'audit', return_value={'calls': 3}):
            root = Path(name); directory = root/'stock-ox'; directory.mkdir()
            calls = {stage: {'fixed': stage} for stage in ('seed', 'update', 'noop')}
            result = {'cases': [{'compiler_pair': ['stock', 'ox'], 'calls': calls}]}
            for stage, value in calls.items():
                (directory/(stage+'-OUTCOME.json')).write_text(json.dumps(value))
            self.assertEqual(c.functional_evidence(result, root), {'calls': 3})
            (directory/'update-OUTCOME.json').write_text('{}')
            with self.assertRaises(ValueError): c.functional_evidence(result, root)

    def test_empty_ledger_is_not_functional_pass(self):
        with tempfile.TemporaryDirectory() as name:
            self.assertEqual(c.remote_settlement(name), [])
            with self.assertRaises((ValueError, KeyError)):
                c.functional_evidence({'schema': 'unison-private-dng-remote-fallback/1',
                    'parameters': c.PARAMETERS, 'complete': False, 'cases': []}, name)

    def test_plan_fixed_scope_and_source_pins(self):
        def plan():
            return {'schema': 'unison-private-dng-remote-owner/2', 'parameters': dict(c.PARAMETERS),
                    'worker_seconds': 480, 'execution_source_sha256': {},
                    'workspace': '/private/tmp/u-rf-fixed',
                    'binaries': {label: {'label': label, 'path': '/fixed/'+label, 'sha256': '0'*64}
                                 for label in ('stock', 'ox')},
                    'io_manifest_sha256': c.CANONICAL_SHA256, 'cpu_manifest_sha256': c.MANIFEST_SHA}
        with patch.object(c, 'source_pins', return_value={}):
            self.assertEqual(c.checked_plan(plan()), Path('/private/tmp/u-rf-fixed'))
            for change in ('source', 'scope', 'path', 'worker-bool', 'worker-float', 'binary', 'manifest'):
                value = plan()
                if change == 'source': value['execution_source_sha256'] = {'wrong': 'pin'}
                elif change == 'scope': value['parameters']['files'] = True
                elif change == 'path': value['workspace'] = '/Users/other'
                elif change == 'worker-bool': value['worker_seconds'] = True
                elif change == 'worker-float': value['worker_seconds'] = 480.0
                elif change == 'binary': del value['binaries']['ox']
                else: value['io_manifest_sha256'] = 'wrong'
                with self.subTest(change=change), self.assertRaises(ValueError): c.checked_plan(value)


class WorkerControls(unittest.TestCase):
    def exercise(self, unknown=False):
        with tempfile.TemporaryDirectory() as name, ExitStack() as stack:
            root = Path(name); packet = root/'WORKER-PACKET.json'
            packet.write_text(json.dumps({'plan': {'binaries': {'stock': {}, 'ox': {}}},
                'parent_pid': c.os.getppid(), 'deadline_monotonic': c.time.monotonic()+60,
                'inherited_fds': [dict(fd=fd, device=1, inode=2) for fd in range(10, 19)]}))
            original = RuntimeError('fixed synthetic dispatch exception')
            def fake_case(*args, **kwargs):
                if unknown: raise original
                return {}
            def retain(record):
                record(); raise Retained()
            def remote(path):
                if unknown: raise ValueError('fixed missing outcome')
                return []
            stack.enter_context(patch.object(c, 'checked_plan', return_value=root))
            stack.enter_context(patch.object(c.os, 'fstat', return_value=types.SimpleNamespace(st_dev=1, st_ino=2)))
            stack.enter_context(patch.dict(c.sys.modules, {'case': types.SimpleNamespace(execute_case=fake_case)}))
            stack.enter_context(patch.object(c, 'audit', return_value={}))
            stack.enter_context(patch.object(c, 'remote_settlement', side_effect=remote))
            stack.enter_context(patch.object(c, 'retain_after_record', side_effect=retain))
            if unknown:
                with self.assertRaises(Retained): c.worker(packet)
                result = json.loads((root/'WORKER-UNKNOWN.json').read_text())
                self.assertTrue(result['original_exception_retained'])
                self.assertIn('fixed synthetic dispatch exception', result['original_failure'])
                self.assertFalse((root/'REMOTE-SETTLED.json').exists())
            else:
                self.assertEqual(c.worker(packet), 0)
                self.assertTrue(json.loads((root/'WORKER-RESULT.json').read_text())['complete'])
                self.assertTrue(json.loads((root/'REMOTE-SETTLED.json').read_text())['functional_pass'])

    def test_worker_fixed_fake_success(self):
        self.exercise()

    def test_worker_unknown_retains_original_exception(self):
        self.exercise(unknown=True)


if __name__ == '__main__': unittest.main()
