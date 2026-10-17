"""Finite disposable-pool controls; never opens the canonical pool."""
import fcntl
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from shared_cpu_pool import Pool, Lease, UnresolvedOwnership, close_descriptors, authorized_unison_tokens


class PoolControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unison-disposable-tokens-')
        self.path = Path(self.temp.name)
        self.path.chmod(0o700)
        identities = []
        for index in range(18):
            target = self.path / ('cpu-%02d.lock' % index)
            target.touch(mode=0o600)
            info = target.stat()
            identities.append((info.st_dev, info.st_ino))
        info = self.path.stat()
        self.pool = Pool(str(self.path), info.st_dev, info.st_ino, tuple(identities), 'disposable')

    def tearDown(self):
        self.temp.cleanup()

    def release(self, lease):
        lease.close_after_verified_settlement(owner_reaped=True, groups_settled=True,
                                              external_children_settled=True)

    def test_distinct_description_contention_and_release(self):
        first = self.pool.try_acquire((0, 1))
        self.assertIsNotNone(first)
        try:
            self.assertIsNone(self.pool.try_acquire((0, 1)))
        finally:
            self.release(first)
        second = self.pool.try_acquire((0, 1))
        self.assertIsNotNone(second)
        self.release(second)

    def test_late_contention_rolls_back_earlier_tokens(self):
        late = self.pool.try_acquire((7,))
        try:
            self.assertIsNone(self.pool.try_acquire(tuple(range(8))))
            earlier = self.pool.try_acquire(tuple(range(7)))
            self.assertIsNotNone(earlier)
            self.release(earlier)
        finally:
            self.release(late)

    def test_unknown_settlement_retains_locks(self):
        lease = self.pool.try_acquire((0,))
        try:
            with self.assertRaises(UnresolvedOwnership):
                lease.close_after_verified_settlement(owner_reaped=True, groups_settled=False,
                                                      external_children_settled=True)
            self.assertIsNone(self.pool.try_acquire((0,)))
        finally:
            self.release(lease)

    def test_partial_close_unknown_never_retries_number(self):
        calls = []
        def uncertain(fd):
            calls.append(fd)
            if fd == 11:
                raise OSError('synthetic indeterminate close')
        with patch('shared_cpu_pool.os.close', uncertain):
            with self.assertRaises(UnresolvedOwnership) as caught:
                close_descriptors([10, 11, 12])
        self.assertEqual(calls, [12, 11])
        self.assertEqual(caught.exception.retained_fds, (10,))
        self.assertEqual(caught.exception.uncertain_fd, 11)

    def test_directory_close_failure_retains_successful_set(self):
        real_close = os.close
        directory_fd = []
        real_open = os.open
        def track_open(path, flags, *args, **kwargs):
            fd = real_open(path, flags, *args, **kwargs)
            if str(path) == str(self.path):
                directory_fd.append(fd)
            return fd
        def fail_directory(fd):
            if fd in directory_fd:
                raise OSError('synthetic directory close uncertainty')
            real_close(fd)
        with patch('shared_cpu_pool.os.open', track_open), patch('shared_cpu_pool.os.close', fail_directory):
            with self.assertRaises(UnresolvedOwnership) as caught:
                self.pool.try_acquire((0, 1))
        retained = caught.exception.retained_fds
        try:
            self.assertEqual(len(retained), 2)
            self.assertIsNone(self.pool.try_acquire((0, 1)))
        finally:
            # Synthetic failure is known not to have closed this test's FD.
            for fd in retained + tuple(directory_fd):
                real_close(fd)

    def test_inode_replacement_refused(self):
        target = self.path / 'cpu-00.lock'
        target.rename(self.path / 'old-token')
        target.touch(mode=0o600)
        with self.assertRaises(ValueError):
            self.pool.try_acquire((0,))

    def test_combined_refusal_and_directory_close_remains_unresolved(self):
        real_close = os.close
        attempts = []
        directory = []
        real_open = os.open
        def opened(path, flags, *args, **kwargs):
            fd = real_open(path, flags, *args, **kwargs)
            if str(path) == str(self.path): directory.append(fd)
            return fd
        def closed(fd):
            attempts.append(fd)
            if fd in directory: raise OSError('original directory close uncertainty')
            real_close(fd)
        with patch('shared_cpu_pool.os.open', side_effect=opened), \
             patch('shared_cpu_pool.os.close', side_effect=closed), \
             patch.object(Pool, '_token_bound', side_effect=ValueError('original token refusal')):
            with self.assertRaises(UnresolvedOwnership) as caught: self.pool.try_acquire((0,))
        try:
            self.assertIsInstance(caught.exception.original_failure, ValueError)
            self.assertEqual(caught.exception.uncertain_closes[0]['fd'], directory[0])
            self.assertIsNotNone(caught.exception.uncertain_closes[0]['observed_before_close'])
            self.assertEqual(attempts.count(directory[0]), 1)
        finally: real_close(directory[0])  # Injected refusal explicitly left it open.

    def test_rollback_and_directory_close_preserve_both_uncertain_identities(self):
        real_close, real_open = os.close, os.open
        opened_fds, attempts = [], []
        def opened(path, flags, *args, **kwargs):
            fd = real_open(path, flags, *args, **kwargs); opened_fds.append(fd); return fd
        def closed(fd):
            attempts.append(fd); raise OSError('original modeled close uncertainty')
        with patch('shared_cpu_pool.os.open', side_effect=opened), \
             patch('shared_cpu_pool.os.close', side_effect=closed), \
             patch.object(Pool, '_token_bound', side_effect=ValueError('original token refusal')):
            with self.assertRaises(UnresolvedOwnership) as caught: self.pool.try_acquire((0,))
        try:
            identities = caught.exception.uncertain_closes
            self.assertEqual({r['fd'] for r in identities}, set(opened_fds))
            self.assertTrue(all(r['observed_before_close'] is not None for r in identities))
            self.assertEqual(len(attempts), len(set(attempts)))
        finally:
            for fd in opened_fds: real_close(fd)  # Test double closed none.

    def test_invalid_indexes_refused(self):
        for indexes in [(), (True,), (1, 0), (0, 0), (18,)]:
            with self.subTest(indexes=indexes), self.assertRaises(ValueError):
                self.pool.try_acquire(indexes)

    def test_unpinned_policy_cannot_authorize_caller_tokens(self):
        with self.assertRaises(ValueError):
            authorized_unison_tokens(b'{"version":3,"tokens":[8,9]}')

    def test_failed_receipt_write_still_enters_retained_owner(self):
        from shared_process_owner import retain_after_record
        class RetainedForTest(BaseException):
            pass
        def disk_failure():
            raise OSError('synthetic full disk')
        with patch('shared_process_owner.retain_forever', side_effect=RetainedForTest) as retain:
            with self.assertRaises(RetainedForTest):
                retain_after_record(disk_failure)
            retain.assert_called_once_with()

    def test_inherited_description_keeps_lock_after_parent_close(self):
        lease = self.pool.try_acquire((0,))
        read_ready, write_ready = os.pipe()
        child = None
        try:
            code = ('import os,sys; fd=int(sys.argv[1]); ready=int(sys.argv[2]); '
                    'os.fstat(fd); os.write(ready,b"R"); os.close(ready); '
                    'assert sys.stdin.buffer.read(1)==b"X"; os.close(fd)')
            child = subprocess.Popen([sys.executable, '-B', '-c', code,
                                      str(lease.fds[0]), str(write_ready)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, pass_fds=lease.fds + (write_ready,))
            os.close(write_ready)
            write_ready = None
            import select
            self.assertTrue(select.select([read_ready], [], [], 5)[0])
            self.assertEqual(os.read(read_ready, 1), b'R')
            # Deliberate disposable-pool experiment, NOT production release:
            # closing this parent's copy must not unlock the inherited copy.
            os.close(lease.fds[0])
            lease.closed = True
            self.assertIsNone(self.pool.try_acquire((0,)))
            stdout, stderr = child.communicate(b'X', timeout=5)
            self.assertEqual((child.returncode, stdout, stderr), (0, b'', b''))
            again = self.pool.try_acquire((0,))
            self.assertIsNotNone(again)
            self.release(again)
        finally:
            if child is not None and child.returncode is None:
                child.kill()
                child.communicate(timeout=5)
            os.close(read_ready)
            if write_ready is not None:
                os.close(write_ready)
            if not lease.closed:
                self.release(lease)


if __name__ == '__main__':
    unittest.main()
