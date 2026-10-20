"""Original tiny protocol bytes and inert socket failures; no process or SDK."""
import json
import os
import socket
import struct
import time
import unittest
from unittest.mock import Mock,patch
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving import launcher

class Launcher(unittest.TestCase):
    def test_exact_rpc_suffix_and_bounded_header(self):
        result=launcher.header(['localhost','-e','none','/original/server','-server','__new-rpc-mode'],
                               '/original/server')
        count=struct.unpack('>I',result[:4])[0]
        self.assertEqual(len(result)-4,count)
        self.assertEqual(json.loads(result[4:]),['/original/server','-server','__new-rpc-mode'])
        for arguments in (['/different/server','-server','__new-rpc-mode'],
                ['/original/server','-server','__new-rpc-mode','-root','/escape'],
                ['/original/server','/original/server','-server','__new-rpc-mode']):
            with self.assertRaises(ValueError):launcher.header(arguments,'/original/server')

    def test_thread_free_forwarding_with_original_pipe_and_socket_bytes(self):
        connection,peer=socket.socketpair();read_in,write_in=os.pipe();read_out,write_out=os.pipe()
        try:
            os.write(write_in,b'abc');os.close(write_in);write_in=None
            peer.sendall(b'XYZ');peer.shutdown(socket.SHUT_WR)
            counts=launcher.forward(connection,read_in,write_out,time.monotonic()+2)
            self.assertEqual(counts,dict(local_to_remote_bytes=3,remote_to_local_bytes=3))
            self.assertEqual(peer.recv(4),b'abc');self.assertEqual(peer.recv(1),b'')
            self.assertEqual(os.read(read_out,3),b'XYZ')
            # Input/output descriptors remain caller-owned, not implicitly closed.
            self.assertTrue(os.fstat(read_in));self.assertTrue(os.fstat(write_out))
        finally:
            connection.close();peer.close()
            for fd in (read_in,write_in,read_out,write_out):
                if fd is not None:os.close(fd)

    def test_socket_failure_retains_owner_and_original_without_close_retry(self):
        connection=Mock();original=OSError('injected before connect')
        connection.connect.side_effect=original
        with patch.object(launcher.socket,'socket',return_value=connection):
            with self.assertRaises(UnresolvedOwnership) as caught:
                launcher.launch(['/original/server','-server','__new-rpc-mode'],
                                '/original/server','/private/tmp/inert.sock',time.monotonic()+1)
        self.assertIs(caught.exception.launcher_socket_owner,connection)
        self.assertIs(caught.exception.original_failure,original)
        connection.close.assert_not_called()

if __name__=='__main__':unittest.main()
