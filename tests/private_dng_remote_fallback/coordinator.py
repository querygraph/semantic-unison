"""Prepared aggregate owner for one explicitly admitted synthetic remote job.

No live transport is authorized by this source. Unknown worker/remote/FD
settlement retains this coordinator; it never kills an aggregate containing
unproved separately-sessioned native owners. Not a timing benchmark.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tests'))
sys.path.insert(0, str(ROOT/'bench/sync'))
from shared_cpu_pool import Pool, UnresolvedOwnership, authorized_unison_tokens
from shared_io_pool import (GlobalPool, CANONICAL_MANIFEST, CANONICAL_SHA256,
                            read_manifest, try_io_cpu_bundle, close_unstarted)
from shared_process_owner import require_ownership_support, retain_after_record, settle
from shared_dispatch import POLICY, MANIFEST, MANIFEST_SHA
from ownership import OwnedGroup
from audit import audit, PAIRS, require
from ledger import audit_directory, exclusive_json

PARAMETERS = {'file_bytes': 1048576, 'files': 1, 'client_workers': 2,
              'server_workers': 2, 'owner_credits': 2, 'total_grant': 8,
              'tag': 50740, 'adobe_validation': 'off'}
SOURCES = (
    'tests/private_dng_remote_fallback/coordinator.py',
    'tests/private_dng_remote_fallback/case.py',
    'tests/private_dng_remote_fallback/audit.py',
    'tests/private_dng_remote_fallback/ledger.py',
    'tests/private_dng_local_clone/run.py',
    'tests/shared_cpu_pool.py', 'tests/shared_io_pool.py',
    'tests/shared_process_owner.py', 'tests/shared_dispatch.py',
    'bench/sync/run.py', 'bench/sync/measure.py', 'bench/sync/ownership.py',
    'bench/sync/proxy.py', 'bench/sync/launcher.py', 'bench/sync/fixtures.py',
    'bench/sync/read_stats.py', 'bench/sync/partitions.py', 'bench/sync/batch_audit.py')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_pins():
    return {str(ROOT/name): digest(ROOT/name) for name in SOURCES}


def checked_plan(plan):
    require(plan['schema'] == 'unison-private-dng-remote-owner/1' and
            plan['parameters'] == PARAMETERS and
            all(type(plan['parameters'][k]) is type(v) for k, v in PARAMETERS.items()) and
            type(plan['worker_seconds']) is int and plan['worker_seconds'] == 480,
            'fixed remote job scope differs')
    require(plan['execution_source_sha256'] == source_pins(), 'remote owner source pins differ')
    workspace = Path(plan['workspace'])
    require(workspace.parent == Path('/private/tmp') and
            workspace.name.startswith('u-rf-') and len(workspace.name) <= 24 and
            len(workspace.name) > 5, 'fresh short private workspace required')
    require(set(plan['binaries']) == {'stock', 'ox'}, 'exact two compiler binaries required')
    for label, item in plan['binaries'].items():
        require(item['label'] == label and Path(item['path']).is_absolute() and
                len(item['sha256']) == 64 and all(c in '0123456789abcdef' for c in item['sha256']),
                'pinned binary record malformed')
    require(plan['io_manifest_sha256'] == CANONICAL_SHA256 and
            plan['cpu_manifest_sha256'] == MANIFEST_SHA, 'canonical resource manifest differs')
    return workspace


def check_binaries(plan):
    for item in plan['binaries'].values():
        require(digest(item['path']) == item['sha256'], 'pinned executable changed')


def remote_settlement(workspace):
    """Consume trusted ledgers only AFTER no further worker dispatch is possible."""
    rows = []
    for client, server in sorted(PAIRS):
        directory = Path(workspace)/(client+'-'+server)
        if directory.exists():
            require(directory.is_dir() and not directory.is_symlink(), 'case directory replaced')
            rows.extend(dict(pair=[client, server], **row) for row in audit_directory(directory))
    return rows


def functional_evidence(result, workspace):
    summary = audit(result)
    for case in result['cases']:
        directory = Path(workspace)/('-'.join(case['compiler_pair']))
        for stage in ('seed', 'update', 'noop'):
            require(case['calls'][stage] == json.loads(
                (directory/(stage+'-OUTCOME.json')).read_text()),
                'functional result differs from saved call outcome')
    return summary


def worker(packet_path):
    packet = json.loads(Path(packet_path).read_text())
    plan = packet['plan']; workspace = checked_plan(plan)
    require(Path(packet_path) == workspace/'WORKER-PACKET.json', 'internal packet path differs')
    # Internal entrypoint: only the live parent-created packet and inherited
    # descriptors qualify. This is cooperative ownership, not a same-UID sandbox.
    require(type(packet['parent_pid']) is int and os.getppid() == packet['parent_pid'],
            'internal worker parent differs')
    require(len(packet['inherited_fds']) == 9 and
            len({r['fd'] for r in packet['inherited_fds']}) == 9, 'IO+eight CPU descriptions required')
    for row in packet['inherited_fds']:
        s = os.fstat(row['fd'])
        require((s.st_dev, s.st_ino) == (row['device'], row['inode']),
                'inherited grant descriptor identity differs')
    require(time.monotonic() < packet['deadline_monotonic'], 'worker dispatch deadline passed')
    result = {'schema': 'unison-private-dng-remote-fallback/1', 'complete': False,
              'parameters': PARAMETERS, 'cases': []}
    failure = original_error = None
    try:
        from case import execute_case
        for client, server in sorted(PAIRS):
            result['cases'].append(execute_case(workspace/(client+'-'+server),
                plan['binaries'][client], plan['binaries'][server],
                deadline_monotonic=packet['deadline_monotonic']))
        result['complete'] = True
        result['audit'] = audit(result)
    except BaseException as error:
        # Retain the exception/traceback itself until settlement is proven:
        # it may hold the last live measure_invocation owner objects.
        original_error = error
        failure = repr(error)
        result['complete'] = False
        result['failure'] = failure
    try:
        rows = remote_settlement(workspace)
        exclusive_json(workspace/'WORKER-RESULT.json', result)
        exclusive_json(workspace/'REMOTE-SETTLED.json', {'calls': rows,
            'worker_finished_starting_calls': True, 'functional_pass': failure is None})
    except BaseException as error:
        # Includes receipt-write failure: never drop inherited grants merely
        # because the reporting path failed after a potentially started call.
        retain_after_record(lambda: exclusive_json(workspace/'WORKER-UNKNOWN.json',
            {'error': repr(error), 'original_failure': failure, 'pid': os.getpid(),
             'original_exception_retained': original_error is not None}))
    return 0 if failure is None else 1


def owner(plan_path, admission_path, admission_sha256):
    require_ownership_support()
    plan_raw = Path(plan_path).read_bytes(); plan = json.loads(plan_raw)
    workspace = checked_plan(plan)
    admission = read_manifest(admission_path, admission_sha256)
    require(admission['state'] == 'ROOT_ADMITTED_ONE_SYNTHETIC_REMOTE_FALLBACK' and
            admission['plan_sha256'] == hashlib.sha256(plan_raw).hexdigest() and
            admission['workspace'] == str(workspace) and
            admission['launch_argv_without_admission_sha256'] == [sys.executable,
                str(Path(__file__)), '--plan', str(plan_path), '--admission', str(admission_path)] and
            admission['start_deadline_unix'] > time.time(), 'fresh exact remote admission required')
    # Exclusive creation is the one-use gate. No retry or alternate output.
    workspace.mkdir(mode=0o700)
    exclusive_json(workspace/'ATTEMPT.json', {'owner_pid': os.getpid(),
        'plan_sha256': hashlib.sha256(plan_raw).hexdigest(), 'admission_sha256': admission_sha256})
    io = cpu = child = None
    closed = False
    try:
        indexes = authorized_unison_tokens(POLICY.read_bytes())
        pool = Pool.read(MANIFEST, MANIFEST_SHA)
        io_pool = GlobalPool.read(CANONICAL_MANIFEST, CANONICAL_SHA256)
        bundle = try_io_cpu_bundle(io_pool, pool, indexes)
        if bundle is None:
            exclusive_json(workspace/'NOT-STARTED.json', {'state': 'CONTENDED_PARTIALS_CLOSED'})
            return 2
        io, cpu = bundle
        checked_plan(plan); check_binaries(plan)
        require(read_manifest(admission_path, admission_sha256) == admission and
                Path(plan_path).read_bytes() == plan_raw and
                admission['start_deadline_unix'] > time.time(),
                'plan/admission changed or expired before child entry')
        fds = list(io.fds)+list(cpu.fds)
        # Stop new work before the owner's observation deadline, reserving
        # forty seconds for an already-started bounded call to settle itself.
        observation_deadline = time.monotonic()+480
        deadline = observation_deadline-40
        packet = {'plan': plan, 'parent_pid': os.getpid(), 'deadline_monotonic': deadline,
                  'inherited_fds': [dict(fd=fd, device=os.fstat(fd).st_dev,
                                        inode=os.fstat(fd).st_ino) for fd in fds]}
        packet_path = workspace/'WORKER-PACKET.json'; exclusive_json(packet_path, packet)
        with (workspace/'STDOUT.txt').open('x') as stdout, (workspace/'STDERR.txt').open('x') as stderr:
            child = OwnedGroup([sys.executable, str(Path(__file__)), '--worker', str(packet_path)],
                strict_group_settlement=True, pass_fds=tuple(fds), stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr)
        exclusive_json(workspace/'START.json', {'owner_pid': os.getpid(), 'worker_pid': child.pid,
            'admission_sha256': admission_sha256, 'cpu_indexes': list(indexes), 'io_mode': 'EX_GLOBAL',
            'call_start_deadline_monotonic': deadline,
            'owner_observation_deadline_monotonic': observation_deadline})
        # Do NOT send a group timeout signal: worker owns separate-session
        # client/supervisor children. Missing worker closure retains ownership.
        require(child.await_terminal(max(0, observation_deadline-time.monotonic())),
                'worker deadline reached with remote owners potentially live')
        rows = remote_settlement(workspace)
        recorded = json.loads((workspace/'REMOTE-SETTLED.json').read_text())
        require(recorded['worker_finished_starting_calls'] is True and recorded['calls'] == rows,
                'worker independent remote settlement binding differs')
        worker_closed = settle(child, time.monotonic()+5)
        result = json.loads((workspace/'WORKER-RESULT.json').read_text())
        passed = worker_closed['returncode'] == 0
        if passed:
            functional_evidence(result, workspace)
        require(source_pins() == plan['execution_source_sha256'], 'execution source changed')
        cpu.close_after_verified_settlement(owner_reaped=worker_closed['reaped'],
            groups_settled=worker_closed['other_group_members_absent_before_reap'],
            external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=worker_closed['reaped'],
            groups_settled=worker_closed['other_group_members_absent_before_reap'],
            external_children_settled=True)
        closed = True
        exclusive_json(workspace/'AGGREGATE-CLOSED.json', {'worker': worker_closed, 'remote_calls': rows,
            'cpu_closed': True, 'io_closed': True, 'functional_pass': passed,
            'parent_terminal': 'must be collected separately from owning tool'})
        return 0 if passed else 1
    except BaseException as error:
        if closed:
            raise
        if child is None and not isinstance(error, UnresolvedOwnership):
            # No worker has entered. Known rollback is not a child-settled claim.
            try:
                if cpu is not None: close_unstarted(cpu)
                if io is not None: close_unstarted(io)
            except BaseException as close_error:
                error = close_error
            else:
                exclusive_json(workspace/'NOT-STARTED.json', {'error': repr(error), 'known_rollback': True})
                return 2
        retain_after_record(lambda: exclusive_json(workspace/'OWNER-UNKNOWN.json',
            {'error': repr(error), 'owner_pid': os.getpid(), 'worker_pid': child.pid if child else None,
             'known_cpu_fds': list(cpu.fds) if cpu and not cpu.closed else [],
             'known_io_fds': list(io.fds) if io and not io.closed else [],
             'retained_fds': list(getattr(error, 'retained_fds', ())),
             'uncertain_closes': list(getattr(error, 'uncertain_closes', ())),
             'uncertain_fd': getattr(error, 'uncertain_fd', None)}))


def interrupted(number, frame):
    raise InterruptedError('coordinator signal '+str(number))


def main():
    os.umask(0o077)
    signal.signal(signal.SIGINT, interrupted); signal.signal(signal.SIGTERM, interrupted)
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        return worker(sys.argv[2])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--admission', required=True)
    parser.add_argument('--admission-sha256', required=True)
    args = parser.parse_args()
    return owner(args.plan, args.admission, args.admission_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
