"""Injected combined clone/close failures; inert FDs, no payload/syscall clone."""
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sdk_multifile import clone
from shared_io_pool import UnresolvedIOOwnership
from shared_cpu_pool import UnresolvedOwnership


class CloneUncertainty(unittest.TestCase):
    def test_clone_refusal_and_directory_close_failure_preserve_every_identity(self):
        for nested in (False,True):
            source=SimpleNamespace(st_dev=1,st_ino=11,st_mode=stat.S_IFREG|0o644,st_size=12,st_mtime_ns=1,st_ctime_ns=2,st_nlink=1,st_uid=os.getuid())
            directory=SimpleNamespace(st_dev=1,st_ino=12,st_mode=stat.S_IFDIR|0o700,st_size=0,st_mtime_ns=1,st_ctime_ns=2,st_nlink=1,st_uid=os.getuid())
            first=OSError('original clone failure');closing=OSError('original directory close uncertainty')
            inner_identity=dict(fd=900003,device=1,inode=13,role='original_inner_descriptor')
            error=UnresolvedIOOwnership('original nested close uncertainty',retained_fds=[900004],uncertain_closes=[inner_identity],original_failure=first) if nested else first
            def refused(*_):raise error
            def observe(fd):return source if fd==900001 else directory
            with patch.object(clone.os,'open',side_effect=[900001,900002]), \
                 patch.object(clone.os,'fstat',side_effect=observe),patch.object(clone.os,'lstat',return_value=source), \
                 patch.object(clone.os,'stat',side_effect=FileNotFoundError('unused original candidate')), \
                 patch.object(clone.os,'close',side_effect=closing) as close:
                with self.assertRaises(UnresolvedOwnership) as caught:
                    clone.prepare('/private/tmp/original-inert-input',clone.stamp(source),'/private/tmp/original-inert-directory','jpeg.dng',clone=refused)
            e=caught.exception
            close.assert_called_once_with(900002)
            self.assertIs(e.original_failure,error);self.assertIs(e.close_failure,closing)
            self.assertIn(900001,e.retained_fds)
            self.assertEqual({r['fd'] for r in e.uncertain_closes},{900002,900003} if nested else {900002})
            if nested:self.assertIn(900004,e.retained_fds)
            self.assertNotIn(900002,e.retained_fds)


if __name__=='__main__':unittest.main()
