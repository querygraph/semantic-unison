import struct,unittest
from sdk_fixture_states import COMPRESSION
from sdk_fixture_states_test import fixture
from sdk_fixture_digest_fault import corrupt_new_raw_digest


def source(codec='uncompressed',little=True):
    data=bytearray(fixture(codec,little));order='<' if little else '>'
    struct.pack_into(order+'H',data,8,5)
    struct.pack_into(order+'HHII',data,58,51111,1,16,1024)
    data[1024:1040]=bytes(range(16))
    return bytes(data)


class DigestFault(unittest.TestCase):
    def test_three_encodings_both_orders_exact_one_bit(self):
        for codec in COMPRESSION:
            for little in (True,False):
                data=source(codec,little);result=corrupt_new_raw_digest(data,codec)
                self.assertEqual([i for i,(a,b) in enumerate(zip(data,result['data'])) if a!=b],[1024])
                self.assertEqual(result['data'][1024]^data[1024],1)
                self.assertFalse(result['actual_sdk_finding_proved'])
                self.assertFalse(result['receiving_rejection_proved'])
    def test_missing_wrong_type_count_and_outside_digest_refuse(self):
        for at,fmt,value in ((58,'H',51112),(60,'H',7),(62,'I',15),(66,'I',4090),(66,'I',8)):
            data=bytearray(source());struct.pack_into('<'+fmt,data,at,value)
            with self.assertRaises(ValueError):corrupt_new_raw_digest(bytes(data),'uncompressed')
    def test_digest_alias_xmp_and_other_primary_extent_refuse(self):
        for offset in (512,600,800):
            data=bytearray(source());struct.pack_into('<I',data,66,offset)
            with self.assertRaises(ValueError):corrupt_new_raw_digest(bytes(data),'uncompressed')
    def test_duplicate_digest_unknown_type_mutable_wrong_codec_refuse(self):
        for at,value in ((10,51111),(12,99)):
            data=bytearray(source());struct.pack_into('<H',data,at,value)
            with self.assertRaises(ValueError):corrupt_new_raw_digest(bytes(data),'uncompressed')
        with self.assertRaises(ValueError):corrupt_new_raw_digest(bytearray(source()),'uncompressed')
        with self.assertRaises(ValueError):corrupt_new_raw_digest(source(),'jpeg')

if __name__=='__main__':unittest.main()
