"""Injected callbacks only; original inert result frames, no SDK."""
import copy,unittest
from shared_result_test import Results
from shared_kernel import Kernel,UnresolvedOwnership
class JournalKernel(unittest.TestCase):
    def fixture(self):
        args,rows=Results().frames();return Kernel(*args),rows,[]
    def test_full_call_journal_before_and_after_each_callback(self):
        k,rows,saves=self.fixture();calls=[]
        def invoke(case):
            i=len(calls);self.assertEqual(saves[-1]['invocations'][-1]['state'],'INTENT')
            calls.append(case);return rows[i]['outcome']
        d=k.execute(invoke=invoke,persist=saves.append)
        self.assertTrue(d['complete']);self.assertEqual(len(calls),12)
        self.assertTrue(all(e['state']=='OUTCOME' for e in d['invocations']))
        with self.assertRaises(ValueError):k.execute(invoke=invoke,persist=saves.append)
    def test_invalid_first_receipt_stops_successors_preserves_outcome(self):
        k,rows,saves=self.fixture();rows[0]['outcome']['stdout']='bad';calls=[]
        def invoke(case):calls.append(case);return rows[0]['outcome']
        with self.assertRaises(ValueError):k.execute(invoke=invoke,persist=saves.append)
        self.assertEqual(len(calls),1);self.assertEqual(saves[-1]['invocations'][0]['state'],'OUTCOME')
        self.assertFalse(saves[-1]['complete']);self.assertFalse(saves[-1]['resource_release_authorized'])
    def test_missing_outcome_retains_unknown_and_no_next_call(self):
        k,rows,saves=self.fixture();calls=[]
        def invoke(case):calls.append(case);raise RuntimeError('no outcome')
        with self.assertRaises(UnresolvedOwnership):k.execute(invoke=invoke,persist=saves.append)
        self.assertEqual(len(calls),1);self.assertEqual(saves[-1]['invocations'][-1]['state'],'INTENT')
    def test_intent_persist_failure_prevents_dispatch(self):
        k,rows,saves=self.fixture();calls=[]
        def persist(d):
            saves.append(d)
            if d['invocations']:raise OSError('intent failed')
        with self.assertRaises(OSError):k.execute(invoke=calls.append,persist=persist)
        self.assertEqual(calls,[])
    def test_returned_evidence_persist_failure_retains(self):
        k,rows,saves=self.fixture()
        def persist(d):
            saves.append(d)
            if d['invocations'] and d['invocations'][-1]['state']=='OUTCOME':raise OSError('save failed')
        with self.assertRaises(UnresolvedOwnership):k.execute(invoke=lambda c:rows[0]['outcome'],persist=persist)
if __name__=='__main__':unittest.main()
