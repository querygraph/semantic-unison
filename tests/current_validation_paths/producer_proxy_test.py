"""Inert sockets, FDs, direct-native handles and signal adapters only."""
import json,os,signal,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from current_validation_paths import producer_proxy as target

class Pump(unittest.TestCase):
    def call(self,fault=None):
        self.events=[];self.fds=[701,702]
        blocks=iter((b'client protocol bytes',b''));reads=iter((b'server protocol bytes',b''));observations=iter((None,dict(original='durable stage')))
        connection=SimpleNamespace(setblocking=lambda _:None,recv=lambda n:next(blocks),
            send=lambda data:len(data),shutdown=lambda _:self.events.append('shutdown'))
        def observe():return None if fault=='no-event' else next(observations)
        def release(sent):
            self.events.append('release')
            if fault=='release':raise self.original
            return dict(copy_fixture_released=True,producer_signalled=False)
        observer=SimpleNamespace(observe=observe,release=release)
        self.original=UnresolvedOwnership('original inert uncertainty',retained_fds=(999,))
        def interrupt(native,group):
            self.events.append('signal-owned-receiver')
            if fault=='signal':raise self.original
            return dict(pid=200,signal=9,owned_unreaped_before_signal=True,group=100)
        def close(fds):
            self.events.append(('close',tuple(fds)))
            if fault=='close':
                self.original.uncertain_fds=tuple(fds);self.original.uncertain_closes=tuple(dict(fd=fd,device=1,inode=fd,role='inert-close') for fd in fds)
                raise self.original
        with patch.object(target.os,'set_blocking'),patch.object(target.os,'read',side_effect=lambda fd,n:next(reads)), \
             patch.object(target.os,'write',side_effect=lambda fd,data:len(data)), \
             patch.object(target.select,'select',side_effect=lambda readers,writers,errors,timeout:(readers,writers,[])), \
             patch.object(target,'interrupt_owned',side_effect=interrupt),patch.object(target,'close_descriptors',side_effect=close):
            return target.pump(connection,701,702,time.monotonic()+2,self.fds,SimpleNamespace(pid=200),observer)
    def test_durable_stage_then_owned_receiver_signal_then_producer_release(self):
        result=self.call();self.assertEqual(self.events[:3],['signal-owned-receiver','release',('close',(702,))])
        self.assertEqual(result['counts']['discarded_client_bytes'],len(b'client protocol bytes'))
        self.assertEqual(result['counts']['server_to_client_bytes'],len(b'server protocol bytes'))
        self.assertFalse(result['input_eof_forwarded']);self.assertEqual(self.fds,[701])
    def test_signal_uncertainty_never_releases_producer_or_closes_input(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('signal')
        self.assertIs(caught.exception,self.original);self.assertEqual(self.events,['signal-owned-receiver'])
        self.assertIsNone(caught.exception.producer_event['signal']);self.assertEqual(self.fds,[701,702])
    def test_release_uncertainty_preserves_actual_signal_event(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('release')
        self.assertIs(caught.exception,self.original);self.assertEqual(caught.exception.producer_event['signal']['pid'],200)
        self.assertEqual(self.events,['signal-owned-receiver','release']);self.assertEqual(self.fds,[701,702])
    def test_input_close_uncertainty_not_retried_and_retains_event(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('close')
        self.assertIs(caught.exception,self.original);self.assertEqual(self.fds,[701])
        self.assertTrue(caught.exception.producer_event['release']['copy_fixture_released'])
        self.assertEqual(self.events.count(('close',(702,))),1)
    def test_no_stage_means_no_signal_or_interruption_receipt(self):
        with self.assertRaisesRegex(ValueError,'no durable stage'):self.call('no-event')
        self.assertNotIn('signal-owned-receiver',self.events)

class Kernel(unittest.TestCase):
    def call(self,fault=None):
        self.events=[];header=json.dumps(['/inert/unison','-server','__new-rpc-mode']).encode();wire=bytearray(len(header).to_bytes(4,'big')+header)
        def recv(n):value=bytes(wire[:n]);del wire[:n];return value
        connection=SimpleNamespace(settimeout=lambda _:None,recv=recv)
        endpoint=SimpleNamespace(bind=lambda _:None,listen=lambda _:None,settimeout=lambda _:None,accept=lambda:(connection,None))
        self.native=SimpleNamespace(pid=200,returncode=None)
        self.observer=SimpleNamespace(files=SimpleNamespace(fd=500,closed=False),close=lambda:self.events.append('observer-close'))
        config=dict(directory='/private/tmp/inert',identity=dict(device=1,inode=2),stage='one',binary='/inert/unison',flags=[],
            deadline=time.monotonic()+2,worker_pid=900,resource_fds=[],producer_observer=dict(inert=True))
        self.original=UnresolvedOwnership('original inert native/FD failure',retained_fds=(999,))
        def close(fds):
            self.events.append(('close',tuple(fds)))
            if fault=='close':
                self.original.uncertain_fds=tuple(fds);self.original.uncertain_closes=tuple(dict(fd=fd,device=1,inode=fd,role='inert-close') for fd in fds)
                raise self.original
        def popen(*args,**kwargs):
            self.events.append('native-start')
            if fault=='start':raise self.original
            return self.native
        def pump(*args):
            self.events.append('pump')
            if fault=='pump':raise self.original
            return dict(original='fabricated owned interruption')
        with patch.object(target.os,'getppid',return_value=900),patch.object(target.os,'getpgrp',return_value=100), \
             patch.object(target.os,'getpid',return_value=100),patch.object(target.os,'getpgid',return_value=100), \
             patch.object(target,'descriptors'),patch.object(target,'Observer',return_value=self.observer), \
             patch.object(target.socket,'socket',return_value=endpoint),patch.object(target.os,'pipe',side_effect=[(700,701),(702,703)]), \
             patch.object(target.subprocess,'Popen',side_effect=popen),patch.object(target,'close_descriptors',side_effect=close), \
             patch.object(target,'pump',side_effect=pump),patch.object(target.os,'waitid',return_value=object()), \
             patch.object(target.os,'wait4',return_value=(200,9,None)),patch.object(target,'close_socket',side_effect=lambda s:self.events.append('socket-close')):
            return target.serve(config)
    def test_exact_owned_native_reap_and_all_metadata_closes_before_frame(self):
        frame=self.call();self.assertEqual(frame['server_returncode'],-9);self.assertTrue(frame['server_reaped'])
        self.assertEqual(frame['schema'],'unison-generated-producer-interruption/1')
        self.assertFalse(frame['resource_release_authorized']);self.assertEqual(self.events[-1],'observer-close')
    def test_failed_start_retains_pipe_and_observer_owners(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('start')
        self.assertIs(caught.exception,self.original);self.assertIsNone(caught.exception.interrupted_native)
        self.assertTrue({999,500,700,701,702,703}<=set(caught.exception.retained_fds))
        self.assertNotIn('observer-close',self.events)
    def test_uncertain_first_pipe_close_retains_native_no_numeric_retry(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('close')
        self.assertIs(caught.exception.interrupted_native,self.native)
        self.assertNotIn(700,caught.exception.retained_fds);self.assertEqual(caught.exception.uncertain_fds,(700,));self.assertEqual(self.events.count(('close',(700,))),1)
        self.assertNotIn('observer-close',self.events)
    def test_pump_failure_keeps_same_native_socket_and_observer_owners(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('pump')
        self.assertIs(caught.exception,self.original);self.assertIs(caught.exception.interrupted_native,self.native)
        self.assertEqual(len(caught.exception.socket_owners),2);self.assertIn(500,caught.exception.retained_fds)
        self.assertNotIn('observer-close',self.events)

if __name__=='__main__':unittest.main()
