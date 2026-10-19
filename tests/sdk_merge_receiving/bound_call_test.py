"""Inert adapter wiring controls; no process, file payload or native operation."""
import json
import unittest
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving import bound_call
from sdk_merge_receiving.evidence_test import fixture,PROXY

class Bound(unittest.TestCase):
    def run_call(self,fault=None):
        row,pair=fixture();self.events=[]
        raw=json.dumps(pair['raw_proxy']).encode();self.original=UnresolvedOwnership('original',retained_fds=(91,))
        def run(*args,**kwargs):
            self.events.append('invoke')
            if fault=='invoke':raise self.original
            self.assertEqual(kwargs['read_proxy'](),pair['raw_proxy'])
            if fault=='bind':pair['client']['returncode']=1
            return pair
        def persist(r,p,b):
            self.events.append('persist');self.assertEqual(b,raw)
            if fault=='persist':raise self.original
        with patch.object(bound_call.transport,'run',side_effect=run):
            return bound_call.call(row,{},proxy_command=PROXY,proxy_environment={},
                socket_path='/private/tmp/inert.sock',deadline=1,pass_fds=(91,),
                read_proxy_bytes=lambda:raw,persist=persist)

    def test_binding_happens_after_independent_read_and_durable_evidence(self):
        result=self.run_call();self.assertEqual(result['returncode'],0)
        self.assertEqual(self.events,['invoke','persist'])
        self.assertEqual(len(result['helper_record_sha256s']),2)

    def test_nested_invocation_or_writer_uncertainty_is_never_replaced(self):
        for fault in ('invoke','persist'):
            with self.subTest(fault=fault),self.assertRaises(UnresolvedOwnership) as caught:self.run_call(fault)
            self.assertIs(caught.exception,self.original)
            self.assertEqual(caught.exception.retained_fds,(91,))

    def test_raw_audit_failure_retains_pair_and_original_bytes(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_call('bind')
        self.assertIsNotNone(caught.exception.transport_pair)
        self.assertIsInstance(caught.exception.raw_proxy_bytes,bytes)
        self.assertIsInstance(caught.exception.original_failure,ValueError)
        self.assertEqual(self.events,['invoke','persist'])

if __name__=='__main__':unittest.main()
