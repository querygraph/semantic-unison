"""Finite lock-only canonical EX_GLOBAL qualification; no media/native access.

Requires a fresh exact Root admission. Parent holds IO+CPU FDs through retained
owned-group settlement. Disposable tests cover inheritance and rollback; this
canonical probe covers real manifest bindings and independent-owner contention.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'bench/sync'))
from shared_cpu_pool import Pool, authorized_unison_tokens, require, UnresolvedOwnership, unique_object
from shared_io_pool import GlobalPool, try_io_cpu_bundle, close_unstarted, CANONICAL_MANIFEST, CANONICAL_SHA256, UnresolvedIOOwnership, descriptor_observation, uncertainty_records
from shared_process_owner import settle, retain_after_record, require_ownership_support
from ownership import OwnedGroup


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as out:
        json.dump(value, out, indent=2)
        out.write('\n')


def pinned_plan(path):
    from shared_io_pool import read_manifest
    # Shared bounded metadata reader requires a supplied SHA. Local plan SHA is
    # authorized by the separately Root-published admission before any locks.
    value = read_manifest(path, digest(path))
    require(value['schema'] == 'firstpair-canonical-io-probe/1', 'probe plan schema differs')
    for pin in value['pins']:
        require(Path(pin['path']).stat().st_size == pin['bytes']
                and digest(pin['path']) == pin['sha256'], 'probe source pin changed')
    return value


def verify_held(io_pool, lease):
    directory = os.open(io_pool.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                        | os.O_NONBLOCK | os.O_CLOEXEC)
    observation = descriptor_observation(directory, 'io_revalidation_directory')
    failure = None
    try:
        io_pool._directory_bound(directory)
        io_pool._barrier_bound(directory, lease.fds[0])
    except BaseException as error:
        failure = error
        raise
    finally:
        try:
            os.close(directory)
        except BaseException as error:
            raise UnresolvedIOOwnership('revalidation directory close unknown',
                retained_fds=lease.fds,
                uncertain_closes=uncertainty_records(failure, {}) + (observation,),
                original_failure=failure, close_failure=error) from (failure or error)


def worker(plan_path, admission_path):
    check_admission(plan_path, admission_path)
    plan = pinned_plan(plan_path)
    output = Path(plan['workspace'])
    # The fixed contender is a new process/description, no session escape,
    # payload access, CPU acquisition or children. Parent still owns full bundle.
    code = ('import sys,json; from shared_io_pool import GlobalPool,close_unstarted; '
            'p=GlobalPool.read(sys.argv[1],sys.argv[2]); x=p.try_acquire(); '
            'print(json.dumps({"busy":x is None}),flush=True); '
            'close_unstarted(x) if x is not None else None; '
            'sys.exit(0 if x is None else 2)')
    with (output / 'CONTENDER-STDOUT.json').open('x') as out, \
         (output / 'CONTENDER-STDERR.txt').open('x') as err:
        child = subprocess.Popen([sys.executable, '-c', code, CANONICAL_MANIFEST,
                                  CANONICAL_SHA256],
                    env=dict(os.environ, PYTHONPATH=str(ROOT / 'tests')),
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        # On timeout, leave child in owned group for outer retained settlement.
        status = child.wait(timeout=10)
    require(status == 0, 'independent fresh description did not contend')
    write(output / 'WORKER-RESULT.json', {'contender_pid': child.pid,
                'actual_wait_exit': status, 'scope': 'fixed no-spawn Python contender only'})


def check_admission(plan_path, admission_path):
    from shared_io_pool import read_manifest
    admission = read_manifest(admission_path, digest(admission_path))
    require(admission['state'] == 'ROOT_ADMITTED_ONE_LOCK_ONLY_CANONICAL_IO_PROBE'
            and admission['plan_sha256'] == digest(plan_path)
            and admission['command'] == [sys.executable, str(Path(__file__).resolve()),
                        '--plan', plan_path, '--admission', str(Path(admission_path).resolve())]
            and time.time() < admission['start_deadline_unix'], 'fresh exact probe admission required')


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        worker(sys.argv[2], sys.argv[3])
        return 0
    require(len(sys.argv) == 5 and sys.argv[1] == '--plan' and sys.argv[3] == '--admission',
            'usage: canonical_io_probe.py --plan PLAN --admission ROOT_RECEIPT')
    require_ownership_support()
    plan_path = str(Path(sys.argv[2]).resolve())
    plan = pinned_plan(plan_path)
    check_admission(plan_path, sys.argv[4])
    output = Path(plan['workspace'])
    os.umask(0o077)
    output.mkdir(mode=0o700)
    photo = ROOT.parent / 'photo/preview-generator'
    indexes = authorized_unison_tokens((photo / 'SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json').read_bytes())
    cpu_pool = Pool.read(photo / 'engine-v3-native-control/ROOT-CPU-POOL-v1.json',
                    '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
    io_pool = GlobalPool.read(CANONICAL_MANIFEST, CANONICAL_SHA256)
    bundle = None
    child = None
    try:
        bundle = try_io_cpu_bundle(io_pool, cpu_pool, indexes)
        if bundle is None:
            write(output / 'NOT-STARTED.json', {'state': 'CONTENDED_KNOWN_PARTIALS_CLOSED'})
            return 2
        io, cpu = bundle
        verify_held(io_pool, io)
        with (output / 'OWNER-STDOUT.txt').open('x') as out, (output / 'OWNER-STDERR.txt').open('x') as err:
            child = OwnedGroup([sys.executable, str(Path(__file__).resolve()), '--worker', plan_path, str(Path(sys.argv[4]).resolve())],
                               cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                               pass_fds=io.fds + cpu.fds)
            write(output / 'START.json', {'owner_pid': os.getpid(), 'group_pid': child.pid,
                 'io_manifest_sha256': CANONICAL_SHA256, 'cpu_indexes': list(indexes),
                 'plan_sha256': digest(plan_path), 'admission_sha256': digest(sys.argv[4])})
            closure = settle(child, time.monotonic() + 60)
        # Parent copies retained full bundle throughout group settlement.
        pinned_plan(plan_path)
        GlobalPool.read(CANONICAL_MANIFEST, CANONICAL_SHA256)
        verify_held(io_pool, io)
        cpu.close_after_verified_settlement(owner_reaped=True, groups_settled=True,
                                             external_children_settled=True)
        close_unstarted(io)
        bundle = None
        require(closure['returncode'] == 0 and not closure['timed_out'], 'probe group failed')
        # Prior copies are closed before new IO→CPU bundle; no CPU→IO inversion.
        bundle = try_io_cpu_bundle(io_pool, cpu_pool, indexes)
        require(bundle is not None, 'fresh post-settlement bundle contended')
        io, cpu = bundle
        verify_held(io_pool, io)
        close_unstarted(cpu)
        close_unstarted(io)
        bundle = None
        write(output / 'AGGREGATE-CLOSED.json', {'state': 'LOCK_ONLY_PROBE_PASSED_CLOSED',
                  'child': closure, 'io_and_cpu_copies_closed': True,
                  'fresh_whole_bundle_reacquired_and_closed': True,
                  'parent_terminal': 'collect actual owner tool terminal separately',
                  'no_payload_native_or_dispatcher_qualification': True})
        return 0
    except BaseException as error:
        if bundle is not None or isinstance(error, UnresolvedOwnership) or child is not None and not child.reaped:
            retain_after_record(lambda: write(output / 'OWNERSHIP-UNRESOLVED.json',
                               {'owner_pid': os.getpid(), 'error': repr(error),
                                'retained_fds': list(getattr(error, 'retained_fds', ())),
                                'uncertain_fd': getattr(error, 'uncertain_fd', None),
                                'uncertain_closes': list(getattr(error, 'uncertain_closes', ())) }))
        write(output / 'FAILED-KNOWN-CLOSED.json', {'error': repr(error)})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
