"""Journal ordering and interruption controls; no SDK or payload access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from worker import execute
from audit import audit_prefix
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership


class Worker(unittest.TestCase):
    def setUp(self):
        self.commands=[['/probe-'+label,'/sdk','/metadata','/candidate',
                        'a'*64,'build','b'*64,'1'] for label in ('stock','ox')]
        self.saved=[];self.calls=[];self.now=0

    def run_worker(self,**changes):
        def invoke(index,command,deadline):
            self.assertEqual(self.saved[-1]['invocations'][-1]['state'],'INTENT')
            self.calls.append(index)
            command[0]='mutated callback copy'
            return {'index':index}
        def inspect(outcome,**kwargs):
            self.assertEqual(self.saved[-1]['invocations'][-1]['state'],'OUTCOME')
            self.assertEqual(kwargs['command'],self.commands[outcome['index']])
            self.assertTrue(kwargs['require_admission'])
            return {'functional_status':'PASSED'}
        args=dict(deadline=500,metadata_version='fake',prepare=lambda *a:None,
                  invoke=invoke,persist=lambda r:self.saved.append(r),
                  check_sources=lambda:None,verify_input=lambda *a:None,
                  clock=lambda:self.now,inspect=inspect)
        args.update(changes)
        return execute(self.commands,**args)

    def test_complete_order_and_detached_snapshots(self):
        result=self.run_worker()
        self.assertTrue(result['complete']);self.assertEqual(self.calls,[0,1])
        self.assertEqual(self.saved[0]['invocations'],[])
        self.assertEqual(self.saved[1]['invocations'][0]['state'],'INTENT')
        self.assertEqual(self.commands[0][0],'/probe-stock')
        result['invocations'].clear()
        self.assertEqual(len(self.saved[-1]['invocations']),2)

    def test_failed_first_stops_successor_after_durable_outcome(self):
        with self.assertRaisesRegex(ValueError,'functional failure'):
            self.run_worker(inspect=lambda *a,**k:dict(functional_status='FAILED'))
        self.assertEqual(self.calls,[0])
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'OUTCOME')
        self.assertFalse(self.saved[-1]['complete'])

    def test_uncertain_invoke_preserves_intent_and_same_carrier(self):
        error=UnresolvedOwnership('unknown original child')
        def invoke(*args):raise error
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_worker(invoke=invoke)
        self.assertIs(caught.exception,error)
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'INTENT')

    def test_post_input_failure_keeps_outcome(self):
        def verify(*args):raise ValueError('input changed')
        with self.assertRaisesRegex(ValueError,'input changed'):self.run_worker(verify_input=verify)
        self.assertEqual(self.calls,[0])
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'OUTCOME')

    def test_next_case_headroom_and_preparation_recheck(self):
        def verify(*args):self.now=450
        with self.assertRaises(TimeoutError):self.run_worker(verify_input=verify)
        self.assertEqual(self.calls,[0])
        self.setUp()
        def prepare(*args):self.now=450
        with self.assertRaises(TimeoutError):self.run_worker(prepare=prepare)
        self.assertEqual(self.calls,[])
        self.assertEqual(self.saved[-1]['phase'],'PREPARING_NO_CALL')

    def test_persist_error_is_retained_not_failed_prefix(self):
        for fail_at in (1,2,3,6):
            with self.subTest(fail_at=fail_at):
                self.setUp();writes=[]
                def persist(value):
                    writes.append(copy.deepcopy(value))
                    self.saved.append(copy.deepcopy(value))
                    if len(writes)==fail_at:raise OSError('publication uncertain')
                with self.assertRaises(UnresolvedOwnership) as caught:self.run_worker(persist=persist)
                self.assertIsInstance(caught.exception.__cause__,OSError)
                self.assertEqual(len(writes),fail_at)

    def test_ordinary_invoke_error_is_not_invented_outcome(self):
        def invoke(*args):raise OSError('launch outcome unavailable')
        with self.assertRaises(OSError):self.run_worker(invoke=invoke)
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'INTENT')

    def test_durable_saved_actual_outcomes_reaudit_exact_prefix(self):
        receipt=Path(__file__).resolve().parents[1]/'qualification/mixed-validation-memory-admission-actual-20261016.json'
        rows=json.loads(receipt.read_text())['rows']
        outcomes=[copy.deepcopy(next(c for c in row['report']['cases'] if c['mode']=='pass')['outcome'])
                  for row in rows if row['label'] in ('stock','ox')]
        commands=[o['command'] for o in outcomes]
        with tempfile.TemporaryDirectory(prefix='unison-mixed-journal-') as directory:
            result=execute(commands,deadline=500,metadata_version='synthetic-only',
                           prepare=lambda *a:None,invoke=lambda i,*a:outcomes[i],
                           persist=lambda r:save(directory,r),check_sources=lambda:None,
                           verify_input=lambda *a:None,clock=lambda:0)
            stored=json.loads((Path(directory)/'RESULT.json').read_text())
            self.assertEqual(stored,result)
            proof=audit_prefix(stored,commands=commands,metadata_version='synthetic-only',require_admission=True)
            self.assertEqual(proof['attempted_probes'],2)
            self.assertFalse(proof['resource_release_authorized'])
            # These are historical outcomes, never a fresh process execution.
            stored['complete']=False;stored['phase']='CALL_MAY_HAVE_STARTED'
            stored['failure']='missing actual outcome'
            stored['invocations'][-1].update(state='INTENT',outcome=None)
            with self.assertRaises(ValueError):
                audit_prefix(stored,commands=commands,metadata_version='synthetic-only',require_admission=True)


if __name__=='__main__':unittest.main()
