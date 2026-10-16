"""Canonical token owner for fixed Adobe-free build/parser entry points.

Loopback sync has separately-sessioned server owners and is deliberately not
released on this group's closure alone. Its separate proof integration follows.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from shared_cpu_pool import Pool, authorized_unison_tokens, require, UnresolvedOwnership
from shared_process_owner import settle, retain_after_record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from ownership import OwnedGroup

POLICY = ROOT.parent / 'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
MANIFEST = ROOT.parent / 'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'
MANIFEST_SHA = '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd'
TARGETS = {'stock-build', 'ox-build', 'read-parser', 'group-parser',
           'aggregate-preflight', 'host-interface', 'shared-entrypoints'}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def run(target, argv, output, credits):
    require(target in TARGETS, 'shared sync requires separate server/helper settlement integration')
    require(type(credits) is int and 1 <= credits <= 8, 'shared credit count differs')
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
        with (output / 'SHARED-STDOUT.txt').open('x') as stdout, (output / 'SHARED-STDERR.txt').open('x') as stderr:
            child = OwnedGroup(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stdout,
                               stderr=stderr, pass_fds=lease.fds)
            write(output / 'SHARED-START.json', {'owner_pid': os.getpid(), 'child_pid': child.pid,
                  'target': target, 'command': argv, 'token_indexes': list(indexes),
                  'cpu_credits': credits, 'unix': time.time(),
                  'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__), ROOT / 'tests/manual.py',
                                        ROOT / 'tests/shared_cpu_pool.py',
                                        ROOT / 'tests/shared_process_owner.py')}})
            closure = settle(child, time.monotonic() + (600 if target.endswith('-build') else 60))
        lease.close_after_verified_settlement(owner_reaped=closure['reaped'],
                    groups_settled=closure['other_group_members_absent_before_reap'],
                    external_children_settled=True)
        write(output / 'SHARED-CLOSED.json', {'child': closure, 'tokens_closed': True,
                                            'parent_terminal': 'collect separately from owning tool'})
        return 124 if closure['timed_out'] else closure['returncode']
    except BaseException as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'child_pid': child.pid if child else None}))
