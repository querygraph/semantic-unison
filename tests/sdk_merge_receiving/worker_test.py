"""Directed adapter faults; all adapters fabricated, no process/file payload."""
import unittest
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.worker import execute
from sdk_merge_receiving.helpers_test import frame, SHA
from sdk_merge_receiving.plan import BUILD

class Worker(unittest.TestCase):
    def run_worker(self, fault=None):
        self.events=[];self.saves=[];self.carrier=UnresolvedOwnership('original',retained_fds=(91,))
        def prepare(row):
            self.events.append(('prepare',row['stage']))
            return dict(sha256=SHA,bytes=256)
        def persist(value):
            self.saves.append(value)
            self.events.append(('persist',len(value['ledger']['entries'])))
            if fault=='intent' and len(value['ledger']['entries'])==1:raise OSError('intent fsync')
        def invoke(row):
            self.events.append(('invoke',row['stage']))
            if fault=='invoke':raise self.carrier
            return dict(returncode=1 if fault=='exit' else 0,
                log=frame('client')+frame('server',pid=124) if row['stage']=='update' else '',
                transport_record_sha256='2'*64,
                helper_record_sha256s=['3'*64,'4'*64] if row['stage']=='update' else [])
        def transport(row,outcome):
            self.events.append(('audit',row['stage']))
            if fault=='audit':raise ValueError('raw proxy missing')
        def verify(row,candidate):
            self.events.append(('verify',row['stage']))
            if fault=='bytes':raise ValueError('wrong received bytes')
        binaries={label:dict(label=label,path='/private/tmp/'+label,sha256='1'*64) for label in ('stock','ox')}
        return execute(binaries,dict(path='/private/tmp/tool',sha256='2'*64,build_id=BUILD,threads=1),
            '/private/tmp/u-smg-1234567890abcdef',prepare=prepare,invoke=invoke,
            audit_transport=transport,verify_outputs=verify,persist=persist)

    def test_nine_calls_with_durable_intent_before_each_dispatch(self):
        result=self.run_worker()
        self.assertTrue(result['ledger']['complete'])
        self.assertFalse(result['resource_release_authorized'])
        for index,event in enumerate(self.events):
            if event[0]=='invoke':self.assertEqual(self.events[index-1][0],'persist')
        self.assertEqual(sum(e[0]=='invoke' for e in self.events),9)
        self.assertEqual(sum(e[0]=='verify' for e in self.events),9)

    def test_intent_write_failure_never_dispatches(self):
        with self.assertRaises(OSError):self.run_worker('intent')
        self.assertFalse(any(e[0]=='invoke' for e in self.events))

    def test_existing_uncertainty_carrier_survives_unchanged(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_worker('invoke')
        self.assertIs(caught.exception,self.carrier)
        self.assertEqual(caught.exception.retained_fds,(91,))

    def test_audit_output_and_failed_call_stop_with_retained_evidence(self):
        for fault in ('audit','bytes','exit'):
            with self.subTest(fault=fault),self.assertRaises(UnresolvedOwnership) as caught:
                self.run_worker(fault)
            self.assertEqual(sum(e[0]=='invoke' for e in self.events),1)
            self.assertIsNotNone(caught.exception.original_failure)
            self.assertIsNotNone(caught.exception.invocation_outcome)
            self.assertEqual(caught.exception.call_ledger['state'],'UNRESOLVED_INTENT')

if __name__=='__main__':unittest.main()
