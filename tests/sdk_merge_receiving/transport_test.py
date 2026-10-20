"""Original inert paired-child ownership controls; never starts any process."""
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving import transport

class Pair(unittest.TestCase):
    def call(self, fault=None):
        self.events=[]
        def finish(label):
            def result(deadline):
                self.events.append(('finish',label))
                if fault==label:raise self.original
                return dict(capture_truncated=fault=='capture',returncode=0,label=label)
            return result
        self.proxy=SimpleNamespace(finish=finish('proxy'))
        self.client=SimpleNamespace(finish=finish('client'))
        self.original=UnresolvedOwnership('inert original',retained_fds=(91,))
        handles=iter((self.proxy,self.client))
        def start(command,environment,pass_fds):
            self.events.append(('start',command[0],tuple(pass_fds)))
            if fault=='start' and command[0]=='client':raise self.original
            return next(handles)
        def ready(*args):
            self.events.append(('ready',))
            if fault=='ready':raise TimeoutError('inert readiness')
        def read():
            self.events.append(('read',))
            if fault=='read':raise ValueError('inert truncated frame')
            return dict(original='raw')
        with patch.object(transport.os,'lstat',side_effect=FileNotFoundError), \
             patch.object(transport,'start',side_effect=start), \
             patch.object(transport,'wait_socket',side_effect=ready):
            return transport.run(['client'],{},proxy_command=['proxy'],proxy_environment={},
                socket_path='/private/tmp/inert.sock',deadline=time.monotonic()+2,
                pass_fds=(91,),read_proxy=read)

    def test_both_peers_started_before_any_finish_and_same_inherited_grant(self):
        result=self.call()
        self.assertEqual(self.events[:3],[('start','proxy',(91,)),('ready',),('start','client',(91,))])
        self.assertEqual(self.events[3:],[('finish','client'),('finish','proxy'),('read',)])
        self.assertFalse(result['resource_release_authorized'])
        self.assertTrue(result['external_sdk_audit_required'])

    def test_failure_of_each_live_peer_retains_both_without_replacing_carrier(self):
        for fault in ('client','proxy'):
            with self.subTest(fault=fault),self.assertRaises(UnresolvedOwnership) as caught:self.call(fault)
            self.assertIs(caught.exception,self.original)
            self.assertEqual(caught.exception.transport_handles,[self.proxy,self.client])
            self.assertEqual(caught.exception.retained_fds,(91,))
            self.assertNotIn(('read',),self.events)

    def test_failed_client_start_keeps_proxy_and_nested_failed_start(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('start')
        self.assertIs(caught.exception,self.original)
        self.assertEqual(caught.exception.transport_handles,[self.proxy])
        self.assertFalse(any(e[0]=='finish' for e in self.events))

    def test_readiness_failure_keeps_proxy_without_starting_client(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('ready')
        self.assertEqual(caught.exception.transport_handles,[self.proxy])
        self.assertIsInstance(caught.exception.original_failure,TimeoutError)
        self.assertEqual(sum(e[0]=='start' for e in self.events),1)

    def test_capture_or_raw_frame_failure_is_not_failed_prefix_release(self):
        for fault in ('capture','read'):
            with self.subTest(fault=fault),self.assertRaises(UnresolvedOwnership) as caught:self.call(fault)
            self.assertEqual(caught.exception.transport_handles,[self.proxy,self.client])
            self.assertIsNotNone(caught.exception.transport_client_result)
            self.assertIsNotNone(caught.exception.transport_proxy_result)

if __name__=='__main__':unittest.main()
