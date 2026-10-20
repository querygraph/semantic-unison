"""Original receipt/artifact fixtures; no compiler, transport or resource pool."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from mixed_peer_compatibility import entry
from mixed_peer_compatibility.contract import UPSTREAM_COMMIT
from shared_cpu_pool import UnresolvedOwnership


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class UpstreamBinding(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'src').mkdir()
        for name,value in [('SOURCE.tar',b'original archive fixture'),('src/copy.ml',b'original source'),
                           ('compiler.opt',b'original compiler fixture'),('binary',b'original binary fixture')]:
            (self.root/name).write_bytes(value)
        compiler=self.root/'compiler.opt';binary=self.root/'binary'
        self.value=dict(complete=True,build_system='make',build_exit=0,selftest_exit=0,
            workspace=str(self.root),binary=str(binary),binary_sha256=sha(binary),
            compiler=str(compiler),compiler_sha256=sha(compiler),
            source_origin=dict(kind='git-commit',commit=UPSTREAM_COMMIT,archive=str(self.root/'SOURCE.tar')),
            source_archive_sha256=sha(self.root/'SOURCE.tar'),source_sha256={'src/copy.ml':sha(self.root/'src/copy.ml')})
        self.plan=dict(artifacts={'old-stock':dict(path=str(binary),sha256=sha(binary))},
            compiler_artifacts={'stock':dict(path=str(compiler.resolve()),sha256=sha(compiler))})

    def verify(self):
        path=self.root/'BUILD.json';path.write_text(json.dumps(self.value))
        self.plan['upstream_build']=dict(path=str(path),sha256=sha(path))
        entry.verify_upstream_baseline(self.plan)

    def test_exact_record_and_original_sources(self):self.verify()
    def test_wrong_revision_origin_or_test_outcome_refuses(self):
        original=copy.deepcopy(self.value)
        for field,bad in [('build_exit',False),('selftest_exit',False),('selftest_exit',1),('complete',False)]:
            with self.subTest(field=field,bad=bad):
                self.value=copy.deepcopy(original);self.value[field]=bad
                with self.assertRaises(ValueError):self.verify()
        for field,bad in [('commit','0'*40),('kind','working-tree'),('archive',str(self.root/'elsewhere'))]:
            with self.subTest(field=field):
                self.value=copy.deepcopy(original);self.value['source_origin'][field]=bad
                with self.assertRaises(ValueError):self.verify()
    def test_fork_capability_inventory_refuses(self):
        for module in ('semanticRemote','semanticRuntime'):
            with self.subTest(module=module):
                self.value['source_sha256']['src/'+module+'.ml']='a'*64
                with self.assertRaises(ValueError):self.verify()
                del self.value['source_sha256']['src/'+module+'.ml']
    def test_changed_archive_or_source_refuses(self):
        for name in ('SOURCE.tar','src/copy.ml'):
            with self.subTest(name=name):
                path=self.root/name;before=path.read_bytes();path.write_bytes(before+b'changed')
                with self.assertRaises(ValueError):self.verify()
                path.write_bytes(before)
    def test_close_uncertainty_propagates_exact_carrier(self):
        error=UnresolvedOwnership('original uncertain fixture close',retained_fds=(987,))
        with patch.object(entry,'digest',side_effect=error):
            with self.assertRaises(UnresolvedOwnership) as caught:self.verify()
        self.assertIs(caught.exception,error)
        self.assertEqual(caught.exception.retained_fds,(987,))


if __name__=='__main__':unittest.main()
