"""Tiny original fake-clone controls; never invokes native cloning or camera IO."""
import os
from pathlib import Path
import tempfile
import unittest
import clone


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-camera-clone-mock-')
        self.root=Path(self.temp.name);self.source=self.root/'borrowed'
        self.source.write_bytes(b'four');self.source.chmod(0o400)
        self.directory=self.root/'sender';self.directory.mkdir(mode=0o700)
        self.expected=clone.stamp(self.source.lstat());self.calls=0
    def tearDown(self):self.temp.cleanup()
    def fake(self,src,parent,name):
        self.calls+=1
        fd=os.open(name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o400,dir_fd=parent)
        try:os.write(fd,b'four')
        finally:os.close(fd)
    def run_case(self,backend=None):
        return clone.prepare(self.source,self.expected,self.directory,clone=backend or self.fake)
    def test_distinct_mutable_copy_source_unchanged(self):
        result=self.run_case();self.assertEqual(self.source.lstat().st_mode&0o777,0o400)
        self.assertEqual(clone.stamp(self.source.lstat()),self.expected)
        self.assertEqual(result['clone_identity']['st_mode']&0o777,0o600)
        self.assertEqual(result['source_payload_read_bytes'],0)
        self.assertEqual(result['backend'],'original-disposable-test-double')
    def test_existing_target_refuses_before_clone(self):
        (self.directory/'image.dng').write_bytes(b'preserve')
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,0)
    def test_changed_source_refuses(self):
        self.expected['st_ino']+=1
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,0)
    def test_wrong_directory_mode_refuses(self):
        self.directory.chmod(0o755)
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,0)
    def test_clone_error_has_no_copy_fallback(self):
        def fail(*args):self.calls+=1;raise OSError('original clone refusal')
        with self.assertRaises(OSError):self.run_case(fail)
        self.assertEqual(self.calls,1);self.assertFalse((self.directory/'image.dng').exists())
    def test_hardlink_alias_refused_without_chmod_source(self):
        def hardlink(src,parent,name):os.link(self.source,name,dst_dir_fd=parent)
        with self.assertRaises(ValueError):self.run_case(hardlink)
        self.assertEqual(self.source.lstat().st_mode&0o777,0o400)


if __name__=='__main__':unittest.main()
