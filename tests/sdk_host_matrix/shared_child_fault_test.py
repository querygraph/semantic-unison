"""Inert owners and capture doubles; injected close failures never call close."""
import os,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
import shared_child as c
class Faults(unittest.TestCase):
    def setUp(self):
        self.streams=[open('/dev/null','rb'),open('/dev/null','rb')]
        self.owner=SimpleNamespace(pid=900001,reaped=False,process=SimpleNamespace(stdout=self.streams[0],stderr=self.streams[1],returncode=None),await_terminal=lambda t:True)
        self.captures=[SimpleNamespace(finish=lambda:dict(text='',truncated=False)),SimpleNamespace(finish=lambda:dict(text='',truncated=False))]
    def tearDown(self):
        # All injected failures occur before any OS close; this fixture still
        # knows its own devnull FD ownership. No real uncertain numeric retry.
        for stream in self.streams:
            if not stream.closed:stream.close()
    def call(self,*,terminal=True,census=None,captures=None,wait=None):
        self.owner.await_terminal=lambda t:terminal
        with patch.object(c,'OwnedGroup',return_value=self.owner),patch.object(c,'CapturedStream',side_effect=captures or self.captures), \
             patch.object(c.subprocess,'run',return_value=census or SimpleNamespace(returncode=0,stderr='',stdout='900001 900001 Z\n')), \
             patch.object(c.os,'wait4',side_effect=wait or [(900001,0,None)]) as reap,patch.object(c.os,'killpg') as signal:
            try:
                with self.assertRaises(c.UnresolvedIOOwnership) as caught:c.invoke(['/inert'],{},time.monotonic()+.01)
                self.error=caught.exception
            finally:self.wait_calls=reap.call_count;signal.assert_not_called()
        self.assertIs(self.error.child_owner,self.owner)
    def test_live_observation_retains_without_reap_or_signals(self):
        self.call(terminal=False);self.assertEqual(self.wait_calls,0)
        self.assertEqual(set(self.error.retained_fds),{s.fileno() for s in self.streams})
    def test_unknown_group_keeps_reserved_leader(self):
        self.call(census=SimpleNamespace(returncode=1,stderr='failed',stdout=''))
        self.assertEqual(self.wait_calls,0);self.assertFalse(self.owner.reaped)
    def test_partial_capture_construction_preserves_first_capture(self):
        self.call(captures=[self.captures[0],RuntimeError('second capture failed')])
        self.assertEqual(self.wait_calls,0);self.assertEqual(self.error.capture_owners,[self.captures[0]])
    def test_close_uncertainty_preserves_preclose_identity_no_retry(self):
        failure=OSError('injected before close');calls=[]
        def fail():calls.append(1);raise failure
        self.captures[0].finish=fail;self.call()
        self.assertEqual(self.wait_calls,1);self.assertEqual(calls,[1])
        self.assertEqual(self.error.uncertain_fds,(self.streams[0].fileno(),))
        self.assertIn(self.streams[1].fileno(),self.error.retained_fds)
        self.assertIs(self.error.original_failure,failure)
    def test_nested_uncertainty_keeps_child_and_original_record(self):
        record=c.descriptor_observation(self.streams[0].fileno(),'injected_nested')
        original=c.UnresolvedIOOwnership('nested',uncertain_closes=[record])
        self.call(captures=[original])
        self.assertEqual(self.wait_calls,0);self.assertIs(self.error.original_failure,original)
        self.assertEqual(len(self.error.uncertain_closes),1)
        enriched=self.error.uncertain_closes[0]
        self.assertEqual(enriched['upstream_observation'],record)
        self.assertEqual(enriched['role'],'shared_sdk_capture')
        self.assertEqual(enriched['fd'],record['fd'])
        self.assertEqual(enriched['observed_before_close'],record['observed_before_close'])
        self.assertNotIn(record['fd'],self.error.retained_fds)
    def test_observer_failure_retains_without_reap_or_signal(self):
        original=RuntimeError('injected query failure');observer=SimpleNamespace()
        def fail():raise original
        observer.sample=fail;self.owner.terminal=lambda:False
        with patch.object(c,'OwnedGroup',return_value=self.owner), \
             patch.object(c,'CapturedStream',side_effect=self.captures), \
             patch.object(c.os,'wait4') as reap,patch.object(c.os,'killpg') as signal:
            with self.assertRaises(c.UnresolvedIOOwnership) as caught:
                c.invoke(['/inert'],{},time.monotonic()+1,observation_factory=lambda _:observer)
            reap.assert_not_called();signal.assert_not_called()
        self.assertIs(caught.exception.process_observer,observer)
        self.assertIs(caught.exception.original_failure,original)
        self.assertFalse(self.owner.reaped)
    def test_invalid_finish_of_launched_child_retains_every_owner(self):
        with patch.object(c,'OwnedGroup',return_value=self.owner), \
             patch.object(c,'CapturedStream',side_effect=self.captures), \
             patch.object(c.os,'wait4') as reap,patch.object(c.os,'killpg') as signal:
            child=c.start(['/inert'],{})
            with self.assertRaises(c.UnresolvedIOOwnership) as caught:child.finish(0)
            reap.assert_not_called();signal.assert_not_called()
        self.assertIs(caught.exception.child_owner,self.owner)
        self.assertEqual(caught.exception.capture_owners,self.captures)
        self.assertEqual(set(caught.exception.retained_fds),{s.fileno() for s in self.streams})
        self.assertFalse(self.owner.reaped)

if __name__=='__main__':unittest.main()
