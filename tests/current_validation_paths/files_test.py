"""Tiny owned files and explicit injected uncertainty; no actual unknown close."""
import os,tempfile,unittest
from pathlib import Path
from current_validation_paths.files import Files
from shared_io_pool import UnresolvedIOOwnership,descriptor_observation


class PrivateFiles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);st=self.root.lstat()
        self.files=Files(self.root,(st.st_dev,st.st_ino));self.path=self.files.Path(self.root)
    def tearDown(self):
        if not self.files.closed:
            if self.files.retained is None:self.files.close()
            else:
                # All failures are injected AFTER closing the selected FD.
                # These remaining descriptor numbers are known test-owned and
                # were not passed to a failed close. Never retry uncertain IDs.
                for fd in self.files.retained.retained_fds:os.close(fd)
                self.files.closed=True
        self.temp.cleanup()
    def test_nested_utf8_bytes_modes_and_metadata(self):
        directory=self.path/'a'/'b';directory.mkdir(parents=True)
        file=directory/'fixture';self.assertEqual(file.write_bytes(b'original bytes'),14)
        self.assertEqual(file.read_bytes(),b'original bytes');file.write_text('é漢字')
        self.assertEqual(file.read_text(),'é漢字');file.chmod(0o400)
        self.assertEqual(file.stat().st_mode&0o777,0o400);self.assertTrue(file.is_file());self.assertTrue(directory.is_dir())
        file.chmod(0o600);file.unlink();self.assertFalse(file.exists())
    def test_outside_symlink_and_hardlink_refuse_without_truncating(self):
        outside=Path(self.temp.name).parent/'not-owned'
        for op in (lambda:self.files.Path(outside).read_bytes(),lambda:self.files.Path(outside).write_bytes(b'no')):
            with self.assertRaises(ValueError):op()
        target=self.root/'target';target.write_bytes(b'keep')
        os.symlink(target,self.root/'link')
        with self.assertRaises(OSError):(self.path/'link').write_bytes(b'no')
        os.link(target,self.root/'hard')
        with self.assertRaises(ValueError):(self.path/'hard').write_bytes(b'no')
        self.assertEqual(target.read_bytes(),b'keep')
    def test_directory_symlink_is_not_followed(self):
        actual=self.root/'actual';actual.mkdir(mode=0o700);(actual/'file').write_bytes(b'keep')
        os.symlink(actual,self.root/'alias')
        with self.assertRaises(OSError):(self.path/'alias/file').read_bytes()
    def test_bare_contexts_and_unplanned_mutations_refuse(self):
        file=self.path/'file'
        for op in (lambda:file.open('wb'),lambda:file.touch(),lambda:file.symlink_to('/elsewhere'),lambda:file.rename(self.path/'other')):
            with self.assertRaises(ValueError):op()
    def test_target_close_uncertainty_retains_root_and_no_numeric_retry(self):
        file=self.path/'file';file.write_bytes(b'keep');calls=[]
        def closer(fds):
            calls.append(tuple(fds));fd=fds[-1];observation=descriptor_observation(fd,'original_injected_fixture')
            os.close(fd) # Test knows this descriptor is already closed.
            raise UnresolvedIOOwnership('injected unknown after successful close',retained_fds=fds[:-1],uncertain_closes=[observation])
        self.files._closer=closer
        with self.assertRaises(UnresolvedIOOwnership) as raised:file.read_bytes()
        error=raised.exception;self.assertIn(self.files.fd,error.retained_fds)
        for op in (file.read_bytes,lambda:file.write_bytes(b'no'),self.files.close):
            with self.assertRaises(UnresolvedIOOwnership) as again:op()
            self.assertIs(again.exception,error)
        self.assertEqual(len(calls),1)
    def test_root_close_uncertainty_is_not_retried(self):
        calls=[]
        def closer(fds):
            calls.append(tuple(fds));fd=fds[0];observation=descriptor_observation(fd,'original_injected_root')
            os.close(fd)
            raise UnresolvedIOOwnership('injected root unknown after successful close',uncertain_closes=[observation])
        self.files._closer=closer
        with self.assertRaises(UnresolvedIOOwnership) as raised:self.files.close()
        self.assertNotIn(self.files.fd,raised.exception.retained_fds)
        with self.assertRaises(UnresolvedIOOwnership):self.files.close()
        self.assertEqual(len(calls),1)

if __name__=='__main__':unittest.main()
