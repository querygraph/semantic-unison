import unittest
from combined import audit_success,settlements,IncompleteEvidence
import sdk_audit
D='a'*64;E='b'*64
EXPECTED=[dict(candidate_id='one',helper_pid=21,sha256=D,bytes=12),dict(candidate_id='two',helper_pid=22,sha256=E,bytes=13)]
def frame(pid,digest,size,first,last,raw='valid',status='exit:0',group='0'):
    report=('UNISON-DNG-VALIDATION 1\n'+''.join(k+' '+v+'\n' for k,v in zip(sdk_audit.FIELDS,
        [digest,str(size),sdk_audit.BUILD,'valid','success',raw,'0','0']))+'END\n').encode().hex()
    return (f'[server: validation-process] Helper result v0 pid={pid} status={status} outcome=completed candidate-sha256={digest} candidate-bytes={size} capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex={report} stderr-hex=\n'
      f'[server: validation-group] Retained group v0 pid={pid} candidate-sha256={digest} other-members={group}\n'
      f'[server: validation-live] Live span v0 owner-pid=9 pid={pid} candidate-sha256={digest} candidate-bytes={size} clock=monotonic-seconds-v0 samples=3 valid=true first={first} last={last}\n')
def logs(**kw):return frame(21,D,12,1,3)+frame(22,E,13,2,4,**kw)
class Join(unittest.TestCase):
    def test_success_overlap_and_flags(self):
        v=audit_success(logs(),expected=EXPECTED,owner_pid=9)
        self.assertTrue(v['overlap_observed']);self.assertEqual(len(v['helper_settlements']),2)
        self.assertFalse(v['cli_worker_fd_closure_proved'])
        self.assertFalse(v['timestamp_producer_authenticated'])
        self.assertFalse(v['sdk_activity_overlap_proved'])
    def test_serial_success_is_not_overlap(self):
        v=audit_success(frame(21,D,12,1,2)+frame(22,E,13,3,4),expected=EXPECTED,owner_pid=9)
        self.assertFalse(v['overlap_observed'])
    def test_closed_findings_are_not_success(self):
        for kw in [dict(raw='mismatch'),dict(status='exit:2')]:
            self.assertEqual(len(settlements(logs(**kw),expected=EXPECTED)),2)
            with self.assertRaises(ValueError):audit_success(logs(**kw),expected=EXPECTED,owner_pid=9)
    def test_unknown_group_cannot_settle(self):
        with self.assertRaises(ValueError):settlements(logs(group='unknown'),expected=EXPECTED)
    def test_missing_or_duplicate_helper(self):
        for log in [frame(21,D,12,1,3),logs()+frame(21,D,12,1,3),frame(21,D,12,1,3)*2]:
            with self.assertRaises(ValueError):audit_success(log,expected=EXPECTED,owner_pid=9)
    def test_owner_and_endpoint_fences(self):
        for args in [dict(owner_pid=10),dict(owner_pid=9,endpoint='client')]:
            with self.assertRaises(ValueError):audit_success(logs(),expected=EXPECTED,**args)
    def test_duplicate_candidate_binding_refused(self):
        with self.assertRaises(ValueError):audit_success(logs(),expected=[EXPECTED[0],EXPECTED[0]],owner_pid=9)
    def test_missing_optional_digest_is_explicit(self):
        v=audit_success(logs(raw='missing'),expected=EXPECTED,owner_pid=9)
        self.assertFalse(v['reports'][1]['report']['raw_digest_verified'])
if __name__=='__main__':unittest.main()
