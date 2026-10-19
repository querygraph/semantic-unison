"""Original executable-byte doubles; never opens an actual executable."""
import copy
import hashlib
import unittest
from unittest.mock import patch
from sdk_merge_receiving import artifacts

class Artifacts(unittest.TestCase):
    def packet(self):
        self.payloads={};self.reads=[]
        def ref(name):
            path='/qualified/'+name;raw=('original '+name).encode();self.payloads[path]=raw
            return dict(path=path,sha256=hashlib.sha256(raw).hexdigest())
        packet=dict(interpreter=ref('python'),tool=ref('sdk'),binaries={name:ref(name) for name in ('stock','ox')},
            builds={name:dict(compiler=ref(name+'-compiler')) for name in ('stock','ox')})
        return packet
    def read(self,path,limit):self.reads.append(path);return self.payloads[path]

    def test_all_six_exact_hashes_without_claiming_lock_authority(self):
        packet=self.packet()
        with patch.object(artifacts,'read_bytes',side_effect=self.read):proof=artifacts.verify(packet)
        self.assertEqual(set(self.reads),set(self.payloads));self.assertEqual(len(self.reads),6)
        self.assertFalse(proof['io_ownership_independently_proved'])
        self.assertTrue(proof['requires_owned_io']);self.assertFalse(proof['resource_release_authorized'])

    def test_changed_or_aliased_artifact_refuses(self):
        packet=self.packet();self.payloads['/qualified/sdk']=b'changed original bytes'
        with patch.object(artifacts,'read_bytes',side_effect=self.read),self.assertRaises(ValueError):artifacts.verify(packet)
        packet=self.packet();packet['tool']=copy.deepcopy(packet['interpreter'])
        with patch.object(artifacts,'read_bytes',side_effect=AssertionError('must not open aliased set')), \
             self.assertRaises(ValueError):artifacts.verify(packet)

if __name__=='__main__':unittest.main()
