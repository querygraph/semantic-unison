"""Retained loopback server kernel; no standalone CLI or execution admission.

The admitted proxy process must be a retained session leader. Its caller retains
this kernel's exception, native child, socket objects and inherited resource FDs;
it must never unwind/exit on an unresolved result. No cancellation signals here.
"""
import json
import errno
import os
import select
import socket
import struct
import subprocess
import time
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership, descriptor_observation
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.plan import require

BUFFER = 262144



def finish_write(connection, *, client_eof, server_eof, incoming, outgoing):
    """Already-disconnected is benign only after both EOFs and drained queues.

    This establishes no process status or FD close outcome. Native wait4 and
    every qualified close remain mandatory after forwarding finishes.
    """
    try: connection.shutdown(socket.SHUT_WR)
    except OSError as error:
        if not (error.errno == errno.ENOTCONN and client_eof and server_eof
                and not incoming and not outgoing):
            raise


def pump(connection, read_fd, write_fd, deadline, owned_fds):
    """Bounded bidirectional forwarding; EOF is not native process settlement."""
    incoming = bytearray(); outgoing = bytearray()
    client_eof = server_eof = write_shutdown = False
    connection.setblocking(False)
    os.set_blocking(read_fd, False); os.set_blocking(write_fd, False)
    counts = dict(client_to_server_bytes=0, server_to_client_bytes=0)
    try:
        while not (client_eof and server_eof and not incoming and not outgoing):
            if time.monotonic() >= deadline:
                raise TimeoutError('protocol observation expired; retain without signals')
            readers = ([] if client_eof or len(incoming) >= BUFFER else [connection])
            if not server_eof and len(outgoing) < BUFFER:
                readers.append(read_fd)
            writers = ([write_fd] if incoming else []) + ([connection] if outgoing else [])
            ready_read, ready_write, _ = select.select(readers, writers, [], .025)
            if connection in ready_read:
                try: block = connection.recv(min(65536, BUFFER-len(incoming)))
                except BlockingIOError: block = None
                if block == b'': client_eof = True
                elif block is not None: incoming.extend(block)
            if read_fd in ready_read:
                try: block = os.read(read_fd, min(65536, BUFFER-len(outgoing)))
                except BlockingIOError: block = None
                if block == b'': server_eof = True
                elif block is not None: outgoing.extend(block)
            if write_fd in ready_write:
                try: count = os.write(write_fd, incoming)
                except BlockingIOError: count = None
                if count is not None:
                    require(count > 0, 'zero-byte native input write')
                    counts['client_to_server_bytes'] += count; del incoming[:count]
            if connection in ready_write:
                try: count = connection.send(outgoing)
                except BlockingIOError: count = None
                if count is not None:
                    require(count > 0, 'zero-byte client protocol write')
                    counts['server_to_client_bytes'] += count; del outgoing[:count]
            if client_eof and not incoming and write_fd in owned_fds:
                # Transfer out of known-close list before attempting the close.
                # A close exception's carrier owns its uncertain numeric identity.
                owned_fds.remove(write_fd)
                close_descriptors([write_fd])
            if server_eof and not outgoing and not write_shutdown:
                finish_write(connection, client_eof=client_eof, server_eof=server_eof,
                             incoming=incoming, outgoing=outgoing); write_shutdown = True
        return counts
    except BaseException as error:
        error.proxy_pump_state = dict(client_eof=client_eof,server_eof=server_eof,
            input_queue_bytes=len(incoming),output_queue_bytes=len(outgoing),
            write_shutdown=write_shutdown,counts=dict(counts),errno=getattr(error,'errno',None))
        raise



def close_socket(value):
    observation = descriptor_observation(value.fileno(), 'merge_proxy_socket')
    try: value.close()
    except BaseException as error:
        raise UnresolvedIOOwnership('proxy socket close unknown; no retry',
            uncertain_closes=[observation], close_failure=error) from error


def serve(socket_path, binary, flags, deadline):
    """One header, one native child, normal wait4; caller owns all admissions.

    Failure, even before dispatch, carries every owner rather than inferring a
    safe no-helper prefix. Socket paths/files are private and never auto-unlinked.
    """
    require(type(deadline) in (int,float) and time.monotonic() < deadline < float('inf'),
            'fresh finite proxy observation required')
    require(type(flags) is list and all(type(x) is str for x in flags), 'exact server flags required')
    require(os.getpgrp() == os.getpid(), 'proxy must own its retained session group')
    endpoint = connection = native = None
    owned_fds = []
    command = None
    phase = 'listener'
    try:
        endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        endpoint.bind(socket_path); endpoint.listen(1); endpoint.settimeout(.025)
        while connection is None:
            if time.monotonic() >= deadline: raise TimeoutError('proxy accept expired')
            try: connection, _ = endpoint.accept()
            except socket.timeout: pass
        phase = 'header'
        connection.settimeout(.025)
        def exact(length):
            result = bytearray()
            while len(result) < length:
                if time.monotonic() >= deadline: raise TimeoutError('proxy header expired')
                try: block = connection.recv(length-len(result))
                except socket.timeout: continue
                if not block: raise ValueError('short proxy header')
                result.extend(block)
            return bytes(result)
        length = struct.unpack('>I', exact(4))[0]
        require(0 < length <= 8192, 'bounded launcher header required')
        arguments = json.loads(exact(length))
        require(type(arguments) is list and arguments == [binary,'-server','__new-rpc-mode'],
                'exact expected native server header required')
        command = arguments + flags
        read_in, write_in = os.pipe(); owned_fds.extend([read_in,write_in])
        read_out, write_out = os.pipe(); owned_fds.extend([read_out,write_out])
        phase = 'native_start'
        native = subprocess.Popen(command, stdin=read_in, stdout=write_out, stderr=None,
                                  close_fds=True, start_new_session=False)
        native_pid = native.pid
        require(os.getpgid(native_pid) == os.getpid(), 'server not in retained proxy group')
        for fd in (read_in,write_out):
            owned_fds.remove(fd); close_descriptors([fd])
        phase = 'forwarding'
        counts = pump(connection, read_out, write_in, deadline, owned_fds)
        # Keep the native PID reserved until normal terminal status is observed.
        phase = 'native_terminal'
        while os.waitid(os.P_PID,native_pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None:
            if time.monotonic() >= deadline: raise TimeoutError('native terminal observation expired')
            time.sleep(.005)
        phase = 'native_reap'
        pid,status,_ = os.wait4(native_pid,0)
        require(pid == native_pid, 'native reap identity differs')
        native.returncode = os.waitstatus_to_exitcode(status)
        phase = 'pipe_close'
        while owned_fds:
            fd = owned_fds.pop(); close_descriptors([fd])
        phase = 'socket_close'
        close_socket(connection); connection = None
        close_socket(endpoint); endpoint = None
        return dict(schema='unison-retained-merge-proxy/1', server_command=command,
            server_pid=pid, server_returncode=native.returncode, server_reaped=True,
            server_group=os.getpid(), input_eof_forwarded=True, output_eof_forwarded=True,
            forwarded_protocol_bytes=counts, parent_group_audit_required=True,
            sdk_helper_audit_required=True, resource_release_authorized=False)
    except BaseException as error:
        # Preserve nested descriptor uncertainty without inspecting/retrying it.
        if isinstance(error,UnresolvedOwnership): retained = error
        else:
            retained = UnresolvedOwnership('proxy unresolved; retain child, sockets and inherited resources')
            retained.original_failure = error
        retained.proxy_failure_phase = phase
        retained.proxy_pump_state = getattr(error,'proxy_pump_state',None)
        retained.proxy_original_errno = getattr(error,'errno',None)
        retained.proxy_native_child = native
        retained.proxy_socket_owners = [x for x in (endpoint,connection) if x is not None]
        retained.retained_fds = tuple(dict.fromkeys((*retained.retained_fds,*owned_fds)))
        retained.proxy_command = command
        if retained is error:
            raise
        raise retained from error
