"""Actual original children, injected counters; no SDK or OS probe invocation."""
import os
from pathlib import Path
import sys
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sdk_host_matrix'))
from shared_child import invoke
from retained import RetainedSamples


class Integration(unittest.TestCase):
    def test_missing_samples_and_nonzero_child_settle_independently(self):
        for code in [0,7]:
            calls=[]
            def factory(owner):
                def query(pid):
                    self.assertFalse(owner.reaped)
                    self.assertEqual(pid,owner.pid)
                    calls.append(pid)
                    return dict(pid=pid,available=False)
                return RetainedSamples(owner,query,limit=2)
            out=invoke([sys.executable,'-c',f'import time;time.sleep(.15);raise SystemExit({code})'],
                       dict(os.environ),time.monotonic()+5,observation_factory=factory,
                       observation_interval=.01)
            self.assertEqual(out['returncode'],code)
            self.assertEqual(len(calls),2)
            self.assertTrue(out['client_cleanup']['reaped'])
            self.assertTrue(out['client_cleanup']['other_group_members_absent_before_reap'])
            report=out['process_observations']
            self.assertEqual(report['pid'],out['client_cleanup']['pid'])
            self.assertFalse(report['process_settlement_proved'])
            self.assertFalse(report['resource_release_authorized'])
            self.assertTrue(all(s['observation']['available'] is False for s in report['samples']))
            with self.assertRaises(ChildProcessError):os.waitpid(report['pid'],os.WNOHANG)

    def test_invalid_observer_refuses_before_spawn(self):
        for interval in [True,0,.001,float('inf')]:
            with self.assertRaises(ValueError):
                invoke(['/never-spawned'],{},time.monotonic()+5,
                       observation_factory=lambda _:None,observation_interval=interval)


if __name__=='__main__':unittest.main()
