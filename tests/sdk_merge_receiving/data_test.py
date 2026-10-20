"""Original arbitrary 64-byte fixture states; never a real DNG or native clone."""
import copy
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from sdk_merge_receiving.data import Cases,install,stamp
from sdk_merge_receiving.plan import CODECS,STAGES

class Data(unittest.TestCase):
    def setUp(self):
        self.temp=Path(tempfile.mkdtemp(prefix='u-merge-data-',dir='/private/tmp'))
        self.workspace=self.temp/'receiving';self.workspace.mkdir(mode=0o700)
        self.sources=self.temp/'original-controls';self.sources.mkdir(mode=0o700)
        self.packet=dict(workspace=str(self.workspace),cases=[],source_observations={})
        self.values={};self.clone_calls=0
        for codec in CODECS:
            states={}
            for state in ('base','left','right','target'):
                value=(codec+'-'+state).encode().ljust(64,b'.');name=self.sources/(codec+'-'+state+'.dng')
                name.write_bytes(value);name.chmod(0o400)
                self.values[str(name)]=value
                states[state]=dict(path=str(name),sha256=hashlib.sha256(value).hexdigest(),bytes=len(value))
                self.packet['source_observations'][str(name)]=stamp(name.lstat())
            self.packet['cases'].append(dict(codec=codec,xmp_offset=8,xmp_size=16,states=states))
        def clone(src,parent,name):
            self.clone_calls+=1;value=os.pread(src,64,0)
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400,dir_fd=parent)
            try:os.write(fd,value)
            finally:os.close(fd)
        self.clone=clone;self.data=Cases(self.packet,clone=clone)
    def tearDown(self):shutil.rmtree(self.temp)
    def row(self,codec='uncompressed',stage='seed'):
        return dict(codec=codec,stage=stage,directory=str(self.workspace/codec))
    def outputs(self,row):
        case=next(c for c in self.packet['cases'] if c['codec']==row['codec'])
        state='base' if row['stage']=='seed' else 'target'
        for side in ('left','right'):
            image=self.workspace/row['codec']/side/'image.dng'
            image.write_bytes(self.values[case['states'][state]['path']]);image.chmod(0o600)

    def seed(self):
        row=self.row();candidate=self.data.prepare(row);self.outputs(row);self.data.verify(row,candidate)

    def test_all_nine_phases_install_only_disposable_inodes_and_verify_exact_bytes(self):
        original=copy.deepcopy(self.packet['source_observations'])
        for codec in CODECS:
            for stage in STAGES:
                row=self.row(codec,stage);candidate=self.data.prepare(row)
                if stage!='noop':self.outputs(row)
                self.data.verify(row,candidate)
        self.assertEqual(self.data.index,9);self.assertEqual(self.clone_calls,9)
        self.assertEqual(len(self.data.history),18)
        for name,epoch in original.items():self.assertEqual(stamp(Path(name).lstat()),epoch)
        self.assertTrue(all(e['backend']=='original-test-double' and e['source_payload_hash_bytes'] is None
            for row in self.data.history for e in row.get('clones',[])))

    def test_input_epoch_change_refuses_before_any_clone(self):
        Path(next(iter(self.packet['source_observations']))).chmod(0o600)
        with self.assertRaises(ValueError):self.data.prepare(self.row())
        self.assertEqual(self.clone_calls,0)

    def test_changed_receiving_inode_cannot_be_overwritten(self):
        self.seed();image=self.workspace/'uncompressed/left/image.dng'
        image.unlink();image.write_bytes(b'new private file');image.chmod(0o600)
        before=image.read_bytes()
        with self.assertRaises(ValueError):self.data.prepare(self.row(stage='update'))
        self.assertEqual(image.read_bytes(),before);self.assertEqual(self.clone_calls,1)

    def test_wrong_output_or_staging_is_not_verified(self):
        row=self.row();candidate=self.data.prepare(row);self.outputs(row)
        (self.workspace/'uncompressed/right/image.dng').write_bytes(b'x'*64)
        with self.assertRaises(ValueError):self.data.verify(row,candidate)
        self.assertEqual(self.data.index,0)

    def test_success_bytes_with_leftover_receiving_staging_are_not_accepted(self):
        row=self.row();candidate=self.data.prepare(row);self.outputs(row)
        (self.workspace/'uncompressed/left/.unison.original-control').write_bytes(b'private staging')
        with self.assertRaises(ValueError):self.data.verify(row,candidate)
        self.assertEqual(self.data.index,0)

    def test_noop_same_bytes_with_changed_timestamp_is_not_accepted(self):
        self.seed();row=self.row(stage='update');candidate=self.data.prepare(row)
        self.outputs(row);self.data.verify(row,candidate)
        row=self.row(stage='noop');candidate=self.data.prepare(row)
        image=self.workspace/'uncompressed/left/image.dng';epoch=image.stat()
        os.utime(image,ns=(epoch.st_atime_ns,epoch.st_mtime_ns+1000000))
        with self.assertRaises(ValueError):self.data.verify(row,candidate)
        self.assertEqual(self.data.index,2)

    def test_returned_candidate_cannot_mutate_manifest_expectation(self):
        row=self.row();candidate=self.data.prepare(row);self.outputs(row)
        candidate['sha256']='0'*64
        with self.assertRaises(ValueError):self.data.verify(row,candidate)
        self.assertNotEqual(self.data.history[-1]['candidate']['sha256'],'0'*64)

    def test_clone_refusal_has_no_copy_fallback_or_retry(self):
        self.data=Cases(self.packet,clone=lambda *_:(_ for _ in ()).throw(OSError('injected refusal')))
        with self.assertRaises(OSError):self.data.prepare(self.row())
        self.assertFalse((self.workspace/'uncompressed/left/image.dng').exists())
        with self.assertRaises(ValueError):self.data.prepare(self.row())

    def test_aliasing_clone_double_cannot_chmod_retained_source(self):
        reference=self.packet['cases'][0]['states']['base'];source=Path(reference['path'])
        endpoint=self.temp/'alias-control';endpoint.mkdir(mode=0o700);st=endpoint.stat()
        def alias(src,parent,name):os.link(source,name,dst_dir_fd=parent)
        with self.assertRaises(ValueError):install(reference,self.packet['source_observations'][str(source)],
            endpoint,(st.st_dev,st.st_ino),'seed',None,clone=alias)
        self.assertEqual(source.stat().st_mode & 0o777,0o400)

if __name__=='__main__':unittest.main()
