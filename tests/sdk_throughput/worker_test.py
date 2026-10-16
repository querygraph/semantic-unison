"""Tiny prepared files/model transport only; no SDK or clone execution."""
import copy
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'sdk_multifile')]
from sdk_throughput import worker
from sdk_throughput.audit import audit
from sdk_throughput.audit_test import fixture


class Worker(unittest.TestCase):
    def control(self,mode):
        with tempfile.TemporaryDirectory(prefix='u-st-worker-',dir='/private/tmp') as tmp:
            root=Path(tmp);old,plan,_=fixture();plan['workspace']=str(root);plan['transport_source_sha256']={}
            saved=[];raw={};calls=[];clock=[1.]
            data={'uncompressed.dng':b'original first fake','jpeg.dng':b'original second fake'}
            def prepare(d,row):
                for name,value in data.items():(d/'left'/name).write_bytes(value)
                return dict(original_tiny_files=True)
            class Invoke:
                def __init__(self,row,*,journal,**kw):self.row=row;self.journal=journal
                def __call__(self):
                    r=self.row;d=Path(r['directory'])
                    self.journal.begin(dict(label=r['label'],mode='semantic',workers=r['endpoint_workers'],directory=str(d),stage='seed'),r['command'])
                    out=copy.deepcopy(old['invocations'][r['index']]['outcome']);out['command']=r['command'];out['proxy']['server_command']=[r['command'][0],'-server']
                    for name,value in data.items():(d/'right'/name).write_bytes(value)
                    raw[str(d/'seed-proxy.json')]=copy.deepcopy(out['proxy']);calls.append(out);self.journal.finish(out)
                    if mode=='stop':clock[0]=100.
                    return out
            with patch.object(worker,'prepare_scripts',return_value={}),patch.object(worker,'Invoker',Invoke),patch.object(worker.time,'monotonic',side_effect=lambda:clock[0]):
                if mode=='complete':
                    result=worker.execute(plan,root,200.,prepare_sources=prepare,read_proxy=lambda q:raw[str(q)],persist=saved.append)
                    self.assertTrue(result['complete']);self.assertEqual(len(calls),24)
                    self.assertEqual(result['parent_audit']['sdk_helpers_settled'],48)
                    self.assertEqual(result['parent_audit']['measured_rows'],20)
                else:
                    with self.assertRaisesRegex(ValueError,'before next comparison row'):
                        worker.execute(plan,root,200.,prepare_sources=prepare,read_proxy=lambda q:raw[str(q)],persist=saved.append)
                    result=saved[-1];self.assertEqual(len(calls),1);self.assertEqual(len(result['cases']),1)
                    proof=audit(result,plan,raw_proxy_receipts=list(raw.values()))
                    self.assertEqual(proof['functional_status'],'FAILED');self.assertEqual(proof['sdk_helpers_settled'],2)
                    self.assertFalse((root/'r0'/'ox-w1').exists())
            self.assertTrue(any(v['invocations'] and v['invocations'][-1]['state']=='INTENT' for v in saved))
    def test_complete24row_composition(self):self.control('complete')
    def test_deadline_stops_before_next_preparation_with_known_prefix(self):self.control('stop')
    def test_preparation_uncertainty_never_starts_transport(self):
        with tempfile.TemporaryDirectory(prefix='u-st-worker-',dir='/private/tmp') as tmp:
            _,plan,_=fixture();plan.update(workspace=tmp,transport_source_sha256={});saved=[]
            error=worker.UnresolvedOwnership('original preparation uncertainty')
            def refuse(*_):raise error
            with patch.object(worker,'prepare_scripts',return_value={}),patch.object(worker,'Invoker') as call:
                with self.assertRaises(worker.UnresolvedOwnership) as caught:
                    worker.execute(plan,Path(tmp),time.monotonic()+200,prepare_sources=refuse,read_proxy=lambda _:None,persist=saved.append)
                self.assertIs(caught.exception,error);call.assert_not_called()
            self.assertEqual(saved[-1]['invocations'],[]);self.assertNotIn('failure',saved[-1])


if __name__=='__main__':unittest.main()
