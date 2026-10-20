"""Bounded thread-free launcher kernel; callable only by its admitted peer.

No ssh process, subprocess, SDK or automatic resource release. A failed launch
retains its socket owner; the executable shim must retain that exception rather
than exit while a remote helper may still be owned by the paired proxy.
"""
import json
import os
import select
import socket
import struct
import time
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.plan import require
from sdk_merge_receiving.proxy import BUFFER, close_socket


def header(arguments,binary):
    require(type(arguments) is list and all(type(x) is str for x in arguments),
            'typed launcher arguments required')
    require(arguments.count(binary)==1,'exact one server binary in launcher arguments required')
    command=arguments[arguments.index(binary):]
    require(command==[binary,'-server','__new-rpc-mode'],'exact native RPC suffix required')
    raw=json.dumps(command,separators=(',',':')).encode()
    require(len(raw)<=8192,'bounded server command header required')
    return struct.pack('>I',len(raw))+raw


def forward(connection,input_fd,output_fd,deadline):
    incoming=bytearray();outgoing=bytearray()
    local_eof=remote_eof=shutdown=False
    connection.setblocking(False);os.set_blocking(input_fd,False);os.set_blocking(output_fd,False)
    counts=dict(local_to_remote_bytes=0,remote_to_local_bytes=0)
    while True:
        if time.monotonic()>=deadline:raise TimeoutError('launcher observation expired')
        readers=([input_fd] if not local_eof and len(outgoing)<BUFFER else [])
        if not remote_eof and len(incoming)<BUFFER:readers.append(connection)
        writers=([output_fd] if incoming else [])+([connection] if outgoing else [])
        ready_read,ready_write,_=select.select(readers,writers,[],.025)
        if input_fd in ready_read:
            try:block=os.read(input_fd,min(65536,BUFFER-len(outgoing)))
            except BlockingIOError:block=None
            if block==b'':local_eof=True
            elif block is not None:outgoing.extend(block)
        if connection in ready_read:
            try:block=connection.recv(min(65536,BUFFER-len(incoming)))
            except BlockingIOError:block=None
            if block==b'':remote_eof=True
            elif block is not None:incoming.extend(block)
        if output_fd in ready_write:
            try:count=os.write(output_fd,incoming)
            except BlockingIOError:count=None
            if count is not None:
                require(count>0,'zero launcher output write')
                del incoming[:count];counts['remote_to_local_bytes']+=count
        if connection in ready_write:
            try:count=connection.send(outgoing)
            except BlockingIOError:count=None
            if count is not None:
                require(count>0,'zero launcher protocol send')
                del outgoing[:count];counts['local_to_remote_bytes']+=count
        if local_eof and not outgoing and not shutdown:
            connection.shutdown(socket.SHUT_WR);shutdown=True
        if remote_eof and not incoming:
            require(not outgoing,'server ended before queued input was forwarded')
            return counts


def launch(arguments,binary,socket_path,deadline,*,input_fd=0,output_fd=1):
    command_header=header(arguments,binary)
    require(type(deadline) in (int,float) and time.monotonic()<deadline<float('inf'),
            'fresh finite launcher observation required')
    connection=None
    try:
        connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        connection.settimeout(max(.001,min(10,deadline-time.monotonic())))
        connection.connect(socket_path);connection.sendall(command_header)
        result=forward(connection,input_fd,output_fd,deadline)
        close_socket(connection);connection=None
        return result
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'launcher transport unresolved; paired proxy/resources must remain owned')
        if retained is not error:retained.original_failure=error
        retained.launcher_socket_owner=connection
        if retained is error:raise
        raise retained from error
