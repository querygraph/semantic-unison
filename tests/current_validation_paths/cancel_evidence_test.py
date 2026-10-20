"""Fabricated cancellation captures only; no process, signal or file IO."""
import copy,json,unittest
from current_validation_paths.evidence_test import bundle,lines
from current_validation_paths.cancel_evidence import audit


def fixture():
    row,pair,entries=bundle('hang',3);entry=entries[0];entry['endpoint']='client';entry['outcome']='cancelled'
    pair['proxy']['stderr']='';pair['client']['stderr']=lines(entry)+'Update propagation interrupted\nAborted by user request\n'
    observed=dict(helper=dict(pid=entry['pid'],sha256=entry['candidate_sha256'],size=entry['candidate_bytes']),
        client_pid=pair['client']['client_cleanup']['pid'],candidate_bytes_verified=True,previous_destination_preserved=True,
        source_preserved=True,helper_settlement_proved=False,resource_release_authorized=False)
    sent=dict(pid=observed['client_pid'],signal=2,sent=True,client_reaped_before_signal=False,resource_release_authorized=False)
    return row,pair,entries,dict(fixture_observation=observed,client_interrupt=sent)


def check(row,pair,entries,cancellation):
    return audit(pair,cancellation=cancellation,client_command=row['command'],proxy_command=pair['proxy']['command'],
        server_command=row['server_command'],raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode(),expected_helpers=entries)

class Evidence(unittest.TestCase):
    def test_actual_exit3_and_cancelled_helper_do_not_authorize_resource_release(self):
        result=check(*fixture());self.assertEqual(result['client_returncode'],3)
        self.assertEqual(result['helper_observations'][0]['expected']['outcome'],'cancelled')
        self.assertFalse(result['resource_release_authorized']);self.assertFalse(result['parent_terminal_proved'])
    def test_validation_failure2_or_signal_client_is_not_normal_cancellation(self):
        for code in (0,1,2,-2,True):
            row,pair,entries,cancellation=fixture();pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=code
            with self.subTest(code=code),self.assertRaises(ValueError):check(row,pair,entries,cancellation)
    def test_signal_and_observer_bind_to_actual_direct_client(self):
        for key,value in [('pid',102),('signal',15),('sent',False),('client_reaped_before_signal',True),('resource_release_authorized',True)]:
            row,pair,entries,cancellation=fixture();cancellation['client_interrupt'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check(row,pair,entries,cancellation)
    def test_observed_helper_must_bind_to_exact_cancelled_raw_record(self):
        for key,value in [('pid',999),('sha256','b'*64),('size',4095)]:
            row,pair,entries,cancellation=fixture();cancellation['fixture_observation']['helper'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check(row,pair,entries,cancellation)
    def test_missing_trace_group_or_normal_native_diagnostic_refuses(self):
        for old,new in [('outcome=cancelled','outcome=timed-out'),('other-members=0','other-members=unknown'),
            ('Update propagation interrupted','missing'),('Aborted by user request','missing')]:
            row,pair,entries,cancellation=fixture();pair['client']['stderr']=pair['client']['stderr'].replace(old,new)
            with self.subTest(old=old),self.assertRaises(ValueError):check(row,pair,entries,cancellation)
    def test_preservation_observation_cannot_claim_child_settlement(self):
        for key,value in [('previous_destination_preserved',False),('helper_settlement_proved',True),('source_preserved',False)]:
            row,pair,entries,cancellation=fixture();cancellation['fixture_observation'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check(row,pair,entries,cancellation)

if __name__=='__main__':unittest.main()
