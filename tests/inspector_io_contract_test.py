"""Original metadata-only contract controls; no input is opened."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import inspector_io_contract as contract

ROOT = Path(__file__).resolve().parents[1]

class Contract(unittest.TestCase):
    def setUp(self):
        self.binding = dict(build_receipt='/private/tmp/inert-build.json',
            build_receipt_sha256='a'*64, binary_sha256='b'*64,
            input='/private/tmp/inert-camera.dng', input_identity={'sentinel': 1}, mode='components')
        self.argv = [sys.executable,str(ROOT/'tools/semantic-inspect/run.py'),
                     '--use-build',self.binding['build_receipt'],'--','--components',self.binding['input']]
        import importlib.util
        spec=importlib.util.spec_from_file_location('runner',ROOT/'tools/semantic-inspect/run.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        self.receipt=dict(schema='unison-semantic-inspector-build/1',complete=True,
            build_only=True,build_exit=0,binary_sha256='b'*64,
            source_sha256={str(p):'c'*64 for p in runner.SOURCES})
    def check(self):
        with patch('shared_io_pool.read_manifest',return_value=self.receipt),patch.object(contract,'identity',return_value={'sentinel':1}),patch.object(Path,'read_bytes',side_effect=AssertionError('no payload read')):
            return contract.check({'inspector_contract':self.binding},self.argv,ROOT)
    def test_accept(self):self.assertEqual(len(self.check()),26)
    def test_wrong_command(self):
        self.argv[-2]='--profile'
        with self.assertRaises(ValueError):self.check()
    def test_changed_identity(self):
        self.binding['input_identity']={}
        with self.assertRaises(ValueError):self.check()
    def test_changed_binary(self):
        self.receipt['binary_sha256']='d'*64
        with self.assertRaises(ValueError):self.check()
    def test_incomplete(self):
        self.receipt['complete']=False
        with self.assertRaises(ValueError):self.check()
    def test_extra_source(self):
        self.receipt['source_sha256']['../escape']='e'*64
        with self.assertRaises(ValueError):self.check()
    def test_missing_contract(self):
        self.binding['extra']=True
        with self.assertRaises(ValueError):self.check()
class Postcheck(unittest.TestCase):
    def test_same(self):
        with patch.object(contract, 'identity', return_value={'x': 1}):
            self.assertTrue(contract.postcheck({'input':'inert','input_identity':{'x':1}})['unchanged'])
    def test_changed(self):
        with patch.object(contract, 'identity', return_value={'x': 2}):
            self.assertFalse(contract.postcheck({'input':'inert','input_identity':{'x':1}})['unchanged'])
    def test_missing(self):
        with patch.object(contract, 'identity', side_effect=FileNotFoundError('gone')):
            result=contract.postcheck({'input':'inert','input_identity':{}})
            self.assertFalse(result['unchanged']);self.assertIn('gone',result['error'])
if __name__=='__main__':unittest.main()
