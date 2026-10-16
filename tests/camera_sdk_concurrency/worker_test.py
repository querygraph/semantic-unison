import copy,hashlib,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import worker as w
class Worker(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.saved=[];self.labels=[]
        self.plan=dict(workspace=str(self.d),tool=dict(build_id=w.BUILD),
            binaries={x:dict(label=x) for x in ['stock','ox']},transport_source_sha256={n:'a'*64 for n in w.SCRIPT_NAMES})
    def tearDown(self):self.tmp.cleanup()
    def execute(self):return w.execute(self.plan,self.d,time.monotonic()+400,persist=self.saved.append)
    def invoker(self,directory,**kw):
        def invoke():
            label=Path(directory).name;self.labels.append(label)
            kw['journal'].begin(dict(label=label,mode='semantic',workers=3,directory=str(directory),stage='seed'),['inert'])
            self.assertEqual(self.saved[-1]['invocations'][-1]['state'],'INTENT')
            kw['journal'].finish(dict(returncode=0));return dict(returncode=0)
        return invoke
    def case(self,directory,**kw):
        kw['persist'](dict(complete=False));kw['invoke']()
        result=dict(complete=True);kw['persist'](result);return result
    def test_serial_compiler_cases_and_parent_audit_before_complete(self):
        def audit(result,plan,workspace):
            self.assertTrue(result['complete']);self.assertFalse(self.saved[-1]['complete'])
            self.assertEqual(len(result['invocations']),2);return {'mock_independent_audit':True}
        with patch.object(w,'prepare_scripts',return_value=self.plan['transport_source_sha256']), \
             patch.object(w,'Invoker',side_effect=self.invoker),patch.object(w,'execute_case',side_effect=self.case), \
             patch.object(w,'audit',side_effect=audit):
            result=self.execute()
        self.assertEqual(self.labels,['stock','ox']);self.assertTrue(result['complete'])
        self.assertEqual(self.saved[-1]['phase'],'FINISHED')
    def test_uncertain_case_bypasses_ordinary_failure(self):
        with patch.object(w,'prepare_scripts',return_value=self.plan['transport_source_sha256']), \
             patch.object(w,'Invoker'),patch.object(w,'execute_case',side_effect=w.UnresolvedOwnership('unknown')):
            with self.assertRaises(w.UnresolvedOwnership):self.execute()
        self.assertNotIn('failure',self.saved[-1]);self.assertEqual(len(self.saved[-1]['cases']),1)
    def test_known_preparation_failure_zero_call_phase(self):
        with patch.object(w,'prepare_scripts',side_effect=ValueError('pin changed')):
            with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.saved[-1]['phase'],'PREPARING_NO_CALL');self.assertEqual(self.saved[-1]['invocations'],[])
    def test_audit_refusal_never_publishes_complete(self):
        with patch.object(w,'prepare_scripts',return_value=self.plan['transport_source_sha256']), \
             patch.object(w,'Invoker',side_effect=self.invoker),patch.object(w,'execute_case',side_effect=self.case), \
             patch.object(w,'audit',side_effect=ValueError('original audit refusal')):
            with self.assertRaises(ValueError):self.execute()
        self.assertFalse(self.saved[-1]['complete']);self.assertIn('original audit refusal',self.saved[-1]['failure'])
    def test_first_case_failure_stops_successor(self):
        def broken(directory,**kw):kw['invoke']();raise ValueError('first case failed')
        with patch.object(w,'prepare_scripts',return_value=self.plan['transport_source_sha256']), \
             patch.object(w,'Invoker',side_effect=self.invoker),patch.object(w,'execute_case',side_effect=broken):
            with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.labels,['stock']);self.assertEqual(len(self.saved[-1]['invocations']),1)
        self.assertFalse((self.d/'ox').exists());self.assertEqual(self.saved[-1]['phase'],'CALL_MAY_HAVE_STARTED')
    def test_real_script_preparation_matches_all_pins(self):
        pins={n:hashlib.sha256((w.ROOT/'bench/sync'/n).read_bytes()).hexdigest() for n in w.SCRIPT_NAMES}
        self.assertEqual(w.prepare_scripts(self.d,pins),pins)
        for name,digest in pins.items():
            target=self.d/name
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),digest)
            self.assertEqual(target.stat().st_mode & 0o777,0o700 if name=='launcher.py' else 0o600)
    def test_real_sdk_build_refused_before_case_creation(self):
        self.plan['tool']['build_id']='unison-sdk171-2724-v1-single'
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(list(self.d.iterdir()),[])
if __name__=='__main__':unittest.main()
