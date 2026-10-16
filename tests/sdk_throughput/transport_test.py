import copy
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'sdk_host_matrix')]
from sdk_throughput.plan import row_plan
from sdk_throughput.transport import Invoker,RowJournal
from sdk_multifile.plan import BUILD
import invocation


class Journal:
    def __init__(self):self.events=[]
    def begin(self,identity,command):self.events.append(('begin',identity,command))
    def finish(self,outcome):self.events.append(('finish',outcome))


class Transport(unittest.TestCase):
    def fixture(self,index):
        label='stock' if index==0 else 'ox'
        b=dict(label=label,path='/inert/'+label,sha256='a'*64);t=dict(path='/inert/sdk',sha256='a'*64,build_id=BUILD,threads=1)
        return b,t,row_plan(b,t,'/private/tmp/u-st-unit',index)
    def test_real_owned_call_journals_exact_configured_workers(self):
        for index in (0,3):
            b,t,row=self.fixture(index);j=Journal();call=Invoker(row,binary=b,tool=t,journal=j,script_pins={n:'a'*64 for n in invocation.SCRIPT_NAMES},deadline=time.monotonic()+200)
            expected_workers=row['endpoint_workers']
            row['endpoint_workers']=18  # Caller mutation must not change the validated binding.
            outcome=dict(original='fake measured return')
            def measured(argv,env,*args,**kwargs):
                self.assertEqual(argv,row['command']);self.assertEqual(json.loads(env['UNISON_SYNC_BENCH_SERVER_FLAGS']),row['server_flags'])
                self.assertEqual(j.events[0][1]['workers'],expected_workers);self.assertTrue(kwargs['strict_group_settlement'])
                return outcome
            with patch.object(invocation,'artifact_sha',return_value='a'*64),patch.object(invocation,'measure_invocation',side_effect=measured) as run:
                self.assertIs(call(),outcome)
                with self.assertRaises(ValueError):call()
                run.assert_called_once()
            self.assertEqual(j.events[-1],('finish',outcome))
    def test_tampered_schedule_flags_limits_or_namespace_refuses(self):
        b,t,original=self.fixture(0)
        for mutate in [lambda r:r.update(round=False),lambda r:r.update(index=True),lambda r:r.update(endpoint_workers=3),lambda r:r.update(reserved_cpu_credits=18),
                       lambda r:r['command'].append('-extra'),lambda r:r.update(directory='/private/tmp/u-st-unit/r1/stock-w1')]:
            r=copy.deepcopy(original);mutate(r)
            with self.assertRaises(ValueError):Invoker(r,binary=b,tool=t,journal=Journal(),script_pins={},deadline=200)
    def test_rowjournal_never_normalizes_changed_transport_identity(self):
        _,_,r=self.fixture(0);j=Journal();adapter=RowJournal(r,j)
        identity=dict(label=r['label'],mode='semantic',workers=3,directory=r['directory'],stage='seed')
        for changes in [dict(workers=1),dict(label='ox'),dict(stage='update')]:
            with self.assertRaises(ValueError):adapter.begin(dict(identity,**changes),r['command'])
        self.assertEqual(j.events,[])


if __name__=='__main__':unittest.main()
