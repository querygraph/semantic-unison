import copy
from pathlib import Path
import tempfile
import unittest
from case import execute
from case_test import Case
from result import audit

class Results(unittest.TestCase):
    def fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);helper=Case();sources=helper.setup_case(d)
            result=execute(d,sources=sources,invoke=lambda:helper.invoke(d,sources),persist=lambda _:None)
            return sources,result
    def test_complete_is_not_cli_or_fd_or_fresh_bytes_proof(self):
        sources,result=self.fixture();proof=audit(result,sources=sources,server_pid=9)
        self.assertEqual(proof['sdk_helpers_settled'],2);self.assertEqual(proof['functional_status'],'PASSED')
        self.assertFalse(proof['cli_worker_fd_closure_proved']);self.assertFalse(proof['receiving_bytes_reverified'])
    def test_corrupt_summary_and_unknown_raw_settlement_refuse(self):
        sources,original=self.fixture()
        for mutate in [lambda r:r['helper_settlements'].pop(),lambda r:r['validation'].update(raw_digests_verified=False),
                       lambda r:r['outcome']['proxy'].update(server_pid=10),
                       lambda r:r['outcome'].update(stdout=r['outcome']['stdout'].replace('other-members=0','other-members=unknown')),
                       lambda r:r.update(complete=True,failure='original failure')]:
            result=copy.deepcopy(original);mutate(result)
            with self.assertRaises(ValueError):audit(result,sources=sources,server_pid=9)
    def test_failed_known_prefix_and_unstarted_preparation_are_distinct(self):
        sources,result=self.fixture();result.update(complete=False,phase='HELPER_SETTLEMENT_RECORDED',failure='byte verification failed')
        self.assertEqual(audit(result,sources=sources,server_pid=9)['functional_status'],'FAILED')
        for key in ['outcome','validation','helper_settlements']:result.pop(key)
        result['phase']='PREPARING_NO_CALL'
        self.assertTrue(audit(result,sources=sources,server_pid=9)['no_call_preparation'])
        result['phase']='CALL_MAY_HAVE_STARTED'
        with self.assertRaises(ValueError):audit(result,sources=sources,server_pid=9)

if __name__=='__main__':unittest.main()
