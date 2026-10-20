import hashlib,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sdk_fixture_preservation as P
from shared_cpu_pool import UnresolvedOwnership
from private_camera_receiving.close import close_descriptors


def copied(source,parent,name):
    # Original disposable test double, not a runtime fallback.
    value=os.pread(source,65536,0);fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=parent)
    try:
        if os.write(fd,value)!=len(value):raise OSError('original fixture short write')
    finally:close_descriptors([fd])


class Preservation(unittest.TestCase):
    def setup(self,root,mode=0o400):
        root=Path(root);source=root/'source';source.write_bytes(b'original generated fixture'*17);source.chmod(mode)
        dest=root/'dest';dest.mkdir(mode=0o700);d=dest.stat();parent=os.open(dest,os.O_RDONLY|os.O_DIRECTORY)
        ref=dict(codec='jpeg',path=str(source),identity=P.stamp(source.stat()),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        return source,dest,parent,(d.st_dev,d.st_ino),ref

    def test_readonly_and_mutable_source_epochs_preserved_clone_is_readonly(self):
        for mode in (0o400,0o600):
            with tempfile.TemporaryDirectory() as root:
                source,dest,parent,identity,ref=self.setup(root,mode)
                try:out=P.preserve_one(ref,parent,str(dest),identity,clone=copied)
                finally:close_descriptors([parent])
                self.assertEqual(P.stamp(source.stat()),ref['identity'])
                self.assertEqual((dest/'jpeg.dng').read_bytes(),source.read_bytes())
                self.assertEqual((dest/'jpeg.dng').stat().st_mode&0o777,0o400)
                self.assertNotEqual(out['identity']['st_ino'],ref['identity']['st_ino'])
                self.assertIsNone(out['source_payload_hash_bytes'])
                self.assertEqual(out['backend'],'original-disposable-test-double')

    def test_existing_target_never_overwritten_or_cloned_again(self):
        with tempfile.TemporaryDirectory() as root:
            source,dest,parent,identity,ref=self.setup(root);(dest/'jpeg.dng').write_bytes(b'preserved old target')
            try:
                with self.assertRaisesRegex(ValueError,'exists'):
                    P.preserve_one(ref,parent,str(dest),identity,clone=lambda *args:self.fail('no retry/overwrite'))
            finally:close_descriptors([parent])
            self.assertEqual((dest/'jpeg.dng').read_bytes(),b'preserved old target')
            self.assertEqual(P.stamp(source.stat()),ref['identity'])

    def test_wrong_hash_preserves_failed_clone_and_source(self):
        with tempfile.TemporaryDirectory() as root:
            source,dest,parent,identity,ref=self.setup(root);ref['sha256']='0'*64
            try:
                with self.assertRaisesRegex(ValueError,'SHA'):
                    P.preserve_one(ref,parent,str(dest),identity,clone=copied)
            finally:close_descriptors([parent])
            self.assertTrue((dest/'jpeg.dng').exists())
            self.assertEqual(P.stamp(source.stat()),ref['identity'])

    def test_qualified_close_uncertainty_is_propagated_once_without_retry(self):
        with tempfile.TemporaryDirectory() as root:
            source,dest,parent,identity,ref=self.setup(root)
            injected=UnresolvedOwnership('original synthetic close uncertainty',uncertain_fd=987)
            calls=[]
            def fail_after_real_fixture_close(fds):
                calls.append(tuple(fds));close_descriptors(fds);raise injected
            try:
                with patch.object(P,'close_descriptors',side_effect=fail_after_real_fixture_close):
                    with self.assertRaises(UnresolvedOwnership) as out:P.preserve_one(ref,parent,str(dest),identity,clone=copied)
                self.assertIs(out.exception,injected);self.assertEqual(len(calls),1)
            finally:close_descriptors([parent])


if __name__=='__main__':unittest.main()
