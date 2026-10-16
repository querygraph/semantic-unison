import os
import hashlib
from pathlib import Path
import stat
import tempfile
import unittest
from clone import prepare,prepare_inputs,stamp

DATA=b'original generated-fixture clone control'

class Clone(unittest.TestCase):
    def fixture(self,root,mode=0o644):
        source=root/'source';source.write_bytes(DATA);source.chmod(mode)
        directory=root/'left';directory.mkdir(mode=0o700)
        return source,stamp(source.lstat()),directory
    def fake(self,src,parent,name):
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644,dir_fd=parent)
        try:os.write(fd,DATA)
        finally:os.close(fd)
    def test_both_retained_modes_preserved_and_only_distinct_clone_mutable(self):
        for mode in [0o400,0o644]:
            with tempfile.TemporaryDirectory() as tmp:
                source,identity,d=self.fixture(Path(tmp),mode);r=prepare(source,identity,d,'uncompressed.dng',clone=self.fake)
                self.assertEqual(stamp(source.lstat()),identity)
                self.assertEqual((d/'uncompressed.dng').read_bytes(),DATA)
                self.assertEqual(stat.S_IMODE((d/'uncompressed.dng').stat().st_mode),0o600)
                self.assertEqual(r['backend'],'original-disposable-test-double');self.assertEqual(r['source_payload_read_bytes'],0)
    def test_existing_name_and_unsafe_names_never_invoke_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,identity,d=self.fixture(Path(tmp));(d/'jpeg.dng').write_bytes(b'prior')
            for name in ['jpeg.dng','../escape','other.dng']:
                with self.assertRaises(ValueError):prepare(source,identity,d,name,clone=lambda *_:self.fail('must not clone'))
            self.assertEqual((d/'jpeg.dng').read_bytes(),b'prior')
    def test_hardlink_alias_cannot_chmod_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,identity,d=self.fixture(Path(tmp))
            def link(src,parent,name):os.link(source,name,dst_dir_fd=parent)
            with self.assertRaises(ValueError):prepare(source,identity,d,'jpeg.dng',clone=link)
            self.assertEqual(stat.S_IMODE(source.stat().st_mode),0o644)
    def test_stale_source_and_clone_error_have_no_copy_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,identity,d=self.fixture(Path(tmp));wrong=dict(identity,st_size=1)
            with self.assertRaises(ValueError):prepare(source,wrong,d,'jpeg.dng',clone=lambda *_:self.fail('stale clone'))
            original=OSError('original clone refused')
            def fail(*_):raise original
            with self.assertRaises(OSError) as caught:prepare(source,identity,d,'jpeg.dng',clone=fail)
            self.assertIs(caught.exception,original);self.assertFalse((d/'jpeg.dng').exists())
    def test_two_input_mapping_and_cross_input_epoch_fence(self):
        for mutate in [False,True]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);directory=root/'left';directory.mkdir(mode=0o700);inputs=[];sources=[];values={}
                for i,name in enumerate(['uncompressed.dng','jpeg.dng']):
                    value=DATA+bytes([i]);source=root/name;source.write_bytes(value);source.chmod(0o644)
                    digest=hashlib.sha256(value).hexdigest();values[name]=value
                    inputs.append(dict(candidate_id=name,path=str(source),sha256=digest,identity=stamp(source.stat())))
                    sources.append(dict(candidate_id=name,sha256=digest,bytes=len(value)))
                def clone(src,parent,name):
                    fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=parent)
                    try:os.write(fd,values[name])
                    finally:os.close(fd)
                    if mutate and name=='uncompressed.dng':(root/'jpeg.dng').write_bytes(b'changed original disposable test input')
                if mutate:
                    with self.assertRaises(ValueError):prepare_inputs(inputs,sources,directory,clone=clone)
                    self.assertFalse((directory/'jpeg.dng').exists())
                else:
                    records=prepare_inputs(inputs,sources,directory,clone=clone)
                    self.assertEqual(len(records),2)
                    self.assertTrue(all(stamp(Path(i['path']).stat())==i['identity'] for i in inputs))
                    self.assertEqual((directory/'jpeg.dng').read_bytes(),values['jpeg.dng'])

if __name__=='__main__':unittest.main()
