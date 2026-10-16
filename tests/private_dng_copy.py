"""One fixed private-copy control; requires a separately pinned IO admission.

No default invocation touches a DNG. Worker and owner stay in one owned group;
no SDK, compiler, renderer or independent server is dispatched.
"""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'bench/sync'))
from shared_cpu_pool import Pool, authorized_unison_tokens, require, unique_object
from shared_process_owner import require_ownership_support, settle, retain_after_record
from ownership import OwnedGroup


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and before.st_uid == os.getuid() and before.st_size <= 262144,
                'bounded owned regular metadata required')
        raw = bytearray()
        while len(raw) <= 262144:
            block = os.read(fd, min(8192, 262145 - len(raw)))
            if not block:
                break
            raw.extend(block)
        require(identity(before) == identity(os.fstat(fd)) == identity(os.lstat(path))
                and len(raw) == before.st_size, 'metadata changed during read')
        return json.loads(raw, object_pairs_hook=unique_object)
    finally:
        os.close(fd)


def write(path, value):
    with open(path, 'x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def identity(s):
    return {k: getattr(s, k) for k in ('st_dev', 'st_ino', 'st_size',
                                      'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_nlink')}


def source_check(plan, fd):
    expected = plan['source']['identity']
    require(identity(os.fstat(fd)) == expected == identity(os.lstat(plan['source']['path'])),
            'source FIVE/mode/nlink changed')


def preflight(plan):
    require(plan['schema'] == 'unison-private-dng-copy-plan/2', 'plan schema differs')
    for pin in plan['execution_pins'] + plan['ancestry_receipts']:
        p = Path(pin['path'])
        require(p.stat().st_size == pin['bytes'] and sha(p) == pin['sha256'],
                'metadata/source pin changed: ' + str(p))
    spec = importlib.util.spec_from_file_location('private_copy_inspector_driver',
                  ROOT / 'tools/semantic-inspect/run.py')
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    for item in plan['inspectors']:
        driver.checked_inspector(item['receipt'])


def worker(plan_path, admission_path):
    plan = load(plan_path)
    preflight(plan)
    check_admission(plan_path, admission_path)
    workspace = Path(plan['destination']['workspace'])
    source = plan['source']['path']
    target = Path(plan['destination']['clone'])
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        source_check(plan, fd)
        require(os.statvfs(workspace).f_bavail * os.statvfs(workspace).f_frsize >= 1073741824,
                'private destination reserve below 1GiB')
        require(not target.exists() and not target.is_symlink(), 'destination already exists')
        libc = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
        clone = libc.clonefile
        clone.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        clone.restype = ctypes.c_int
        if clone(os.fsencode(source), os.fsencode(target), 0):
            raise OSError(ctypes.get_errno(), 'clonefile failed; no copy fallback')
        source_check(plan, fd)
        resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1048576, 16 * 1048576))
        d = target.lstat()
        require(stat.S_ISREG(d.st_mode) and d.st_nlink == 1 and d.st_size == plan['source']['identity']['st_size']
                and (d.st_dev, d.st_ino) != (os.fstat(fd).st_dev, os.fstat(fd).st_ino),
                'clone type/length/distinct inode differs')
        digest = hashlib.sha256()
        counted = 0
        with target.open('rb') as f:
            while True:
                block = f.read(1048576)
                if not block:
                    break
                counted += len(block)
                require(counted <= d.st_size, 'clone grew while hashing')
                digest.update(block)
        require(counted == d.st_size and digest.hexdigest() == plan['source']['historical_sha256'],
                'clone historical SHA differs')
        source_check(plan, fd)
        baseline = identity(target.lstat())
        results = []
        for item in plan['inspectors']:
            source_check(plan, fd)
            require(identity(target.lstat()) == baseline, 'clone changed before inspector')
            command = [sys.executable, str(ROOT / 'tools/semantic-inspect/run.py'),
                       '--use-build', item['receipt'], '--', '--profile',
                       'org.firstpair.dng-xmp/1', str(target)]
            with (workspace / (item['label'] + '-stdout.json')).open('x') as out, \
                 (workspace / (item['label'] + '-stderr.txt')).open('x') as err:
                child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
                # No independent session: outer retained leader owns timeout cleanup.
                try:
                    code = child.wait(timeout=180)
                except subprocess.TimeoutExpired:
                    raise RuntimeError('inspector deadline; outer group cleanup required')
            results.append({'label': item['label'], 'pid': child.pid, 'wait_exit': code})
            require(code == 0, 'inspector failed; no retry')
            require(identity(target.lstat()) == baseline, 'clone changed after inspector')
            source_check(plan, fd)
        reports = [load(workspace / (i['label'] + '-stdout.json')) for i in plan['inspectors']]
        require(reports[0] == reports[1], 'stock/Ox observations differ')
        preflight(plan)
        write(workspace / 'RESULT.json', {'state': 'PRIVATE_CLONE_AND_TWO_OBSERVATIONS_PASSED',
              'clone_identity': baseline, 'clone_sha256': digest.hexdigest(),
              'destination_hash_read_bytes': counted, 'inspectors': results,
              'source_final': identity(os.fstat(fd)),
              'read_budget_scope': plan['budgets']['read_budget_scope'],
              'no_sdk_or_receiving': True})
    finally:
        os.close(fd)


def check_admission(plan_path, admission_path):
    admission = load(admission_path)
    require(admission['state'] == 'ROOT_ADMITTED_ONE_PRIVATE_DNG_IO_CONTROL'
            and admission['plan_sha256'] == sha(plan_path)
            and admission['command'] == [sys.executable, str(Path(__file__).resolve()),
                                         '--plan', plan_path, '--io-admission', str(Path(admission_path).resolve())]
            and admission['start_deadline_unix'] > time.time()
            and admission['accepts_uninstrumented_inspector_logical_read_budget'] is True,
            'fresh exact IO admission required')


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        check_admission(str(Path(sys.argv[2]).resolve()), sys.argv[3])
        worker(sys.argv[2], sys.argv[3])
        return 0
    require(len(sys.argv) == 5 and sys.argv[1] == '--plan' and sys.argv[3] == '--io-admission',
            'usage: private_dng_copy.py --plan PLAN --io-admission PINNED_ROOT_RECEIPT')
    plan_path = str(Path(sys.argv[2]).resolve())
    plan = load(plan_path)
    preflight(plan)
    require_ownership_support()
    check_admission(plan_path, sys.argv[4])
    # Admission comes from the coordinated local owner, never an untrusted peer.
    workspace = Path(plan['destination']['workspace'])
    require(not workspace.exists() and not workspace.is_symlink(), 'workspace already used; no replay')
    os.umask(0o077)
    workspace.mkdir(mode=0o700)
    photo = ROOT.parent / 'photo/preview-generator'
    tokens = authorized_unison_tokens((photo / 'SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json').read_bytes())
    pool = Pool.read(photo / 'engine-v3-native-control/ROOT-CPU-POOL-v1.json',
                    '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
    lease = None
    child = None
    try:
        lease = pool.try_acquire(tokens)
        require(lease is not None, 'CPU set contended; no payload dispatched')
        with (workspace / 'OWNER-STDOUT.txt').open('x') as out, (workspace / 'OWNER-STDERR.txt').open('x') as err:
            child = OwnedGroup([sys.executable, str(Path(__file__).resolve()), '--worker', plan_path, str(Path(sys.argv[4]).resolve())],
                               cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err, pass_fds=lease.fds)
            write(workspace / 'START.json', {'owner_pid': os.getpid(), 'worker_pid': child.pid,
                  'plan_sha256': sha(plan_path), 'io_admission_sha256': sha(sys.argv[4]),
                  'cpu_tokens': list(tokens), 'unix': time.time()})
            closure = settle(child, time.monotonic() + 600)
        preflight(plan)
        lease.close_after_verified_settlement(owner_reaped=True, groups_settled=True,
                                              external_children_settled=True)
        lease = None
        write(workspace / 'AGGREGATE-CLOSED.json', {'child': closure, 'cpu_tokens_closed': True,
              'parent_terminal': 'collect separately from owner tool',
              'result_present': (workspace / 'RESULT.json').exists()})
        return closure['returncode'] if not closure['timed_out'] else 124
    except BaseException as error:
        if lease is not None or child is not None and not child.reaped:
            retain_after_record(lambda: write(workspace / 'OWNERSHIP-UNRESOLVED.json',
                                {'owner_pid': os.getpid(), 'error': repr(error)}))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
