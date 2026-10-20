"""Fake owner/OS controls; no native processes, signals, canonical locks or IO."""
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from mixed_peer_compatibility import coordinator as c
from shared_cpu_pool import UnresolvedOwnership

class Coordinator(unittest.TestCase):
    def setUp(self):
        self.events=[];self.owner=types.SimpleNamespace(pid=123,reaped=False,process=types.SimpleNamespace(returncode=None),
             await_terminal=lambda t:self.event('observe',True),terminal=lambda:self.event('terminal',True))
    def event(self,name,value):self.events.append(name);return value
    def run_case(self,audit=None,rows=None,status=0):
        with patch.object(c,'audit_saved',side_effect=lambda *args:self.event('audit',audit or {'functional':'PASS'})),patch.object(c,'members',side_effect=lambda pid:self.event('census',rows or [{'pid':123,'state':'Z'}])),patch.object(c.os,'wait4',side_effect=lambda *args:self.event('wait',(123,status,None))):
            return c.observe_and_reap(self.owner,lambda:self.event('read',{}),{},'/inert',time.monotonic()+1)
    def test_order(self):
        self.assertTrue(self.run_case()['functional_pass'])
        self.assertEqual(self.events,['observe','read','audit','census','terminal','wait'])
    def test_failed_prefix_closed(self):
        self.assertFalse(self.run_case(audit={'functional':'FAILED_OR_INCOMPLETE'},status=256)['functional_pass'])
        self.assertTrue(self.owner.reaped)
    def test_exit_contradiction_failed_closed(self):
        self.assertFalse(self.run_case(status=256)['functional_pass'])
        self.assertTrue(self.owner.reaped)
    def test_observation_timeout_no_audit_or_wait(self):
        self.owner.await_terminal=lambda _:False
        with self.assertRaises(UnresolvedOwnership) as error:self.run_case()
        self.assertIs(error.exception.mixed_peer_worker,self.owner)
        self.assertNotIn('wait',self.events)
    def test_unknown_audit_preserves_actual_carrier(self):
        original=UnresolvedOwnership('unknown close',retained_fds=(999,))
        with patch.object(c,'audit_saved',side_effect=original),patch.object(c.os,'wait4') as wait:
            with self.assertRaises(UnresolvedOwnership) as error:
                c.observe_and_reap(self.owner,lambda:{},{},'/inert',time.monotonic()+1)
        self.assertIs(error.exception,original);wait.assert_not_called()
    def test_live_group_not_reaped(self):
        with patch.object(c,'audit_saved',return_value={'functional':'PASS'}),patch.object(c,'members',return_value=[{'pid':999,'state':'S'}]),patch.object(c.os,'wait4') as wait:
            with self.assertRaises(UnresolvedOwnership):c.observe_and_reap(self.owner,lambda:{},{},'/inert',time.monotonic()-1)
        wait.assert_not_called()
if __name__=='__main__':unittest.main()
