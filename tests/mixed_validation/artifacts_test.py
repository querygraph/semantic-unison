"""Original tiny artifact and clone controls; no camera/SDK/native UI."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from artifacts import verified_hash,prepare_input,verify_input,verify_sources
from plan_test import fixture
from sdk_multifile.clone import stamp
from shared_cpu_pool import UnresolvedOwnership


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-mixed-artifacts-',dir='/private/tmp')
        self.root=Path(self.temp.name).resolve()
        self.file=self.root/'original.dng';self.file.write_bytes(b'original tiny fixture'*200)
        self.file.chmod(0o644)
        self.item=dict(path=str(self.file),bytes=self.file.stat().st_size,
                       sha256=hashlib.sha256(self.file.read_bytes()).hexdigest())
    def tearDown(self):self.temp.cleanup()
    def plan(self):
        p=fixture();p['workspace']=str(self.root/'workspace')
        p['input']=dict(self.item);p['input_epoch']=stamp(os.lstat(self.file))
        return p

    def test_exact_hash_and_epoch(self):
        epoch=stamp(os.lstat(self.file))
        self.assertEqual(verified_hash(self.item,expected_epoch=epoch),epoch)
        self.assertEqual(stamp(os.lstat(self.file)),epoch)
        bad=dict(epoch,st_ino=epoch['st_ino']+1)
        with self.assertRaises(ValueError):verified_hash(self.item,expected_epoch=bad)

    def test_wrong_hash_size_symlink_refused(self):
        for changed in (dict(self.item,sha256='0'*64),dict(self.item,bytes=self.item['bytes']-1)):
            with self.assertRaises(ValueError):verified_hash(changed)
        link=self.root/'link';link.symlink_to(self.file)
        with self.assertRaises(OSError):verified_hash(dict(self.item,path=str(link)))

    def test_uncertain_close_preserves_identity_and_never_retries(self):
        observed=os.lstat(self.file);calls=[];chunks=[self.file.read_bytes(),b'']
        def fail(fd):calls.append(fd);raise OSError('injected uncertain close')
        with patch('artifacts.os.open',return_value=900),patch('artifacts.os.fstat',return_value=observed),\
             patch('artifacts.os.read',side_effect=lambda *a:chunks.pop(0)),patch('os.close',side_effect=fail):
            with self.assertRaises(UnresolvedOwnership) as caught:verified_hash(self.item)
        self.assertEqual(calls,[900])
        self.assertEqual(caught.exception.uncertain_closes[0]['fd'],900)

    def test_media_cannot_be_execution_inventory(self):
        p=self.plan();p['source_pins']=[dict(self.item)]
        with self.assertRaisesRegex(ValueError,'source media'):verify_sources(p)

    def test_native_tiny_clone_and_post_fences(self):
        p=self.plan();Path(p['workspace']).mkdir(mode=0o700)
        record=prepare_input(p,0)
        self.assertEqual(record['source_payload_read_bytes'],0)
        self.assertEqual(record['backend'],'native-fclonefileat-only')
        self.assertNotEqual(record['clone_identity']['st_ino'],p['input_epoch']['st_ino'])
        verify_input(p,0,record)
        self.assertEqual(stamp(os.lstat(self.file)),p['input_epoch'])
        with self.assertRaises(FileExistsError):prepare_input(p,0)
        candidate=Path(p['workspace'])/'stock/uncompressed.dng'
        candidate.write_bytes(b'changed')
        with self.assertRaises(ValueError):verify_input(p,0,record)


if __name__=='__main__':unittest.main()
