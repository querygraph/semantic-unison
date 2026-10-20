"""Real build-artifact rechecks and pure provenance mutation controls."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixed_validation.build_receipts import check,verify

Q=Path(__file__).resolve().parents[1]/'qualification/mixed-validation-probe-build-actual-20261016.json'


def fixture(label='stock'):
    row=next(r for r in json.loads(Q.read_text())['rows'] if r['label']==label)
    r=copy.deepcopy(row['report']);p=Path(r['executable']['path']).parent/'RESULT.json'
    item=dict(label=label,executable=r['executable'],build_receipt=dict(path=str(p),bytes=p.stat().st_size,
              sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    production=json.loads(Path(r['build_result']['path']).read_text())
    return r,item,production


class Builds(unittest.TestCase):
    def test_both_real_compiler_outputs_reverified_without_execution(self):
        for label in ('stock','ox'):
            with self.subTest(label=label):
                r,item,p=fixture(label);proof=verify(item)
                self.assertTrue(proof['build_provenance_bound'])
                self.assertFalse(proof['standard_library_inventory_complete'])
                self.assertFalse(proof['artifact_execution_authorized'])
    def test_incomplete_execution_alias_and_companion_refuse(self):
        for mutation in ('complete','sdk','source','compiler','exe','reaped','argv','companion','prod'):
            r,item,p=fixture()
            if mutation=='complete':r['complete']=False
            elif mutation=='sdk':r['sdk_calls']=True
            elif mutation=='source':r['source']['path']='/different/probe.ml'
            elif mutation=='compiler':p['compiler_sha256']='0'*64
            elif mutation=='exe':item['executable']=dict(item['executable'],sha256='0'*64)
            elif mutation=='reaped':r['outcome']['client_cleanup']['reaped']=False
            elif mutation=='argv':r['command'][1]='-different'
            elif mutation=='companion':r['linked_inputs'].pop(next(iter(r['linked_inputs'])))
            else:p['selftest_exit']=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):check(r,item,p)


if __name__=='__main__':unittest.main()
