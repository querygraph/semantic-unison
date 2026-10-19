"""Original pure orchestration doubles; no child/FD/native activity."""
import copy,unittest
from sdk_merge_receiving.plan_test import inputs
from shared_cpu_pool import UnresolvedOwnership
from sdk_negative_receiving.worker import execute


class Worker(unittest.TestCase):
    def run_case(self,fail=None,error=None):
        binaries,tool,_=inputs();trace=[];snapshots=[]
        def step(name):
            trace.append(name)
            if fail==name:raise error or ValueError('original '+name)
        def prepare(row):step('prepare');return dict(sha256='a'*64,bytes=4096)
        def invoke(row):step('invoke');return dict(original_outcome=True)
        def audit(row,out,candidate):step('audit');return dict(resource_release_authorized=False)
        def verify(row,candidate):step('verify');return dict(resource_release_authorized=False)
        def persist(value):step('persist');snapshots.append(copy.deepcopy(value))
        def run():return execute(binaries,tool,'/private/tmp/u-snr-'+'a'*16,
            prepare=prepare,invoke=invoke,audit_transport=audit,verify_outputs=verify,persist=persist)
        return run,trace,snapshots
    def test_twelve_intents_precede_calls_and_require_rejections_are_not_retries(self):
        run,trace,snapshots=self.run_case();result=run()
        self.assertEqual(trace,['persist']+['prepare','persist','invoke','audit','verify','persist']*12)
        self.assertEqual(len(snapshots),25);self.assertEqual(len(result['results']),12)
        self.assertEqual([e['expected_client_exit'] for e in result['events'] if e['event']=='ACCEPTED'],[0,1,0,0]*3)
        self.assertTrue(result['parent_audit_required']);self.assertFalse(result['resource_release_authorized'])
    def test_failure_at_each_adapter_stops_new_calls_and_retains_original(self):
        for phase in ('prepare','persist','invoke','audit','verify'):
            original=ValueError('injected '+phase);run,trace,_=self.run_case(phase,original)
            with self.subTest(phase=phase),self.assertRaises(UnresolvedOwnership) as raised:run()
            self.assertIs(raised.exception.original_failure,original)
            self.assertLessEqual(trace.count('invoke'),1)
            if phase=='persist':self.assertEqual(trace,['persist'])
    def test_existing_uncertain_owner_is_not_replaced_or_retried(self):
        original=UnresolvedOwnership('injected uncertain descriptor');original.uncertain_fds=(55,)
        run,trace,_=self.run_case('audit',original)
        with self.assertRaises(UnresolvedOwnership) as raised:run()
        self.assertIs(raised.exception,original);self.assertEqual(original.uncertain_fds,(55,))
        self.assertEqual(trace.count('invoke'),1);self.assertNotIn('verify',trace)
    def test_late_persistence_failure_retains_completed_prefix_without_next_call(self):
        binaries,tool,_=inputs();calls=[];count=0
        def persist(value):
            nonlocal count
            count+=1
            if count==5:raise ValueError('save second acceptance failed')
        with self.assertRaises(UnresolvedOwnership) as raised:
            execute(binaries,tool,'/private/tmp/u-snr-'+'a'*16,
                prepare=lambda row:dict(sha256='a'*64,bytes=4096),
                invoke=lambda row:calls.append(row['stage']),
                audit_transport=lambda *args:dict(resource_release_authorized=False),
                verify_outputs=lambda *args:dict(resource_release_authorized=False),persist=persist)
        self.assertEqual(calls,['seed','negative']);self.assertEqual(len(raised.exception.negative_receiving_state['results']),2)

if __name__=='__main__':unittest.main()
