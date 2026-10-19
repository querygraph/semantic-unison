import struct,unittest
from sdk_fixture_states import states,geometry,VALUES,COMPRESSION


def fixture(codec='uncompressed',little=True,packet=None):
    order='<' if little else '>';data=bytearray(4096);data[:2]=b'II' if little else b'MM';struct.pack_into(order+'HIH',data,2,42,8,4)
    if packet is None:packet=b'<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:RDF><rdf:Description rdf:about="" xmp:MetadataDate="2026-10-19"/></rdf:RDF></x:xmpmeta>'+b' '*128+b'<?xpacket end="w"?>'
    for i,(tag,typ,n,value) in enumerate([(256,4,1,6000),(257,4,1,4000),(259,3,1,COMPRESSION[codec]),(700,1,len(packet),512)]):
        at=10+12*i;struct.pack_into(order+'HHI',data,at,tag,typ,n);struct.pack_into(order+('H' if typ==3 else 'I'),data,at+8,value)
    data[512:512+len(packet)]=packet;data[3072:]=bytes(range(256))*4
    return bytes(data)


class States(unittest.TestCase):
    def test_all_three_codecs_both_orders_four_disjoint_exact_states(self):
        for codec in COMPRESSION:
            for little in (True,False):
                source=fixture(codec,little);r=states(source,codec);offset,size=r['xmp_offset'],r['xmp_size']
                self.assertEqual(list(r['states']),list(VALUES));self.assertEqual(len(set(r['states'].values())),4)
                for state,data in r['states'].items():
                    self.assertEqual(len(data),len(source));self.assertEqual(data[:offset],source[:offset]);self.assertEqual(data[offset+size:],source[offset+size:])
                    for key,value in zip(('Rating','Label'),VALUES[state]):self.assertIn(('xmp:'+key+'="'+value+'"').encode(),data[offset:offset+size])
                self.assertNotEqual(r['states']['left'],r['states']['right'])
    def test_preserves_processing_instruction_and_unrelated_metadata_exactly(self):
        for data in states(fixture(),'uncompressed')['states'].values():
            self.assertIn(b'<?xpacket end="w"?>',data);self.assertIn(b'xmp:MetadataDate="2026-10-19"',data)
    def test_declared_codec_dimensions_and_duplicate_tags_refuse(self):
        with self.assertRaises(ValueError):states(fixture(),'jpeg')
        for at,fmt,value in ((18,'I',5999),(30,'I',3999),(46,'H',256)):
            data=bytearray(fixture());struct.pack_into('<'+fmt,data,at,value)
            with self.assertRaises(ValueError):states(bytes(data),'uncompressed')
    def test_xmp_table_alias_outside_extent_and_wrong_type_refuse(self):
        for at,fmt,value in ((54,'I',8),(54,'I',4090),(48,'H',7),(50,'I',1048577)):
            data=bytearray(fixture());struct.pack_into('<'+fmt,data,at,value)
            with self.assertRaises(ValueError):states(bytes(data),'uncompressed')
    def test_empty_bigtiff_truncated_and_mutable_bytes_refuse(self):
        big=bytearray(fixture());struct.pack_into('<H',big,2,43)
        for data in (b'',bytes(big),fixture()[:30],bytearray(fixture())):
            with self.assertRaises(ValueError):states(data,'uncompressed')
    def test_existing_scalar_duplicate_anchor_and_invalid_namespace_refuse(self):
        packet=fixture()[512:];packet=packet[:packet.index(b'<?xpacket')]+b'<?xpacket end="w"?>'
        for changed in (packet.replace(b'/></rdf:RDF>',b'><xmp:Rating>1</xmp:Rating></rdf:Description></rdf:RDF>'),packet.replace(b'rdf:about=""',b'rdf:about="" xmp:Rating="1"'),packet.replace(b'rdf:about=""',b'rdf:about="" rdf:about=""'),packet.replace(b'http://ns.adobe.com/xap/1.0/',b'urn:wrong')):
            with self.assertRaises(ValueError):states(fixture(packet=changed),'uncompressed')
    def test_padding_must_be_outside_root_and_large_enough(self):
        packet=fixture()[512:];packet=packet[:packet.index(b' '*128)]
        for changed in (packet,packet.replace(b'</rdf:RDF>',b' '*128+b'</rdf:RDF>')):
            with self.assertRaises(ValueError):states(fixture(packet=changed),'uncompressed')
    def test_dtd_entities_bad_utf8_and_deep_xml_refuse(self):
        for packet in (b'<!DOCTYPE x [<!ENTITY a "owned">]><x/>',b'\xff',b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'+b'<a>'*34+b'</a>'*34+b'</x:xmpmeta>'):
            with self.assertRaises(ValueError):states(fixture(packet=packet),'uncompressed')

if __name__=='__main__':unittest.main()
