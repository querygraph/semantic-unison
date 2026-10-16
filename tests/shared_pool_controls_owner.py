"""One finite disposable-token suite under the standing canonical Unison lane.

This qualifies token primitives, not the general build/sync dispatcher. Unknown
settlement deliberately retains this owner and its descriptors for inspection.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench' / 'sync'))
from ownership import OwnedGroup
from shared_cpu_pool import Pool, authorized_unison_tokens

POLICY = Path('/Users/alexy/src/photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json')
MANIFEST = Path('/Users/alexy/src/photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json')
MANIFEST_SHA = '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd'


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    if len(sys.argv) != 2:
        raise SystemExit('one fresh absolute output directory required')
    output = Path(sys.argv[1])
    if not output.is_absolute():
        raise SystemExit('absolute output required')
    indexes = authorized_unison_tokens(POLICY.read_bytes())
    pool = Pool.read(MANIFEST, MANIFEST_SHA)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    lease = pool.try_acquire(indexes)
    if lease is None:
        write(output / 'NOT-STARTED.json', {'state': 'CONTENDED_ALL_PARTIAL_DESCRIPTORS_CLOSED'})
        return 2
    child = None
    try:
        sources = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in (Path(__file__), ROOT / 'tests/shared_cpu_pool.py',
                                ROOT / 'tests/shared_cpu_pool_test.py', ROOT / 'bench/sync/ownership.py')}
        with (output / 'stdout.txt').open('x') as stdout, (output / 'stderr.txt').open('x') as stderr:
            child = OwnedGroup([sys.executable, '-B', str(ROOT / 'tests/shared_cpu_pool_test.py')],
                               cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                               pass_fds=lease.fds)
            write(output / 'START.json', {'owner_pid': os.getpid(), 'child_pid': child.pid,
                                         'token_indexes': list(indexes), 'cpu_credits': 8,
                                         'workload': 'eight disposable-pool controls; no Adobe/SDK/compiler',
                                         'sources': sources, 'unix': time.time()})
            receipt, _ = child.finish(timeout=45, grace=1)
        if (not receipt['reaped'] or not receipt['group_cleanup_before_leader_reap']
                or receipt['observation_error'] is not None):
            raise RuntimeError('child settlement not established')
        # This fixed suite starts no children or external process groups.
        lease.close_after_verified_settlement(owner_reaped=True, groups_settled=True,
                                              external_children_settled=True)
        write(output / 'CLOSED.json', {'child': receipt, 'tokens_closed': True,
                                     'passed': receipt['returncode'] == 0,
                                     'dispatcher_integration_qualified': False,
                                     'parent_tool_terminal': 'collect separately from owning tool'})
        return receipt['returncode']
    except BaseException as error:
        write(output / 'OWNERSHIP-RETAINED.json', {'error': repr(error), 'owner_pid': os.getpid(),
                                                'child_pid': child.pid if child else None})
        # Do not turn an exception or deadline into token release. A retaining
        # owner needs an explicitly reviewed recovery, not automatic retry.
        while True:
            time.sleep(1)


if __name__ == '__main__':
    raise SystemExit(main())
