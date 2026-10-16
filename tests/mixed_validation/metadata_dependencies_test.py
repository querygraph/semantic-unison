"""Saved installed-package contract mutations; no package execution or media."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixed_validation import metadata_dependencies as deps
from mixed_validation import execute


class Metadata(unittest.TestCase):
    def setUp(self):
        p=Path(__file__).resolve().parents[2]/'doc/mixed-exiftool-package-inventory-v1.json'
        self.record=json.loads(p.read_text())
        self.metadata=dict(executable=self.record['executable'],version='13.10',
                           inventory=dict(path=str(p),sha256='a'*64,bytes=p.stat().st_size))
        self.expected=[Path(r['path']) for r in self.record['modules']]
    def call(self):
        with patch.object(execute,'document',return_value=self.record),\
             patch.object(deps,'verified_hash') as checker,\
             patch.object(deps,'system_perl',return_value=self.record['system_interpreter']),\
             patch.object(deps,'package_paths',return_value=self.expected):
            proof=deps.verify(self.metadata)
        return proof,checker.call_count
    def test_all_declared_module_pins_checked_and_limits_truthful(self):
        proof,count=self.call()
        self.assertEqual(proof['package_modules_verified'],236)
        self.assertEqual(count,238)
        self.assertFalse(proof['full_runtime_dependency_inventory_complete'])
        self.assertFalse(proof['execution_authorized'])
    def test_wrong_version_roster_and_claim_refuse(self):
        original=copy.deepcopy(self.record)
        for mode in ('version','missing','reorder','runtime','root'):
            self.record=copy.deepcopy(original)
            if mode=='version':self.record['version']='13.1'
            elif mode=='missing':self.record['modules'].pop()
            elif mode=='reorder':self.record['modules'].reverse()
            elif mode=='runtime':self.record['full_runtime_dependency_inventory_complete']=True
            else:self.record['package_root']='/different/install'
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.call()


if __name__=='__main__':unittest.main()
