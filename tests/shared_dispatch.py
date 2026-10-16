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


def run(target, argv, output, credits):
    require(target in TARGETS, 'target has no shared owner scope')
    require(type(credits) is int and 1 <= credits <= 8, 'shared credit count differs')
    require_ownership_support()
    authorized = authorized_unison_tokens(POLICY.read_bytes())
    indexes = authorized[:credits]
    pool = Pool.read(MANIFEST, MANIFEST_SHA)
    try:
        lease = pool.try_acquire(indexes)
    except UnresolvedOwnership as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'stage': 'acquisition',
              'retained_fd_count': len(error.retained_fds), 'uncertain_fd': error.uncertain_fd}))
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
        if target == 'dng-private-framing':
            sources.extend([ROOT / 'src/dngPrivateData.ml', ROOT / 'src/dngPrivateData.mli',
                            ROOT / 'tests/dng_private_data/test.ml'])
        if target == 'shared-io-controls':
            sources.append(ROOT / 'tests/shared_io_plan.py')
        pins = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in set(sources)}
        with (output / 'SHARED-STDOUT.txt').open('x') as stdout, (output / 'SHARED-STDERR.txt').open('x') as stderr:
            child = OwnedGroup(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stdout,
                               stderr=stderr, pass_fds=lease.fds)
            write(output / 'SHARED-START.json', {'owner_pid': os.getpid(), 'child_pid': child.pid,
                  'target': target, 'command': argv, 'token_indexes': list(indexes),
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
        write(output / 'SHARED-CLOSED.json', {'child': closure, 'tokens_closed': True,
                                            'source_pins_unchanged': source_unchanged,
                                            'parent_terminal': 'collect separately from owning tool'})
        return 124 if closure['timed_out'] else 3 if not source_unchanged else closure['returncode']
    except BaseException as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'child_pid': child.pid if child else None}))
