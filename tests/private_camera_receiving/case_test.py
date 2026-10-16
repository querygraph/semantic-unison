"""Original tiny byte fixtures + mock transport only; no camera payload IO."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import case


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-camera-case-mock-')
        self.root=Path(self.temp.name)
        (self.root/'left').mkdir();(self.root/'right').mkdir()
        self.source=self.root/'left/image.dng';self.target=self.root/'right/image.dng'
        self.source.write_bytes(b'original tiny generated control\0');self.source.chmod(0o600)
        self.initial=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.saved=[];self.calls=[];self.checks=0;self.failure=None;self.corrupt=False
    def tearDown(self):self.temp.cleanup()
    def check(self):self.checks+=1
    def invoke(self,stage):
        self.calls.append(stage)
        outcome={'returncode':1 if stage==self.failure else 0,'timed_out':False,'capture_truncated':False}
        if not outcome['returncode'] and stage!='noop':
            new=self.root/'right/stage'
            new.write_bytes(self.source.read_bytes()+(b'bad' if self.corrupt else b''));new.replace(self.target)
        return outcome
    def run_case(self,**kwargs):
        return case.exercise(self.root,initial_sha256=self.initial,
                check_borrowed=self.check,invoke=self.invoke,
                save=lambda value:self.saved.append(copy.deepcopy(value)),
                deadline_monotonic=kwargs.get('deadline',time.monotonic()+120))
    def test_each_owned_close_uncertainty_retains(self):
        # Separate fixtures: initial hash, append writer, retained old reader.
        for fail_at in (1, 3, 8):
            with self.subTest(close_number=fail_at):
                if self.target.exists():
                    self.target.unlink()
                self.source.write_bytes(b'original tiny generated control\0')
                calls = 0
                uncertain = []
                original = case.close_descriptors
                def close(fds):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        uncertain.extend(fds)
                        with patch('close.os.close', side_effect=OSError('fixture uncertain close')):
                            original(fds)
                    else:
                        original(fds)
                try:
                    with patch.object(case, 'close_descriptors', side_effect=close):
                        with self.assertRaises(case.UnresolvedOwnership) as caught:
                            self.run_case()
                    self.assertEqual(caught.exception.uncertain_fds, tuple(uncertain))
                finally:
                    for fd in uncertain:
                        os.close(fd)  # injected fault did not actually close fixture

    def test_exact_three_stages_and_old_reader(self):
        result=self.run_case()
        self.assertTrue(result['complete']);self.assertEqual(self.calls,['seed','update','noop'])
        self.assertEqual(self.target.read_bytes(),b'original tiny generated control\0'+case.TRAILER)
        self.assertFalse(result['photographic_validity_claimed'])
    def test_failure_preserves_actual_call(self):
        self.failure='seed'
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,['seed']);self.assertEqual(self.saved[-1]['calls']['seed']['returncode'],1)
        self.assertIn('failure',self.saved[-1]);self.assertFalse(self.saved[-1]['complete'])
    def test_wrong_initial_hash_refuses_before_calls(self):
        self.initial='0'*64
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,[])
    def test_corrupt_seed_stops_without_edit(self):
        self.corrupt=True;before=self.source.read_bytes()
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.source.read_bytes(),before);self.assertEqual(self.calls,['seed'])
    def test_expired_budget_starts_no_call(self):
        with self.assertRaises(ValueError):self.run_case(deadline=time.monotonic()+34)
        self.assertEqual(self.calls,[])
    def test_readonly_sender_not_mutated(self):
        self.source.chmod(0o400)
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,[])
    def test_symlink_sender_refused(self):
        replacement=self.root/'plain';self.source.rename(replacement);self.source.symlink_to(replacement)
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,[])


if __name__=='__main__':unittest.main()
