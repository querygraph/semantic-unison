"""Canonical token owner for fixed Adobe-free build/parser entry points.

Loopback sync has separately-sessioned server owners. Its exact functional
matrix/server/pump proofs must pass before the runner is reaped or tokens close.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from shared_cpu_pool import Pool, authorized_unison_tokens, require, UnresolvedOwnership
from shared_process_owner import settle, retain_after_record, require_ownership_support

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from ownership import OwnedGroup

POLICY = ROOT.parent / 'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
MANIFEST = ROOT.parent / 'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'
MANIFEST_SHA = '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd'
TARGETS = {'stock-build', 'ox-build', 'read-parser', 'group-parser',
           'aggregate-preflight', 'host-interface', 'shared-entrypoints', 'shared-sync-controls',
           'sync-functional', 'inspect-stock', 'inspect-ox', 'inspect-file', 'inspector-reuse-controls',
           'shared-io-controls', 'dng-private-framing', 'private-dng-local-clone'}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def checked_io_request(request, target, argv, output, credits):
    """Read admission metadata only; this does not acquire IO/CPU locks."""
    from shared_io_pool import GlobalPool, read_manifest, CANONICAL_MANIFEST, CANONICAL_SHA256
    require(target in ('inspect-file', 'private-dng-local-clone'),
            'IO successor only supports complete local single-group jobs')
    require(isinstance(request, dict) and set(request) == {'path', 'sha256'},
            'explicit pinned IO admission required')
    value = read_manifest(request['path'], request['sha256'])
    require(value['state'] == 'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB'
            and value['target'] == target and value['command'] == argv
            and value['workspace'] == str(output) and value['cpu_credits'] == credits
            and value['io_manifest_sha256'] == CANONICAL_SHA256
            and value['start_deadline_unix'] > time.time(),
            'fresh exact shared-dispatch IO job admission required')
    source_paths = {Path(__file__), ROOT / 'tests/manual.py', ROOT / 'tests/shared_io_pool.py',
                    ROOT / 'tests/shared_cpu_pool.py', ROOT / 'tests/shared_process_owner.py',
                    ROOT / 'bench/sync/ownership.py', Path(argv[1])}
    expected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    require(value['execution_source_sha256'] == expected, 'exact IO execution source set changed')
    return GlobalPool.read(CANONICAL_MANIFEST, CANONICAL_SHA256), value['start_deadline_unix']


def run(target, argv, output, credits, *, io_admission=None):
    require(target in TARGETS, 'target has no shared owner scope')
    require(type(credits) is int and 1 <= credits <= 8, 'shared credit count differs')
    require_ownership_support()
    authorized = authorized_unison_tokens(POLICY.read_bytes())
    indexes = authorized[:credits]
    pool = Pool.read(MANIFEST, MANIFEST_SHA)
    io_lease = None
    io_pool, io_deadline = (checked_io_request(io_admission, target, argv, output, credits)
                            if io_admission is not None else (None, None))
    if io_pool is not None:
        write(output / 'SHARED-IO-ATTEMPT.json', {'admission': io_admission, 'target': target,
              'owner_pid': os.getpid(), 'command': argv})
    try:
        if io_pool is None:
            lease = pool.try_acquire(indexes)
        else:
            from shared_io_pool import try_io_cpu_bundle
            bundle = try_io_cpu_bundle(io_pool, pool, indexes)
            if bundle is None:
                lease = None
            else:
                io_lease, lease = bundle
    except UnresolvedOwnership as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'stage': 'acquisition',
              'retained_fds': list(error.retained_fds), 'uncertain_fd': error.uncertain_fd,
              'uncertain_closes': list(getattr(error, 'uncertain_closes', ()))}))
    if lease is None:
        write(output / 'SHARED-NOT-STARTED.json', {'state': 'CONTENDED_PARTIAL_SET_CLOSED',
                                                'token_indexes': list(indexes)})
        return 2
    child = None
    try:
        sources = [Path(__file__), ROOT / 'tests/manual.py', ROOT / 'tests/shared_cpu_pool.py',
                   ROOT / 'tests/shared_process_owner.py', ROOT / 'bench/sync/ownership.py',
                   Path(argv[1])]
        if target in ('inspect-stock', 'inspect-ox', 'inspect-file',
                      'inspector-reuse-controls', 'shared-entrypoints'):
            sources.append(ROOT / 'tools/semantic-inspect/run.py')
        if target in ('sync-functional', 'shared-sync-controls'):
            sources.extend((ROOT / 'bench/sync').glob('*.py'))
        if io_lease is not None:
            sources.append(ROOT / 'tests/shared_io_pool.py')
        if target == 'dng-private-framing':
            sources.extend([ROOT / 'src/dngPrivateData.ml', ROOT / 'src/dngPrivateData.mli',
                            ROOT / 'tests/dng_private_data/test.ml'])
        if target == 'shared-io-controls':
            sources.append(ROOT / 'tests/shared_io_plan.py')
        pins = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in set(sources)}
        if io_pool is not None:
            # Metadata-only final source/admission check immediately before
            # launch. A known refusal with no child is rollback, not unknown.
            try:
                checked_pool, checked_deadline = checked_io_request(io_admission, target, argv, output, credits)
                require(checked_pool == io_pool and checked_deadline == io_deadline
                        and time.time() < io_deadline, 'IO admission expired or changed before launch')
            except ValueError as refusal:
                from shared_io_pool import close_unstarted
                close_unstarted(lease)
                close_unstarted(io_lease)
                write(output / 'SHARED-NOT-STARTED.json', {'state': 'PRELAUNCH_REFUSAL_KNOWN_CLOSED',
                                                        'error': str(refusal)})
                return 2
        with (output / 'SHARED-STDOUT.txt').open('x') as stdout, (output / 'SHARED-STDERR.txt').open('x') as stderr:
            child = OwnedGroup(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stdout,
                               stderr=stderr, pass_fds=lease.fds + (io_lease.fds if io_lease else ()))
            write(output / 'SHARED-START.json', {'owner_pid': os.getpid(), 'child_pid': child.pid,
                  'target': target, 'command': argv, 'token_indexes': list(indexes),
                  'io_mode': 'EX_GLOBAL' if io_lease is not None else 'NOT_ACQUIRED',
                  'io_admission': io_admission,
                  'cpu_credits': credits, 'unix': time.time(),
                  'sources': pins})
            seconds = 300 if target == 'sync-functional' or target.startswith('inspect-') else 600 if target.endswith('-build') else 60
            if target == 'sync-functional':
                # Separate server sessions retain their own coordinator. Do
                # not kill it on an outer deadline and discard live handles.
                if not child.await_terminal(seconds - 2):
                    raise RuntimeError('shared sync batch deadline; live coordinator retained')
                from shared_audit import audit_shared
                report_path = output / 'RESULT.json'
                info = report_path.lstat()
                import stat
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                        and info.st_uid == os.getuid() and 0 < info.st_size <= 16 * 1048576,
                        'bounded private shared result required')
                raw = report_path.read_bytes()
                after = report_path.lstat()
                require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                        and len(raw) == info.st_size, 'shared result changed')
                external = audit_shared(json.loads(raw))
                write(output / 'SHARED-SERVER-AUDIT.json', external)
                closure = settle(child, time.monotonic() + 2)
            else:
                closure = settle(child, time.monotonic() + seconds)
        source_unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                               for name, digest in pins.items())
        lease.close_after_verified_settlement(owner_reaped=closure['reaped'],
                    groups_settled=closure['other_group_members_absent_before_reap'],
                    external_children_settled=True)
        if io_lease is not None:
            io_lease.close_after_verified_settlement(owner_reaped=closure['reaped'],
                groups_settled=closure['other_group_members_absent_before_reap'],
                external_children_settled=True)
        write(output / 'SHARED-CLOSED.json', {'child': closure, 'tokens_closed': True,
                                            'io_barrier_acquired_and_closed': io_lease is not None,
                                            'source_pins_unchanged': source_unchanged,
                                            'parent_terminal': 'collect separately from owning tool'})
        return 124 if closure['timed_out'] else 3 if not source_unchanged else closure['returncode']
    except BaseException as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'child_pid': child.pid if child else None,
              'retained_io_fds': list(io_lease.fds) if io_lease is not None and not io_lease.closed else [],
              'error_retained_fds': list(getattr(error, 'retained_fds', ())),
              'uncertain_fd': getattr(error, 'uncertain_fd', None),
              'uncertain_closes': list(getattr(error, 'uncertain_closes', ())) }))
