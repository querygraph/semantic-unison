"""Actual tiny original Python helpers; no SDK, payload, compiler or canonical IO."""
import os,sys,time,unittest
from unittest.mock import patch
from shared_child import invoke,start
class Children(unittest.TestCase):
    def test_actual_success_and_nonzero_children_normally_reaped(self):
        for code in [0,7]:
            argv=[sys.executable,'-c',f'import sys;print("original helper");sys.exit({code})']
            d=invoke(argv,dict(os.environ),time.monotonic()+5)
            self.assertEqual(d['returncode'],code);self.assertEqual(d['stdout'],'original helper\n')
            self.assertTrue(d['client_cleanup']['reaped']);self.assertTrue(d['client_cleanup']['other_group_members_absent_before_reap'])
            self.assertFalse(d['io_cpu_release_authorized'])
            with self.assertRaises(ChildProcessError):os.waitpid(d['client_cleanup']['pid'],os.WNOHANG)
    def test_actual_capture_limit_keeps_drain_and_reap(self):
        d=invoke([sys.executable,'-c','print("x"*4096)'],dict(os.environ),time.monotonic()+5,capture_limit=128)
        self.assertTrue(d['capture_truncated']);self.assertEqual(len(d['stdout']),128)
        self.assertTrue(d['client_cleanup']['reaped'])
    def test_invalid_budget_refuses_before_spawn(self):
        for args in [dict(deadline=0),dict(deadline=True),dict(deadline=float('inf')),dict(deadline=time.monotonic()+5,capture_limit=True)]:
            with self.assertRaises(ValueError):invoke(['/never-executed'],{},**args)
    def test_split_start_drains_before_finish_and_reaps_only_once(self):
        child=start([sys.executable,'-c','import sys;sys.stdout.write("x"*1048576)'],
                    dict(os.environ),capture_limit=128)
        # A pipe-sized backlog must not prevent exit while the caller owns a
        # second process. Captures must already drain before finish is called.
        self.assertTrue(child.owner.await_terminal(5))
        self.assertFalse(child.owner.reaped)
        result=child.finish(time.monotonic()+5)
        self.assertEqual(result['returncode'],0)
        self.assertTrue(result['capture_truncated'])
        self.assertEqual(len(result['stdout']),128)
        with self.assertRaises(ValueError):child.finish(time.monotonic()+5)
        with self.assertRaises(ChildProcessError):os.waitpid(child.owner.pid,os.WNOHANG)

    def test_two_split_handles_have_independent_captures_and_reaps(self):
        handles=[start([sys.executable,'-c',f'print({n})'],dict(os.environ)) for n in (1,2)]
        outcomes=[child.finish(time.monotonic()+5) for child in reversed(handles)]
        self.assertEqual([row['stdout'] for row in outcomes],['2\n','1\n'])
        self.assertTrue(all(child.owner.reaped for child in handles))

if __name__=='__main__':unittest.main()
