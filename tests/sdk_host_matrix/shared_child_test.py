"""Actual tiny original Python helpers; no SDK, payload, compiler or canonical IO."""
import os,sys,time,unittest
from unittest.mock import patch
from shared_child import invoke
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
if __name__=='__main__':unittest.main()
