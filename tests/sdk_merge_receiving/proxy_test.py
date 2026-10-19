"""Original tiny socket/pipe forwarding and inert native-process doubles only."""
import json
import os
import socket
import struct
import time
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership
from sdk_merge_receiving import proxy

class Pump(unittest.TestCase):
    def test_original_six_bytes_forward_and_stdin_eof_close_once(self):
        connection, peer = socket.socketpair()
        read_in,write_in=os.pipe(); read_out,write_out=os.pipe()
        owned=[read_out,write_in]
        try:
            peer.sendall(b'abc');peer.shutdown(socket.SHUT_WR)
            os.write(write_out,b'XYZ');os.close(write_out);write_out=None
            counts=proxy.pump(connection,read_out,write_in,time.monotonic()+2,owned)
            self.assertEqual(counts,dict(client_to_server_bytes=3,server_to_client_bytes=3))
            self.assertEqual(os.read(read_in,4),b'abc')
            self.assertEqual(os.read(read_in,1),b'')
            self.assertEqual(peer.recv(4),b'XYZ');self.assertEqual(peer.recv(1),b'')
            self.assertEqual(owned,[read_out])
        finally:
            # These are known test-owned handles, no injected OS close failure.
            connection.close();peer.close();os.close(read_in)
            for fd in owned:os.close(fd)
            if write_out is not None:os.close(write_out)

    def test_expiry_keeps_all_known_pipe_owners(self):
        connection,peer=socket.socketpair()
        read_in,write_in=os.pipe();read_out,write_out=os.pipe()
        owned=[read_out,write_in]
        try:
            with self.assertRaises(TimeoutError):proxy.pump(connection,read_out,write_in,0,owned)
            self.assertEqual(owned,[read_out,write_in])
            for fd in owned:self.assertTrue(os.fstat(fd))
        finally:
            connection.close();peer.close()
            for fd in (read_in,write_in,read_out,write_out):os.close(fd)

class Server(unittest.TestCase):
    def execute(self, *, expired=False, close_error=None):
        self.endpoint=Mock();self.connection=Mock();self.native=SimpleNamespace(pid=101,returncode=None)
        header=json.dumps(['/pinned/server','-server']).encode()
        self.endpoint.accept.return_value=(self.connection,None)
        self.connection.recv.side_effect=[struct.pack('>I',len(header)),header]
        self.closed=[];clock=[0]
        def pump(connection,read,write,deadline,owned):
            owned.remove(write);self.closed.append(write)
            if expired:clock[0]=2
            return dict(client_to_server_bytes=3,server_to_client_bytes=3)
        def close(fds):
            if close_error is not None:raise close_error
            self.closed.extend(fds)
        with ExitStack() as stack:
            stack.enter_context(patch.object(proxy.os,'getpid',return_value=100))
            stack.enter_context(patch.object(proxy.os,'getpgrp',return_value=100))
            stack.enter_context(patch.object(proxy.os,'getpgid',return_value=100))
            stack.enter_context(patch.object(proxy.socket,'socket',return_value=self.endpoint))
            stack.enter_context(patch.object(proxy.os,'pipe',side_effect=[(10,11),(12,13)]))
            stack.enter_context(patch.object(proxy.subprocess,'Popen',return_value=self.native))
            stack.enter_context(patch.object(proxy,'close_descriptors',side_effect=close))
            stack.enter_context(patch.object(proxy,'close_socket',side_effect=lambda s:self.closed.append(s)))
            stack.enter_context(patch.object(proxy,'pump',side_effect=pump))
            stack.enter_context(patch.object(proxy.time,'monotonic',side_effect=lambda:clock[0]))
            reap=stack.enter_context(patch.object(proxy.os,'wait4',return_value=(101,0,None)))
            stack.enter_context(patch.object(proxy.os,'waitid',return_value=None if expired else object()))
            signals=stack.enter_context(patch.object(proxy.os,'kill'))
            groups=stack.enter_context(patch.object(proxy.os,'killpg'))
            try:return proxy.serve('/private/tmp/original.sock','/pinned/server',['-semanticcpubudget','2'],1)
            finally:
                signals.assert_not_called();groups.assert_not_called()
                self.reap_calls=reap.call_count

    def test_normal_native_reap_and_all_handles_close_without_release_claim(self):
        result=self.execute()
        self.assertEqual(result['server_command'],['/pinned/server','-server','-semanticcpubudget','2'])
        self.assertEqual(self.reap_calls,1);self.assertTrue(result['server_reaped'])
        self.assertFalse(result['resource_release_authorized'])
        self.assertEqual(self.closed[:4],[10,13,11,12])

    def test_live_native_after_eof_retains_sockets_and_pipe_no_reap(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.execute(expired=True)
        error=caught.exception
        self.assertIs(error.proxy_native_child,self.native)
        self.assertEqual(error.proxy_socket_owners,[self.endpoint,self.connection])
        self.assertEqual(error.retained_fds,(12,));self.assertEqual(self.reap_calls,0)
        self.assertIsInstance(error.original_failure,TimeoutError)

    def test_nested_close_uncertainty_keeps_original_carrier_and_remaining_handles(self):
        record=dict(fd=10,role='inert',observed_before_close=None,identity_observation_error='inert')
        carrier=UnresolvedIOOwnership('injected without OS close',uncertain_closes=[record])
        with self.assertRaises(UnresolvedIOOwnership) as caught:self.execute(close_error=carrier)
        self.assertIs(caught.exception,carrier)
        self.assertEqual(carrier.uncertain_closes,(record,))
        self.assertEqual(set(carrier.retained_fds),{11,12,13})
        self.assertEqual(self.reap_calls,0)

if __name__=='__main__':unittest.main()
