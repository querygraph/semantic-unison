"""Whole pure data lifecycle with tiny original files and explicit copy doubles."""
import hashlib,os,shutil,tempfile,unittest
from pathlib import Path
from sdk_fixture_digest_fault_test import source
from sdk_merge_receiving.data import stamp
from sdk_negative_receiving.data import Cases


class CaseLifecycle(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='u-negative-cases-'));self.workspace=self.root/'receiving';self.workspace.mkdir(mode=0o700)
        sources=self.root/'source';sources.mkdir(mode=0o700);packet=dict(workspace=str(self.workspace),cases=[],source_observations={});self.values={}
        for codec in ('uncompressed','jpeg','jxl'):
            data=source(codec);path=sources/(codec+'.dng');path.write_bytes(data);path.chmod(0o400)
            self.values[codec]=data;packet['cases'].append(dict(codec=codec,states=dict(base=dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))))
            packet['source_observations'][str(path)]=stamp(path.lstat())
        self.clone_calls=0
        def clone(fd,parent,name):
            self.clone_calls+=1;target=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400,dir_fd=parent)
            try:self.assertEqual(os.write(target,os.pread(fd,4096,0)),4096)
            finally:os.close(target)
        self.data=Cases(packet,clone=clone)
    def tearDown(self):shutil.rmtree(self.root)
    def row(self,codec,policy,stage):return dict(codec=codec,policy=policy,stage=stage,directory=str(self.workspace/(codec+'-'+policy)))
    def transfer_double(self,row):
        root=Path(row['directory'])
        if row['stage']=='seed' or row['policy']=='warn':
            image=root/'right/image.dng';image.write_bytes((root/'left/image.dng').read_bytes());image.chmod(0o600)
    def test_all_twelve_phases_preserve_sources_and_qualify_require_warn_separately(self):
        for codec in ('uncompressed','jpeg','jxl'):
            for policy in ('require','warn'):
                for stage in ('seed','negative'):
                    row=self.row(codec,policy,stage);candidate=self.data.prepare(row);self.transfer_double(row)
                    result=self.data.verify(row,candidate);self.assertFalse(result['resource_release_authorized'])
                    if stage=='negative':self.assertEqual(result['destination_preserved'],policy=='require')
        self.assertEqual(self.clone_calls,6);self.assertEqual(self.data.index,12);self.assertEqual(len(self.data.history),24)
        self.data.fence_sources()
        for path in self.data.packet['source_observations']:
            self.assertEqual(Path(path).read_bytes(),self.values[Path(path).stem])
    def test_published_require_candidate_is_not_accepted(self):
        seed=self.row('uncompressed','require','seed');candidate=self.data.prepare(seed);self.transfer_double(seed);self.data.verify(seed,candidate)
        row=self.row('uncompressed','require','negative');candidate=self.data.prepare(row)
        root=Path(row['directory']);(root/'right/image.dng').write_bytes((root/'left/image.dng').read_bytes())
        with self.assertRaises(ValueError):self.data.verify(row,candidate)
        self.assertEqual(self.data.index,1)
    def test_wrong_phase_or_changed_destination_refuses_before_fault(self):
        with self.assertRaises(ValueError):self.data.prepare(self.row('jpeg','warn','negative'))
        row=self.row('uncompressed','require','seed');candidate=self.data.prepare(row);self.transfer_double(row);self.data.verify(row,candidate)
        root=Path(row['directory']);left=(root/'left/image.dng').read_bytes();(root/'right/image.dng').write_bytes(b'x'*4096)
        with self.assertRaises(ValueError):self.data.prepare(self.row('uncompressed','require','negative'))
        self.assertEqual((root/'left/image.dng').read_bytes(),left)

if __name__=='__main__':unittest.main()
