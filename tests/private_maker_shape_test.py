"""Original candidate-shape fixtures only; no retained input or media reads."""
import struct
import unittest
from private_maker_shape import inspect,MAX_READ


def fixture(order='little',value=1100,kind=7,count=8,next_ifd=0):
    endian='<' if order=='little' else '>'
    return (struct.pack(endian+'H',1)+struct.pack(endian+'HHII',42,kind,count,value)
            +struct.pack(endian+'I',next_ifd)).ljust(128,b'\0')


class Shape(unittest.TestCase):
    def call(self,data,**kw):
        reads=[]
        def read(offset,count):reads.append((offset,count));return data[offset:offset+count]
        result=inspect(read,length=len(data),original_offset=1000,byte_order=kw.pop('byte_order','little'),**kw)
        self.assertEqual(sum(n for _,n in reads),result['requested_read_bytes'])
        self.assertLessEqual(result['requested_read_bytes'],MAX_READ)
        return result,reads
    def test_both_orders_explicit_base_no_pointed_reads(self):
        for order in ('little','big'):
            result,reads=self.call(fixture(order),byte_order=order)
            self.assertEqual(reads,[(0,2),(2,16)])
            self.assertEqual(result['entries'][0]['payload_relative_offset'],100)
            self.assertTrue(result['entries'][0]['declared_extent_within_payload'])
            for name in ('maker_format_recognized','private_reference_closure_proved','semantic_eligibility','inline_values_disclosed','pointed_values_read'):
                self.assertIs(result[name],False)
    def test_external_extents_stay_external_not_safe(self):
        for value in (999,1127,2**32-1):
            result,_=self.call(fixture(value=value))
            self.assertFalse(result['entries'][0]['declared_extent_within_payload'])
            self.assertFalse(result['semantic_eligibility'])
    def test_inline_long_and_next_pointer_not_proven(self):
        result,_=self.call(fixture(kind=4,count=1,value=0x12345678,next_ifd=1100))
        row=result['entries'][0]
        self.assertIsNone(row['payload_relative_offset']);self.assertNotIn('value',row)
        self.assertFalse(row['private_pointer_semantics_verified']);self.assertFalse(result['next_ifd_zero'])
    def test_counts_types_short_reads_and_duplicate_refuse(self):
        for data in (b'\0\0'+b'\0'*16,b'\x01\x01'+b'\0'*16,fixture(kind=99),fixture()[:10]):
            with self.assertRaises(ValueError):self.call(data)
        row=fixture()[2:14];data=struct.pack('<H',2)+row+row+b'\0'*4
        with self.assertRaises(ValueError):self.call(data)
    def test_metadata_alias_and_offsets_refuse_without_read(self):
        for changes in (dict(length=True),dict(original_offset=True),dict(original_offset=2**32),dict(ifd_offset=-1),dict(byte_order='native')):
            values=dict(length=128,original_offset=1000,byte_order='little');values.update(changes)
            with self.assertRaises(ValueError):inspect(lambda *a:self.fail('invalid metadata read'),**values)


if __name__=='__main__':unittest.main()
