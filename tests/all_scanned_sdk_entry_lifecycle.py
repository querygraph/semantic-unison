"""Actual inherited-FD refusals using disposable inner pools; zero SDK/media."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tests/camera_sdk_concurrency')]
import all_scanned_sdk_entry as entry
import all_scanned_sdk_boundary as boundary
import all_scanned_sdk_worker as worker
import shared_dispatch as dispatch
from sdk_host_matrix import shared_binding
from camera_sdk_concurrency.lifecycle import Lease
from camera_sdk_concurrency.persistence import save
from sdk_multifile.clone import stamp

HERE = Path(__file__).resolve()


def command(path, digest, workspace):
    return [sys.executable, str(HERE), '--worker', '--plan', str(path),
            '--plan-sha256', digest, '--workspace', str(workspace)]


def worker_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true', required=True)
    for name in ('plan', 'plan-sha256', 'workspace'):
        parser.add_argument('--' + name, required=True)
    return parser.parse_args(argv)


def child():
    args = worker_arguments(sys.argv[1:])
    path, digest, workspace = Path(args.plan), args.plan_sha256, Path(args.workspace)
    contract = boundary.read_document(path, digest)
    real_sha = entry.artifact_sha
    def artifact(path):
        return 'a' * 64 if str(path) == boundary.PYTHON or str(path).startswith('/inert/') else real_sha(path)
    def refuse(*args, **kwargs):
        (workspace / 'BOUNDARY-REACHED').write_text('guard accepted; SDK and clone intentionally unstarted\n')
        raise ValueError('original pre-SDK worker refusal')
    with patch.object(entry, 'child_argv', side_effect=command), \
         patch.object(entry, 'artifact_sha', side_effect=artifact), \
         patch.object(shared_binding, 'inventory', return_value=tuple(tuple(x) for x in contract['disposable_inventory'])), \
         patch.object(worker, 'execute', side_effect=refuse):
        try:
            entry.worker_entry(SimpleNamespace(plan=str(path), plan_sha256=digest, workspace=str(workspace)), contract)
        except ValueError as error:
            save(workspace, dict(schema='unison-all-scanned-sdk-worker/1', complete=False,
                phase='PREPARING_NO_CALL', cases=[], invocations=[], failure=str(error)))
            return 7
    raise AssertionError('worker must refuse before SDK')


def controls():
    root = Path(tempfile.mkdtemp(prefix='u-asv-boundary-', dir='/private/tmp'))
    cases = []
    for count in (8, 7):
        workspace = root / str(count); workspace.mkdir(mode=0o700)
        for name in ('cpu', 'io'): (workspace / name).mkdir(mode=0o700)
        cpu, io = Lease(workspace / 'cpu', count), Lease(workspace / 'io', 1)
        source = workspace / 'metadata-only-inert-source'; source.write_bytes(b'original tiny fixture'); source.chmod(0o400)
        contract = dict(workspace=str(workspace), interpreter=dict(sha256='a' * 64),
            binaries={label: dict(path='/inert/' + label, sha256='a' * 64) for label in ('stock', 'ox')},
            tool=dict(path='/inert/sdk', sha256='a' * 64), execution_source_sha256={},
            source=dict(path=str(source), identity=stamp(source.lstat())),
            disposable_inventory=[(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in cpu.fds + io.fds])
        path = workspace / 'plan.json'; path.write_text(json.dumps(contract) + '\n')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        class CPU:
            def try_acquire(self, indexes): return cpu
        class IO:
            def try_acquire(self): return io
        with patch.object(dispatch.Pool, 'read', return_value=CPU()), \
             patch.object(dispatch, 'checked_io_request', return_value=(IO(), time.time() + 60)), \
             patch.object(boundary, 'checked_plan', return_value=contract):
            code = dispatch.run(entry.TARGET, command(path, digest, workspace), workspace, 8,
                                io_admission=dict(path='/inert/disposable-admission', sha256='0' * 64))
        closed = boundary.read_document(workspace / 'SHARED-CLOSED.json', entry.artifact_sha(workspace / 'SHARED-CLOSED.json'))
        audit = boundary.read_document(workspace / 'SHARED-SERVER-AUDIT.json', entry.artifact_sha(workspace / 'SHARED-SERVER-AUDIT.json'))
        result = boundary.read_document(workspace / 'RESULT.json', entry.artifact_sha(workspace / 'RESULT.json'))
        assert code == 7 and cpu.closed and io.closed and closed['child']['reaped']
        assert closed['child']['returncode'] == 7 and closed['child']['other_group_members_absent_before_reap']
        assert (workspace / 'BOUNDARY-REACHED').exists() == (count == 8)
        assert result['failure'] == ('original pre-SDK worker refusal' if count == 8 else 'exact9inherited descriptions required')
        assert audit['functional_status'] == 'FAILED' and audit['attempted_cli_invocations'] == 0
        assert stamp(source.lstat()) == contract['source']['identity']
        cases.append(dict(inherited_descriptors=count + 1, boundary_reached=count == 8,
                          workspace=str(workspace), child=closed['child'], parent_audit=audit))
    summary = dict(cases=cases, scope='Two actual Python children/inherited-FD guards and dispatcher known-zero-call audit. Inner pools, admission, artifact hashes, inventory and entry argv explicitly doubled; zero SDK/clone/canonical IO/retained media.')
    save(root, summary)
    print(json.dumps(dict(workspace=str(root),cases=2,actual_python_children=2,SDK_calls=0)), flush=True)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--worker']: raise SystemExit(child())
    if sys.argv[1:] == ['--controls']: controls()
    else: raise ValueError('explicit --controls or owned --worker only')
