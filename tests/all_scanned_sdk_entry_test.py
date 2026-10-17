import copy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import all_scanned_sdk_entry as entry
import all_scanned_sdk_boundary as boundary
import all_scanned_sdk_worker as worker
import shared_dispatch as dispatch
from sdk_host_matrix import shared_binding


class Entry(unittest.TestCase):
    def test_actual_child_argument_shape_uses_names_not_python_argv_offsets(self):
        import all_scanned_sdk_entry_lifecycle as lifecycle
        path, digest, workspace = '/inert/plan', 'a' * 64, '/private/tmp/u-asv-inert'
        argv = lifecycle.command(path, digest, workspace)
        args = lifecycle.worker_arguments(argv[2:])
        self.assertEqual((args.plan, args.plan_sha256, args.workspace), (path, digest, workspace))

    def test_dispatch_has_no_cpu_only_native_route(self):
        with patch.object(dispatch.Pool, 'read') as pool:
            with self.assertRaises(ValueError):
                dispatch.run(entry.TARGET, [boundary.PYTHON, str(Path(entry.__file__).resolve())],
                             Path('/private/tmp/u-asv-inert'), 8)
            pool.assert_not_called()

    def test_exact_admission_command_checked_before_pool_metadata(self):
        root = entry.ROOT; workspace = Path('/private/tmp/u-asv-inert')
        argv = entry.child_argv('/private/tmp/inert-plan', 'a' * 64, workspace)
        paths = {Path(dispatch.__file__), root / 'tests/manual.py', root / 'tests/shared_io_pool.py',
                 root / 'tests/shared_cpu_pool.py', root / 'tests/shared_process_owner.py',
                 root / 'bench/sync/ownership.py', Path(entry.__file__)}
        pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        import time
        admission = dict(state='ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB', target=entry.TARGET,
            command=argv, workspace=str(workspace), cpu_credits=8,
            io_manifest_sha256='f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636',
            start_deadline_unix=time.time() + 60, execution_source_sha256=pins)
        sentinel = object()
        with patch('shared_io_pool.read_manifest', return_value=admission), \
             patch('shared_io_pool.GlobalPool.read', return_value=sentinel) as pool, \
             patch.object(boundary, 'checked_plan', return_value=dict(workspace=str(workspace))), \
             patch.object(boundary, 'current_sources', return_value={}):
            result = dispatch.checked_io_request(dict(path='/inert/admission', sha256='a' * 64),
                                                entry.TARGET, argv, workspace, 8)
            self.assertIs(result[0], sentinel)
            altered = list(argv); altered[-1] = '/private/tmp/u-asv-other'
            admission['command'] = altered
            with self.assertRaises(ValueError):
                dispatch.checked_io_request(dict(path='/inert/admission', sha256='a' * 64),
                                            entry.TARGET, altered, workspace, 8)
            self.assertEqual(pool.call_count, 1)

    def worker_fixture(self):
        workspace = '/private/tmp/u-asv-inert'
        contract = dict(workspace=workspace, interpreter=dict(sha256='a' * 64),
            binaries={label: dict(path='/inert/' + label, sha256='a' * 64) for label in ('stock', 'ox')},
            tool=dict(path='/inert/sdk', sha256='a' * 64), source={}, execution_source_sha256={})
        args = SimpleNamespace(workspace=workspace, plan='/inert/plan', plan_sha256='b' * 64)
        return args, contract

    def test_inherited_guard_precedes_artifact_hash_and_native_kernel(self):
        args, contract = self.worker_fixture()
        events = []
        def guard(*a, **kw): events.append('guard'); raise ValueError('original inherited FD refusal')
        with patch.object(entry, 'read_document', return_value={}), \
             patch.object(entry, 'artifact_sha', return_value='a' * 64) as artifact, \
             patch.object(shared_binding, 'verify', side_effect=guard), \
             patch.object(worker, 'execute') as execute:
            with self.assertRaisesRegex(ValueError, 'inherited FD refusal'): entry.worker_entry(args, contract)
            self.assertEqual(events, ['guard'])
            execute.assert_not_called()
            self.assertEqual(artifact.call_count, 1)  # START metadata only.

    def test_guarded_worker_reaches_kernel_only_after_artifact_checks(self):
        args, contract = self.worker_fixture(); start = dict(original_inert_start=True)
        with patch.object(entry, 'read_document', return_value=start), \
             patch.object(entry, 'artifact_sha', return_value='a' * 64) as artifact, \
             patch.object(shared_binding, 'verify') as verify, \
             patch.object(worker, 'execute', return_value=dict(original_inert_result=True)) as execute:
            self.assertEqual(entry.worker_entry(args, contract), dict(original_inert_result=True))
            self.assertEqual(artifact.call_count, 5)  # START + interpreter + two binaries + SDK.
            self.assertEqual(verify.call_args.kwargs['target'], entry.TARGET)
            self.assertEqual(execute.call_args.args[1], Path(args.workspace))


if __name__ == '__main__': unittest.main()
