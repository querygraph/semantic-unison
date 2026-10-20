"""Inert transport/persistence tests; no process or real signal."""
import json,time,unittest
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from current_validation_paths import cancel_call

class DurableCall(unittest.TestCase):
    def call(self,fault=None):
        self.events=[];self.original=UnresolvedOwnership('original inert persistence',retained_fds=(999,))
        frame=dict(original='fabricated frame');raw=json.dumps(frame).encode()
        self.result=dict(pair=dict(original='fabricated pair'),fixture_observation=dict(original='fabricated observation'),
            client_interrupt=dict(original='fabricated signal'))
        def transport(*args,**kwargs):
            self.events.append('transport')
            if fault=='transport':raise self.original
            if fault!='unread':self.assertEqual(kwargs['read_proxy'](),frame)
            return self.result
        def read():self.events.append('read');return b'{} trailing' if fault=='raw' else raw
        def persist(row,pair,raw):
            self.events.append('persist')
            if fault=='persist':raise self.original
            self.saved=(row,pair,raw)
        with patch.object(cancel_call,'run',side_effect=transport):
            return cancel_call.call(dict(command=['inert-client']),{},proxy_command=['inert-proxy'],proxy_environment={},
                socket_path='/private/tmp/inert.sock',deadline=time.monotonic()+1,pass_fds=(100,),read_proxy_bytes=read,
                persist=persist,before_interrupt=lambda *args:None)
    def test_raw_pair_persists_before_returning_separate_signal_observations(self):
        pair,raw,evidence=self.call();self.assertEqual(self.events,['transport','read','persist'])
        self.assertEqual(self.saved[1:],(pair,raw));self.assertEqual(evidence['client_interrupt'],self.result['client_interrupt'])
    def test_unknown_transport_same_carrier_no_persistence(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('transport')
        self.assertIs(caught.exception,self.original);self.assertEqual(self.events,['transport'])
    def test_unknown_persistence_preserves_result_and_raw(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('persist')
        self.assertIs(caught.exception,self.original);self.assertEqual(caught.exception.cancellation_result,self.result)
        self.assertEqual(json.loads(caught.exception.cancellation_raw_proxy),dict(original='fabricated frame'))
    def test_invalid_raw_is_not_a_settled_failed_prefix(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('raw')
        self.assertIsInstance(caught.exception.original_failure,json.JSONDecodeError)
        self.assertNotIn('persist',self.events)

    def test_transport_cannot_skip_independent_raw_read(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('unread')
        self.assertIsNone(caught.exception.cancellation_raw_proxy)
        self.assertEqual(caught.exception.cancellation_result,self.result)
        self.assertNotIn('persist',self.events)

if __name__=='__main__':unittest.main()
