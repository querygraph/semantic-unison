"""Inert handles/signal adapter only; no process or signal is issued."""
import time,unittest
from types import SimpleNamespace
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from current_validation_paths import signal_transport as target

class Cancellation(unittest.TestCase):
    def run_pair(self,fault=None):
        self.events=[];self.original=UnresolvedOwnership('original inert',retained_fds=(999,))
        def handle(label,pid):
            def terminal():
                self.events.append(('terminal',label));return fault=='already-terminal'
            def finish(deadline):
                self.events.append(('finish',label))
                if fault==label:raise self.original
                return dict(capture_truncated=fault=='truncated')
            return SimpleNamespace(owner=SimpleNamespace(pid=pid,reaped=False,terminal=terminal),finish=finish)
        self.proxy=handle('proxy',7001);self.client=handle('client',7002)
        def observe(client,deadline):
            self.events.append(('observe',client is self.client))
            if fault=='observer':raise self.original
            return dict(fabricated_helper=True)
        def kill(pid,sig):
            self.events.append(('signal',pid,int(sig)))
            if fault=='signal':raise ProcessLookupError('inert uncertain signal')
        def frame():
            self.events.append(('frame',));return dict(original='fabricated frame')
        with patch.object(target.os,'lstat',side_effect=FileNotFoundError), \
             patch.object(target,'start',side_effect=[self.proxy,self.client]), \
             patch.object(target,'wait_socket'),patch.object(target.os,'kill',side_effect=kill):
            return target.run(['client'],{},proxy_command=['proxy'],proxy_environment={},
                socket_path='/private/tmp/inert.sock',deadline=time.monotonic()+2,
                pass_fds=(100,101),read_proxy=frame,before_interrupt=observe)
    def test_signal_only_after_observer_before_both_finishes(self):
        result=self.run_pair()
        self.assertEqual(self.events,[('observe',True),('terminal','client'),('signal',7002,2),
            ('finish','client'),('finish','proxy'),('frame',)])
        self.assertFalse(result['resource_release_authorized']);self.assertFalse(result['publication_proved'])
    def test_observer_failure_retains_both_without_signal_or_finish(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_pair('observer')
        self.assertIs(caught.exception,self.original);self.assertEqual(self.events,[('observe',True)])
        self.assertEqual(caught.exception.transport_handles,[self.proxy,self.client])
        self.assertEqual(caught.exception.retained_fds,(999,100,101))
    def test_terminal_client_refuses_without_signal_or_finish(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_pair('already-terminal')
        self.assertEqual(self.events,[('observe',True),('terminal','client')])
        self.assertTrue(caught.exception.client_interrupt.attempted)
    def test_signal_uncertainty_retains_handle_and_forbids_numeric_retry(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_pair('signal')
        interrupt=caught.exception.client_interrupt
        self.assertIsNone(interrupt.record)
        with patch.object(target.os,'kill') as kill,self.assertRaises(ValueError):interrupt.send()
        kill.assert_not_called();self.assertFalse(any(e[0]=='finish' for e in self.events))
    def test_either_finish_uncertain_keeps_both_and_original_carrier(self):
        for fault in ('client','proxy'):
            with self.subTest(fault=fault),self.assertRaises(UnresolvedOwnership) as caught:self.run_pair(fault)
            self.assertIs(caught.exception,self.original)
            self.assertEqual(caught.exception.transport_handles,[self.proxy,self.client])
            self.assertTrue(caught.exception.client_interrupt.record['sent'])
            self.assertNotIn(('frame',),self.events)
    def test_truncated_capture_is_not_cancellation_settlement(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_pair('truncated')
        self.assertIsNotNone(caught.exception.transport_client_result)
        self.assertIsNotNone(caught.exception.transport_proxy_result)
        self.assertNotIn(('frame',),self.events)
    def test_signal_capability_consumed_even_when_owner_refuses(self):
        owner=SimpleNamespace(pid=True,reaped=False)
        interrupt=target.ClientInterrupt(SimpleNamespace(owner=owner))
        with patch.object(target.os,'kill') as kill:
            with self.assertRaises(ValueError):interrupt.send()
            with self.assertRaises(ValueError):interrupt.send()
            kill.assert_not_called()

if __name__=='__main__':unittest.main()
