"""Original inert transport/persistence boundary controls, no actual child."""
import json,unittest
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from sdk_negative_receiving import bound_call


class BoundCall(unittest.TestCase):
    def call(self,run=None,persist=None):
        raw=json.dumps(dict(original_frame=True)).encode();events=[]
        def transport(*args,**kw):
            events.append('transport');self.assertEqual(kw['read_proxy'](),dict(original_frame=True))
            return dict(original_pair=True)
        def save(row,pair,frame):events.append('persist');self.assertEqual(frame,raw)
        with patch.object(bound_call,'run',side_effect=run or transport):
            result=bound_call.call(dict(command=['/original/client']),{},proxy_command=['/original/proxy'],
                proxy_environment={},socket_path='/original/none.sock',deadline=123,pass_fds=(701,),
                read_proxy_bytes=lambda:raw,persist=persist or save)
        return result,events
    def test_raw_evidence_is_persisted_before_return_without_policy_success_claim(self):
        result,events=self.call();self.assertEqual(events,['transport','persist'])
        self.assertEqual(result[0],dict(original_pair=True))
        self.assertNotIn('resource_release_authorized',result[0])
    def test_failed_persistence_preserves_pair_and_original_error(self):
        error=ValueError('injected durable record failure')
        def fail(*args):raise error
        with self.assertRaises(UnresolvedOwnership) as raised:self.call(persist=fail)
        self.assertIs(raised.exception.original_failure,error)
        self.assertEqual(raised.exception.negative_pair,dict(original_pair=True))
        self.assertIsInstance(raised.exception.negative_raw_proxy,bytes)
    def test_unknown_transport_carrier_is_preserved(self):
        error=UnresolvedOwnership('injected owner retained');error.retained_fds=(701,)
        with self.assertRaises(UnresolvedOwnership) as raised:self.call(run=error)
        self.assertIs(raised.exception,error);self.assertEqual(error.retained_fds,(701,))

if __name__=='__main__':unittest.main()
