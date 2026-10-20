"""Disposable EX_GLOBAL controls; never reads/opens canonical IO files."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import shared_io_pool as io
from shared_cpu_pool import Pool, UnresolvedOwnership


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unison-disposable-io-')
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.directory = self.root / 'pool'
        self.directory.mkdir(mode=0o700)
        self.barrier = self.directory / 'all-devices.lock'
        self.barrier.touch(mode=0o600)
        def ident(path):
            s = path.stat()
            return {'device': s.st_dev, 'inode': s.st_ino, 'uid': s.st_uid,
                    'mode': s.st_mode & 0o777, 'nlink': s.st_nlink}
        self.value = {'schema': 'firstpair-physical-io-pool/1',
             'state': 'PROVISIONED_SINGLE_BARRIER_NOT_RUNTIME_QUALIFIED',
             'namespace': str(self.directory), 'storageDomain': 'disposable-host-domain',
             'directoryIdentity': ident(self.directory),
             'barrier': {'name': 'all-devices.lock', 'path': str(self.barrier),
                         'identity': ident(self.barrier)},
             'physicalLanes': [], 'topologyQualified': False,
             'permittedClaimMode': 'EXCLUSIVE_GLOBAL_BARRIER_ONLY_UNTIL_PINNED_SUCCESSOR',
             'lifecycle': dict(openExistingOnly=True, nonblocking=True, closeOnly=True,
                lockUnForbidden=True, partialBundleRollbackBeforeWait=True,
                unknownSettlementRetainsOwner=True, recreateMissing=False)}
        self.manifest = self.root / 'manifest.json'
        self.save()
        self.pool = io.GlobalPool.read(self.manifest, self.digest)

    def save(self):
        self.manifest.write_text(json.dumps(self.value))
        self.digest = hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_two_descriptions_contend_then_reacquire(self):
        first = self.pool.try_acquire()
        self.assertIsNone(self.pool.try_acquire())
        io.close_unstarted(first)
        second = self.pool.try_acquire()
        io.close_unstarted(second)

    def test_independent_child_description_contends_then_acquires(self):
        program = ('import sys; from shared_io_pool import GlobalPool,close_unstarted; '
                   'p=GlobalPool.read(sys.argv[1],sys.argv[2]); l=p.try_acquire(); '
                   'print("BUSY" if l is None else "ACQUIRED",flush=True); '
                   'close_unstarted(l) if l is not None else None')
        def probe():
            child = subprocess.run([sys.executable, '-c', program,
                         str(self.manifest), self.digest],
                         env=dict(os.environ, PYTHONPATH=str(Path(__file__).parent)),
                         capture_output=True, text=True, timeout=3)
            self.assertEqual(child.returncode, 0, child.stderr)
            return child.stdout.strip()
        first = self.pool.try_acquire()
        try:
            self.assertEqual(probe(), 'BUSY')
        finally:
            io.close_unstarted(first)
        self.assertEqual(probe(), 'ACQUIRED')

    def test_inherited_fd_outlives_parent_copy(self):
        first = self.pool.try_acquire()
        # Fixed inert child owns inherited description, no media operations.
        child = subprocess.Popen([sys.executable, '-c',
            'import sys; print("READY",flush=True); sys.stdin.buffer.read(1)'],
            pass_fds=first.fds, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            self.assertEqual(child.stdout.readline(), b'READY\n')
            # Parent copy closes; child ownership is retained by this test.
            # Explicit transfer: READY was actually received from the live
            # inherited holder. Close parent copies without claiming child
            # settlement; retain child handle until actual communicate/wait.
            first.closed = True
            io.close_descriptors(first.fds)
            print(json.dumps({'event': 'PARENT_COPY_TRANSFER', 'holder_pid': child.pid,
                  'ready_received': True, 'parent_copies_closed': True,
                  'child_settled': False}), flush=True)
            self.assertIsNone(self.pool.try_acquire())
        finally:
            child.communicate(b'x', timeout=3)
            self.assertEqual(child.returncode, 0)
            print(json.dumps({'event': 'HOLDER_ACTUAL_WAIT', 'pid': child.pid,
                              'exit': child.returncode}), flush=True)
        second = self.pool.try_acquire()
        io.close_unstarted(second)

    def test_replaced_or_symlink_barrier_refused(self):
        self.barrier.rename(self.directory / 'old')
        self.barrier.touch(mode=0o600)
        with self.assertRaises(ValueError):
            self.pool.try_acquire()
        self.barrier.unlink()
        self.barrier.symlink_to(self.directory / 'old')
        with self.assertRaises(OSError):
            self.pool.try_acquire()

    def test_hardlink_refused(self):
        os.link(self.barrier, self.root / 'alias')
        with self.assertRaises(ValueError):
            self.pool.try_acquire()

    def test_missing_never_recreated(self):
        self.barrier.unlink()
        with self.assertRaises(FileNotFoundError):
            self.pool.try_acquire()
        self.assertFalse(self.barrier.exists())

    def test_manifest_pins_and_claim_mode_refused(self):
        with self.assertRaises(ValueError):
            io.GlobalPool.read(self.manifest, '0' * 64)
        self.value['physicalLanes'] = ['invented']
        self.save()
        with self.assertRaises(ValueError):
            io.GlobalPool.read(self.manifest, self.digest)

    def test_cpu_contention_rolls_back_io_and_earlier_cpu(self):
        directory = self.root / 'cpu'
        directory.mkdir(mode=0o700)
        ids = []
        for n in range(18):
            p = directory / ('cpu-%02d.lock' % n)
            p.touch(mode=0o600)
            s = p.stat(); ids.append((s.st_dev, s.st_ino))
        s = directory.stat()
        cpu = Pool(str(directory), s.st_dev, s.st_ino, tuple(ids), 'disposable')
        late = cpu.try_acquire((7,))
        self.assertIsNone(io.try_io_cpu_bundle(self.pool, cpu, tuple(range(8))))
        probe = self.pool.try_acquire()
        io.close_unstarted(probe)
        early = cpu.try_acquire(tuple(range(7)))
        io.close_unstarted(early)
        io.close_unstarted(late)

    def test_unknown_settlement_keeps_barrier(self):
        first = self.pool.try_acquire()
        with self.assertRaises(UnresolvedOwnership):
            first.close_after_verified_settlement(owner_reaped=True, groups_settled=False,
                                                  external_children_settled=True)
        self.assertIsNone(self.pool.try_acquire())
        io.close_unstarted(first)

    def test_directory_close_failure_retains_acquired_barrier(self):
        original = os.close
        directory_fd = []
        original_bound = self.pool._directory_bound
        def remember(fd):
            directory_fd[:] = [fd]
            original_bound(fd)
        def fail(fd):
            if directory_fd and fd == directory_fd[0]:
                raise OSError('injected pre-close uncertainty; no kernel close executed')
            original(fd)
        with patch.object(io.GlobalPool, '_directory_bound', lambda pool, fd: remember(fd)), \
             patch.object(io.os, 'close', side_effect=fail):
            with self.assertRaises(UnresolvedOwnership) as raised:
                self.pool.try_acquire()
        self.assertEqual(len(raised.exception.retained_fds), 1)
        self.assertIsNone(self.pool.try_acquire())
        # Test injector proves no close happened; resolve retained descriptions
        # once with original close. This is not retry of a real uncertain close.
        for fd in raised.exception.retained_fds:
            original(fd)
        original(directory_fd[0])

    def test_refusal_plus_directory_close_carries_unresolved(self):
        original_close = os.close
        original_failure = ValueError('injected ordinary identity refusal')
        seen = {}
        def refuse(pool, fd):
            seen['directory'] = fd
            seen['identity'] = io.descriptor_observation(fd, 'io_directory')
            raise original_failure
        def fail_close(fd):
            if fd == seen.get('directory'):
                raise OSError('injected directory close before kernel close')
            return original_close(fd)
        with patch.object(io.GlobalPool, '_directory_bound', refuse), \
             patch.object(io.os, 'close', side_effect=fail_close):
            with self.assertRaises(io.UnresolvedIOOwnership) as raised:
                self.pool.try_acquire()
        error = raised.exception
        self.assertIs(error.original_failure, original_failure)
        self.assertIs(error.__cause__, original_failure)
        self.assertEqual(error.retained_fds, ())
        self.assertEqual(error.uncertain_fds, (seen['directory'],))
        self.assertEqual(error.uncertain_closes[0], seen['identity'])
        # Injector explicitly executed NO kernel close; this is resolution
        # using injector proof, never retry of a genuinely unknown close.
        original_close(seen['directory'])

    def test_rollback_and_directory_close_both_uncertainties_preserved(self):
        original_close = os.close
        original_bound = self.pool._barrier_bound
        seen = {'calls': 0, 'close_calls': []}
        refusal = ValueError('injected post-lock identity refusal')
        def refuse_after_lock(pool, directory, fd):
            seen.update(directory=directory, barrier=fd)
            seen['calls'] += 1
            original_bound(directory, fd)
            if seen['calls'] == 2:
                raise refusal
        def fail_close(fd):
            if fd in (seen.get('directory'), seen.get('barrier')):
                seen['close_calls'].append(fd)
                raise OSError('injected close before kernel close')
            return original_close(fd)
        with patch.object(io.GlobalPool, '_barrier_bound', refuse_after_lock), \
             patch.object(io.os, 'close', side_effect=fail_close):
            with self.assertRaises(io.UnresolvedIOOwnership) as raised:
                self.pool.try_acquire()
        error = raised.exception
        self.assertEqual(error.uncertain_fds, (seen['barrier'], seen['directory']))
        self.assertIsNone(error.uncertain_fd)  # no misleading singular close
        self.assertEqual(seen['close_calls'], [seen['barrier'], seen['directory']])
        self.assertEqual([x['role'] for x in error.uncertain_closes],
                         ['io_barrier', 'io_directory'])
        self.assertEqual(error.uncertain_closes[0]['observed_before_close']['inode'],
                         self.value['barrier']['identity']['inode'])
        self.assertEqual(error.uncertain_closes[1]['observed_before_close']['inode'],
                         self.value['directoryIdentity']['inode'])
        self.assertIs(error.original_failure.__cause__, refusal)
        self.assertIs(error.__cause__, error.original_failure)
        # Both fake failures executed no closes; verify retained actual lock.
        self.assertIsNone(self.pool.try_acquire())
        original_close(seen['barrier'])
        original_close(seen['directory'])


class ManifestBounds(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-owned-json-bounds-')
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'original-metadata.json'

    def payload(self,size):
        prefix=b'{"original":true}'
        raw=prefix+b' '*(size-len(prefix))
        self.path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def test_default_and_explicit_boundaries(self):
        digest=self.payload(65536)
        self.assertEqual(io.read_manifest(self.path,digest),{'original':True})
        digest=self.payload(65537)
        with patch.object(io.os,'read',side_effect=AssertionError('oversize read')):
            with self.assertRaisesRegex(ValueError,'bounded owned IO manifest'):
                io.read_manifest(self.path,digest)
        self.assertEqual(io.read_manifest(self.path,digest,maximum_bytes=262144),{'original':True})
        digest=self.payload(262144)
        self.assertEqual(io.read_manifest(self.path,digest,maximum_bytes=262144),{'original':True})
        digest=self.payload(262145)
        with patch.object(io.os,'read',side_effect=AssertionError('oversize read')):
            with self.assertRaisesRegex(ValueError,'bounded owned IO manifest'):
                io.read_manifest(self.path,digest,maximum_bytes=262144)

    def test_invalid_limit_before_open(self):
        for limit in (True,0,-1,262145,'262144'):
            with self.subTest(limit=limit),patch.object(io.os,'open') as opening:
                with self.assertRaisesRegex(ValueError,'reader limit'):
                    io.read_manifest(self.path,'0'*64,maximum_bytes=limit)
                opening.assert_not_called()

    def test_large_reader_still_enforces_digest_and_nlink(self):
        digest=self.payload(65537)
        with self.assertRaisesRegex(ValueError,'SHA differs'):
            io.read_manifest(self.path,'0'*64,maximum_bytes=262144)
        os.link(self.path,self.path.with_name('disposable-link'))
        with self.assertRaisesRegex(ValueError,'bounded owned IO manifest'):
            io.read_manifest(self.path,digest,maximum_bytes=262144)


if __name__ == '__main__':
    unittest.main()
