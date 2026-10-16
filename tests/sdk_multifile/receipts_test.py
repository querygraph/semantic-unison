"""Original synthetic diagnostic frames only; no SDK operation."""
import unittest
from receipts import audit,BUILD
from combined_test import frame,EXPECTED,D,E

def logs(first=1,second=2):return frame(21,D,12,first,first+2)+frame(22,E,13,second,second+2)

class Receipts(unittest.TestCase):
    def call(self,log):return audit(log,expected=EXPECTED,owner_pid=9,build_id=BUILD)
    def test_positive_and_serial_known_live_spans(self):
        self.assertTrue(self.call(logs())['known_live_overlap_observed'])
        self.assertFalse(self.call(logs(second=5))['known_live_overlap_observed'])
        self.assertFalse(self.call(logs())['sdk_compute_overlap_proved'])
    def test_missing_or_single_sample_timing_is_unknown_not_false(self):
        for log in ['\n'.join(l for l in logs().splitlines() if 'validation-live' not in l),logs().replace('samples=3','samples=1')]:
            value=self.call(log);self.assertIsNone(value['known_live_overlap_observed'])
            self.assertFalse(value['timing_coverage_complete']);self.assertEqual(len(value['helper_settlements']),2)
    def test_unknown_group_or_bad_sdk_verdict_refuses(self):
        for log in [logs().replace('other-members=0','other-members=unknown'),frame(21,D,12,1,3)+frame(22,E,13,2,4,raw='missing'),frame(21,D,12,1,3)+frame(22,E,13,2,4,raw='mismatch')]:
            with self.assertRaises(ValueError):self.call(log)
    def test_wrong_owner_extra_or_duplicate_diagnostics_refuse(self):
        for log in [logs().replace('owner-pid=9','owner-pid=8'),logs()+logs(),logs()+frame(23,'c'*64,14,1,3)]:
            with self.assertRaises(ValueError):self.call(log)

if __name__=='__main__':unittest.main()
