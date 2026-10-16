"""Original tiny-byte result/tampering controls; no retained photo access."""
import copy
import os
import struct
from pathlib import Path
import tempfile
import time
import unittest
from private_maker_shape_test import fixture
from private_maker_slice import read_source,stamp
from private_maker_audit import audit


class Audit(unittest.TestCase):
    def result(self,data=None):
        data=fixture() if data is None else data
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'tiny';path.write_bytes(data);path.chmod(0o400)
            geometry=dict(payload_offset=0,payload_length=len(data),original_offset=1000,
                          byte_order='little',ifd_offset=0,max_requested_read_bytes=3078)
            result=read_source(dict(path=str(path),identity=stamp(os.lstat(path))),geometry,
                               deadline=time.monotonic()+5)
        return result,geometry
    def test_candidate_and_declines(self):
        for data in (fixture(),fixture(kind=99),b'\0'*128):
            result,g=self.result(data);proof=audit(result,g)
            self.assertFalse(proof['semantic_eligibility']);self.assertTrue(proof['metadata_consistent'])
    def test_ranges_totals_and_claims(self):
        result,g=self.result()
        mutations=[lambda r:r.update(semantic_eligibility=True),
            lambda r:r.update(requested_read_bytes=True),lambda r:r.update(fd_closure_proved_by_return=1),
            lambda r:r.update(extra='hidden bytes'),lambda r:r['read_ranges'][1].update(offset=500),
            lambda r:r['read_ranges'][1].update(received=15),
            lambda r:r['read_ranges'].append(dict(r['read_ranges'][0]))]
        for change in mutations:
            r=copy.deepcopy(result);change(r)
            with self.assertRaises(ValueError):audit(r,g)
    def test_shape_arithmetic_and_inline_secrecy(self):
        result,g=self.result()
        for key,value in [('count',9),('type',True),('value_bytes',9),('out_of_line',1),
                          ('payload_relative_offset',99),('declared_extent_within_payload',False),
                          ('private_pointer_semantics_verified',True),('value',123)]:
            r=copy.deepcopy(result);r['shape']['entries'][0][key]=value
            # An altered relative offset may be internally consistent; use an impossible value.
            if key=='payload_relative_offset':r['shape']['entries'][0][key]=2**32
            with self.subTest(key=key),self.assertRaises(ValueError):audit(r,g)
    def test_decline_cannot_hide_shape_or_arbitrary_text(self):
        result,g=self.result(fixture(kind=99))
        for key,value in [('shape',{}),('reason','private bytes'),('reason',[]),('outcome','SUCCESS')]:
            r=copy.deepcopy(result);r[key]=value
            with self.assertRaises(ValueError):audit(r,g)
    def test_exact_maximum_table_is_accepted_without_pointed_reads(self):
        data=struct.pack('<H',256)+b''.join(struct.pack('<HHII',tag,7,8,1100)
            for tag in range(256))+struct.pack('<I',0)
        result,g=self.result(data)
        self.assertEqual(result['requested_read_bytes'],3078)
        self.assertEqual(len(result['read_ranges']),2)
        self.assertTrue(audit(result,g)['candidate_shape'])


if __name__=='__main__':unittest.main()
