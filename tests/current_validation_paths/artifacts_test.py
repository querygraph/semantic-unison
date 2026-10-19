"""Tiny original text artifacts, never executable or SDK payload reads."""
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from current_validation_paths.invoke import artifacts

class ArtifactFences(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='vpart-',dir='/private/tmp');root=Path(self.temp.name)
        (root/'src').mkdir(mode=0o700);(root/'src/current.ml').write_bytes(b'original source fixture\n')
        (root/'binary.txt').write_bytes(b'inert binary identity fixture\n');(root/'python.txt').write_bytes(b'inert interpreter identity fixture\n')
        ref=lambda p:dict(path=str(root/p),sha256=hashlib.sha256((root/p).read_bytes()).hexdigest())
        self.root=root;self.packet=dict(repository=str(root),source_pins={'src/current.ml':ref('src/current.ml')['sha256']},binary=ref('binary.txt'),interpreter=ref('python.txt'))
    def tearDown(self):self.temp.cleanup()
    def test_exact_current_source_and_both_artifacts_read_without_execution(self):artifacts(self.packet)
    def test_stale_source_refuses_before_reading_any_binary(self):
        (self.root/'src/current.ml').write_bytes(b'changed current source\n')
        from cached_benchmark.contract import read_bytes
        seen=[]
        def read(path,limit):seen.append(path);return read_bytes(path,limit)
        with patch('current_validation_paths.invoke.read_bytes',side_effect=read),self.assertRaises(ValueError):artifacts(self.packet)
        self.assertEqual(seen,[str(self.root/'src/current.ml')])
    def test_source_pin_cannot_escape_repository(self):
        self.packet['source_pins']={'../outside':'a'*64}
        with patch('current_validation_paths.invoke.read_bytes') as read,self.assertRaises(ValueError):artifacts(self.packet)
        read.assert_not_called()
    def test_uncertain_artifact_close_preserves_original_carrier(self):
        original=UnresolvedOwnership('original inert uncertain close',retained_fds=(999,))
        with patch('current_validation_paths.invoke.read_bytes',side_effect=original),self.assertRaises(UnresolvedOwnership) as caught:artifacts(self.packet)
        self.assertIs(caught.exception,original)

if __name__=='__main__':unittest.main()
