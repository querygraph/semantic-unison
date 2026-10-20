"""Tiny original generated clone fixtures only; no retained data/SDK/native tool."""
import hashlib,os,tempfile,unittest
from pathlib import Path
from sdk_fixture_digest_fault_test import source
from sdk_negative_receiving.data import install_fault
from sdk_fixture_states import COMPRESSION


class FaultInstallation(unittest.TestCase):
    def test_each_encoding_and_byte_order_exact_one_byte_private_write(self):
        for codec in COMPRESSION:
            for little in (True,False):
                with tempfile.TemporaryDirectory() as temp:
                    root=Path(temp);raw=source(codec,little);path=root/'image.dng';path.write_bytes(raw);path.chmod(0o600)
                    native=root.stat();epoch=path.stat();expected=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
                    result=install_fault(root,(native.st_dev,native.st_ino),expected,codec)
                    after=path.read_bytes();self.assertEqual([i for i,(a,b) in enumerate(zip(raw,after)) if a!=b],[1024])
                    self.assertEqual(path.stat().st_ino,epoch.st_ino);self.assertEqual(result['after']['sha256'],hashlib.sha256(after).hexdigest())
                    self.assertFalse(result['actual_SDK_finding_proved']);self.assertFalse(result['resource_release_authorized'])
    def test_bad_hash_directory_identity_and_hardlink_refuse_before_mutation(self):
        for mode in ('hash','directory','hardlink'):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp);raw=source();path=root/'image.dng';path.write_bytes(raw);path.chmod(0o600)
                st=root.stat();identity=(st.st_dev,st.st_ino);expected=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
                if mode=='hash':expected['sha256']='f'*64
                if mode=='directory':identity=(st.st_dev,st.st_ino+1)
                if mode=='hardlink':os.link(path,root/'other')
                with self.assertRaises(ValueError):install_fault(root,identity,expected,'uncompressed')
                self.assertEqual(path.read_bytes(),raw)
    def test_malformed_digest_shape_refuses_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=bytearray(source());raw[58:60]=b'\x00\x00';raw=bytes(raw)
            path=root/'image.dng';path.write_bytes(raw);path.chmod(0o600);st=root.stat()
            with self.assertRaises(ValueError):install_fault(root,(st.st_dev,st.st_ino),dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)),'uncompressed')
            self.assertEqual(path.read_bytes(),raw)

if __name__=='__main__':unittest.main()
