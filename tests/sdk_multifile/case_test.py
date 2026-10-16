"""Original tiny inputs and synthetic receipt transport; zero SDK/CLI calls."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from case import execute,UnresolvedOwnership
from combined_test import frame

class Case(unittest.TestCase):
    def setup_case(self,d):
        for side in ['left','right']:(d/side).mkdir()
        sources=[]
        for name,data in [('uncompressed.dng',b'original first fake'),('jpeg.dng',b'original second fake')]:
            (d/'left'/name).write_bytes(data)
            sources.append(dict(candidate_id=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        return sources
    def invoke(self,d,sources,*,missing=False,corrupt=False):
        for s in sources:(d/'right'/s['candidate_id']).write_bytes((d/'left'/s['candidate_id']).read_bytes())
        if corrupt:(d/'right'/'jpeg.dng').write_bytes(b'wrong')
        log=''.join(frame(21+i,s['sha256'],s['bytes'],1+i,3+i) for i,s in enumerate(sources[:1] if missing else sources))
        return dict(stdout=log,stderr='',supervisor_output='',returncode=0,timed_out=False,capture_truncated=False,supervisor_capture_truncated=False,proxy=dict(server_pid=9))
    def test_exact_case_records_settlement_before_byte_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources=self.setup_case(d);records=[]
            result=execute(d,sources=sources,invoke=lambda:self.invoke(d,sources),persist=records.append)
            self.assertTrue(result['complete']);self.assertTrue(result['validation']['raw_digests_verified'])
            self.assertTrue(any(r['phase']=='HELPER_SETTLEMENT_RECORDED' for r in records))
    def test_missing_helper_never_becomes_known_failed_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources=self.setup_case(d)
            with self.assertRaises(UnresolvedOwnership) as caught:
                execute(d,sources=sources,invoke=lambda:self.invoke(d,sources,missing=True),persist=lambda _:None)
            self.assertIn('outcome',caught.exception.result)
    def test_corrupt_received_bytes_preserves_known_settlement(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources=self.setup_case(d);records=[]
            with self.assertRaises(ValueError):execute(d,sources=sources,invoke=lambda:self.invoke(d,sources,corrupt=True),persist=records.append)
            self.assertFalse(records[-1]['complete']);self.assertEqual(len(records[-1]['helper_settlements']),2)
    def test_returned_outcome_persistence_failure_retains(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources=self.setup_case(d)
            def persist(value):
                if 'outcome' in value:raise OSError('original injected record failure')
            with self.assertRaises(UnresolvedOwnership):execute(d,sources=sources,invoke=lambda:self.invoke(d,sources),persist=persist)
    def test_post_call_error_is_not_hidden_by_successful_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources=self.setup_case(d);records=[]
            original=ValueError('original post-call pin failure')
            def invoke():
                original.outcome=self.invoke(d,sources);raise original
            with self.assertRaises(ValueError) as caught:
                execute(d,sources=sources,invoke=invoke,persist=records.append)
            self.assertIs(caught.exception,original)
            self.assertFalse(records[-1]['complete']);self.assertEqual(len(records[-1]['helper_settlements']),2)

if __name__=='__main__':unittest.main()
