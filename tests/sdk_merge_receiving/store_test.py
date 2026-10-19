"""Original tiny private JSON records and injected pre-close failures only."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from shared_io_pool import UnresolvedIOOwnership
from sdk_merge_receiving.store import Store

class Metadata(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='unison-merge-metadata-')
        self.root=Path(self.temporary.name).resolve()/'records';self.root.mkdir(mode=0o700)
        native=self.root.stat();self.store=Store(str(self.root),dict(device=native.st_dev,inode=native.st_ino))
    def tearDown(self):
        if not self.store.closed:self.store.close()
        self.temporary.cleanup()

    def test_durable_record_is_one_use_and_independently_read_by_hash(self):
        record=self.store.write('INTENT-0.json',dict(index=0,command=['original']))
        self.assertEqual(self.store.read_json(record['name'],expected_sha256=record['sha256']),
                         dict(index=0,command=['original']))
        self.assertEqual(hashlib.sha256(self.store.read(record['name'])).hexdigest(),record['sha256'])
        self.assertEqual((self.root/record['name']).stat().st_mode & 0o777,0o600)
        with self.assertRaises(FileExistsError):self.store.write(record['name'],dict(forged=True))
        with self.assertRaises(ValueError):self.store.read(record['name'],expected_sha256='0'*64)

    def test_name_substitution_during_publication_cannot_return_a_false_pin(self):
        real_fsync=os.fsync;replaced=[]
        def replace_at_sync(fd):
            if fd!=self.store.fd and not replaced:
                replaced.append(True)
                (self.root/'RACE.json').rename(self.root/'displaced.json')
                replacement=os.open(self.root/'RACE.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                try:os.write(replacement,b'{"substituted":true}\n')
                finally:os.close(replacement)
            return real_fsync(fd)
        with patch('os.fsync',side_effect=replace_at_sync):
            with self.assertRaises(ValueError):self.store.write('RACE.json',dict(original=True))
        self.assertTrue((self.root/'displaced.json').exists())
        self.assertEqual((self.root/'RACE.json').read_bytes(),b'{"substituted":true}\n')

    def test_path_escape_and_replaced_directory_refuse_before_creation(self):
        for name in ('../escape','/absolute','.','..','a/b','a'*97):
            with self.assertRaises(ValueError):self.store.write(name,{})
        self.root.rename(self.root.with_name('original-records'))
        self.root.mkdir(mode=0o700)
        with self.assertRaises(ValueError):self.store.write('REFUSED.json',{})
        self.assertFalse((self.root/'REFUSED.json').exists())
        self.assertFalse((self.root.with_name('original-records')/'REFUSED.json').exists())

    def test_links_modes_and_nonregular_inputs_are_not_metadata(self):
        self.store.write('record.json',dict(original=True))
        os.symlink('record.json',self.root/'link.json')
        with self.assertRaises(OSError):self.store.read('link.json')
        os.link(self.root/'record.json',self.root/'hard.json')
        with self.assertRaises(ValueError):self.store.read('record.json')
        os.unlink(self.root/'hard.json');os.chmod(self.root/'record.json',0o644)
        with self.assertRaises(ValueError):self.store.read('record.json')
        os.mkfifo(self.root/'fifo.json',0o600)
        with self.assertRaises(ValueError):self.store.read('fifo.json')

    def test_combined_write_close_failure_retains_cause_directory_and_uncertain_file(self):
        original=OSError('injected write before syscall');closing=OSError('injected close before syscall')
        attempts=[]
        def fail(fd):attempts.append(fd);raise closing
        with patch('os.write',side_effect=original),patch('os.close',side_effect=fail):
            with self.assertRaises(UnresolvedIOOwnership) as caught:self.store.write('PARTIAL.json',{})
        error=caught.exception
        self.assertIs(error.original_failure,original);self.assertIs(error.close_failure,closing)
        self.assertEqual(attempts,list(error.uncertain_fds))
        self.assertEqual(error.retained_fds,(self.store.fd,))
        self.assertIs(error.metadata_store,self.store)
        # The injected function never called the OS close. The test fixture,
        # unlike a real uncertain caller, knows the descriptor was untouched.
        os.close(attempts[0])
        self.assertTrue((self.root/'PARTIAL.json').exists())

    def test_directory_close_uncertainty_is_consumed_once_without_numeric_retry(self):
        attempts=[]
        def fail(fd):attempts.append(fd);raise OSError('injected before OS close')
        with patch('os.close',side_effect=fail):
            with self.assertRaises(UnresolvedIOOwnership) as caught:self.store.close()
        self.assertEqual(caught.exception.uncertain_fds,(self.store.fd,))
        self.assertNotIn(self.store.fd,caught.exception.retained_fds)
        self.assertIs(caught.exception.metadata_store,self.store)
        with self.assertRaises(ValueError):self.store.close()
        self.assertEqual(attempts,[self.store.fd])
        # No actual close syscall ran in the mock: release the known fixture.
        os.close(self.store.fd)

    def test_nonfinite_or_oversized_data_never_creates_a_record(self):
        for value in (dict(x=float('nan')),dict(x='x'*(2*1048576))):
            with self.assertRaises(ValueError):self.store.write('REFUSED.json',value)
        self.assertFalse((self.root/'REFUSED.json').exists())

if __name__=='__main__':unittest.main()
