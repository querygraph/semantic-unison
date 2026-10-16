"""Tiny original slice/fence controls, no retained camera source access."""
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from private_maker_shape_test import fixture
from private_maker_slice import read_source,stamp,InputChanged,MAX_READ
from shared_cpu_pool import UnresolvedOwnership


class Slice(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-maker-slice-')
        self.path=Path(self.temp.name)/'original';self.path.write_bytes(b'PREFIX'+fixture()+b'TRAILER')
        self.path.chmod(0o400)
        self.source=dict(path=str(self.path),identity=stamp(os.lstat(self.path)))
        self.geometry=dict(payload_offset=6,payload_length=128,original_offset=1000,
                           byte_order='little',ifd_offset=0,max_requested_read_bytes=MAX_READ)
    def tearDown(self):self.temp.cleanup()
    def call(self):return read_source(self.source,self.geometry,deadline=time.monotonic()+5)
    def test_exact_slice_budget_and_unchanged_source(self):
        before=self.path.read_bytes();result=self.call()
        self.assertEqual(result['outcome'],'CANDIDATE_SHAPE')
        self.assertEqual(result['read_ranges'],[dict(offset=6,requested=2,received=2),dict(offset=8,requested=16,received=16)])
        self.assertEqual(result['requested_read_bytes'],18)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(stamp(os.lstat(self.path)),self.source['identity'])
        self.assertFalse(result['semantic_eligibility']);self.assertFalse(result['raw_payload_disclosed'])
    def test_changed_source_refuses_before_payload(self):
        self.source['identity']['st_ino']+=1
        with patch('private_maker_slice.os.pread') as read:
            with self.assertRaises(InputChanged):self.call()
            read.assert_not_called()
    def test_mutation_during_read_is_not_an_unsupported_layout(self):
        original=os.pread
        def changed(*a):
            raw=original(*a);self.source['identity']['st_size']+=1;return raw
        with patch('private_maker_slice.os.pread',side_effect=changed):
            with self.assertRaises(InputChanged):self.call()
    def test_invalid_geometry_never_opens_payload(self):
        for key,value in [('payload_offset',True),('payload_offset',100000),('max_requested_read_bytes',MAX_READ+1),('ifd_offset',-1)]:
            old=self.geometry[key];self.geometry[key]=value
            with self.subTest(key=key),patch('private_maker_slice.os.open') as opened:
                with self.assertRaises(ValueError):self.call()
                opened.assert_not_called()
            self.geometry[key]=old
    def test_unknown_close_overrides_success_and_is_not_retried(self):
        observed=os.lstat(self.path);calls=[]
        def fail(fd):calls.append(fd);raise OSError('injected close uncertainty')
        with patch('private_maker_slice.os.open',return_value=900),\
             patch('private_maker_slice.os.fstat',return_value=observed),\
             patch('private_maker_slice.os.pread',side_effect=lambda fd,n,offset:self.path.read_bytes()[offset:offset+n]),\
             patch('os.close',side_effect=fail):
            with self.assertRaises(UnresolvedOwnership) as caught:self.call()
        self.assertEqual(calls,[900]);self.assertEqual(caught.exception.uncertain_closes[0]['fd'],900)


if __name__=='__main__':unittest.main()
