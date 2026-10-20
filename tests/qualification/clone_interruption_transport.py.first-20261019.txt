"""Generated-only fault transport: kill one still-owned server at clone stage.

No production hook or timeout cancellation. A fresh exact proxy configuration
must name a private generated target. Any ambiguity retains the actual owners.
"""
import json,os,select,signal,socket,stat,struct,subprocess,time
from pathlib import Path
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import uncertainty_records
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.proxy import close_socket,BUFFER
from sdk_merge_receiving.launcher import header
from sdk_merge_receiving.store import Store
from sdk_host_matrix.shared_binding import descriptors


def stage(directory):
    values=list(Path(directory).glob('*clone*.unison.tmp'))
    if not values:return None
    if len(values)!=1:raise ValueError('one generated clone stage required')
    p=values[0];s=p.lstat()
    if not (stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1
            and 0<=s.st_size<=16*1048576):raise ValueError('bounded owned clone stage required')
    return dict(path=str(p),device=s.st_dev,inode=s.st_ino,size=s.st_size)


def interrupt_owned(native,proxy_pid,*,waitid=os.waitid,kill=os.kill,getpgid=os.getpgid):
    """No poll/reap before signal: reserve the exact owned PID throughout."""
    pid=native.pid
    if type(pid) is not int or pid<=0 or getpgid(pid)!=proxy_pid:
        raise ValueError('exact unreaped native member required')
    if waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is not None:
        raise ValueError('native already terminal before clone interruption')
    kill(pid,signal.SIGKILL)
    return dict(pid=pid,signal=signal.SIGKILL,owned_unreaped_before_signal=True,
                group=proxy_pid,reason='observed private clone stage; original generated-file failure control')


def pump(connection,read_fd,write_fd,deadline,owned_fds,native,directory):
    incoming=bytearray();outgoing=bytearray();client_eof=server_eof=shutdown=False
    connection.setblocking(False);os.set_blocking(read_fd,False);os.set_blocking(write_fd,False)
    counts=dict(client_to_server_bytes=0,server_to_client_bytes=0,discarded_client_bytes=0)
    event=None;next_write=0
    while not (client_eof and server_eof and not incoming and not outgoing):
        if time.monotonic()>=deadline:raise TimeoutError('interruption observation expired; no timeout signal')
        observed=stage(directory) if event is None else None
        if observed is not None:
            event=dict(stage=observed,signal=interrupt_owned(native,os.getpid()))
            counts['discarded_client_bytes']+=len(incoming);incoming.clear()
            owned_fds.remove(write_fd);close_descriptors([write_fd])
        readers=([connection] if not client_eof and len(incoming)<BUFFER else [])
        if not server_eof and len(outgoing)<BUFFER:readers.append(read_fd)
        writers=([write_fd] if incoming and event is None and time.monotonic()>=next_write else [])
        if outgoing:writers.append(connection)
        ready_read,ready_write,_=select.select(readers,writers,[],.005)
        if connection in ready_read:
            try:block=connection.recv(min(65536,BUFFER-len(incoming)))
            except BlockingIOError:block=None
            if block==b'':client_eof=True
            elif block is not None:
                if event is None:incoming.extend(block)
                else:counts['discarded_client_bytes']+=len(block)
        if read_fd in ready_read:
            try:block=os.read(read_fd,min(65536,BUFFER-len(outgoing)))
            except BlockingIOError:block=None
            if block==b'':server_eof=True
            elif block is not None:outgoing.extend(block)
        if write_fd in ready_write:
            try:n=os.write(write_fd,incoming[:4096])
            except BlockingIOError:n=None
            if n is not None:
                if n<=0:raise ValueError('native write stalled')
                del incoming[:n];counts['client_to_server_bytes']+=n;next_write=time.monotonic()+.01
        if connection in ready_write:
            try:n=connection.send(outgoing)
            except BlockingIOError:n=None
            if n is not None:
                if n<=0:raise ValueError('client write stalled')
                del outgoing[:n];counts['server_to_client_bytes']+=n
        if client_eof and not incoming and write_fd in owned_fds:
            owned_fds.remove(write_fd);close_descriptors([write_fd])
        if server_eof and not outgoing and not shutdown:
            connection.shutdown(socket.SHUT_WR);shutdown=True
    if event is None:raise ValueError('clone stage never observed; no interruption proof')
    return dict(event=event,counts=counts,client_eof_observed=True,server_eof_observed=True,
                input_eof_forwarded=False,discard_permitted_only_after_owned_signal=True)


def serve(config):
    """Single original generated run; all pipes/sockets kept on any uncertainty."""
    endpoint=connection=native=None;owned_fds=[]
    try:
        if set(config)!={'directory','identity','stage','binary','flags','deadline','worker_pid','resource_fds','target_directory'}:
            raise ValueError('exact clone interruption configuration required')
        if os.getppid()!=config['worker_pid'] or os.getpgrp()!=os.getpid():raise ValueError('actual retained proxy parent/group required')
        descriptors(config['resource_fds']);deadline=config['deadline']
        if not time.monotonic()<deadline<float('inf'):raise ValueError('fresh observation required')
        endpoint=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);endpoint.bind(config['directory']+'/'+config['stage']+'.sock');endpoint.listen(1);endpoint.settimeout(.025)
        while connection is None:
            if time.monotonic()>=deadline:raise TimeoutError('accept observation expired')
            try:connection,_=endpoint.accept()
            except socket.timeout:pass
        connection.settimeout(.025)
        def exact(n):
            raw=bytearray()
            while len(raw)<n:
                if time.monotonic()>=deadline:raise TimeoutError('header observation expired')
                try:block=connection.recv(n-len(raw))
                except socket.timeout:continue
                if not block:raise ValueError('short header')
                raw.extend(block)
            return bytes(raw)
        size=struct.unpack('>I',exact(4))[0]
        if not 0<size<=8192:raise ValueError('bounded header required')
        command=json.loads(exact(size))
        if command!=[config['binary'],'-server','__new-rpc-mode']:raise ValueError('exact native server header required')
        command+=config['flags']
        read_in,write_in=os.pipe();owned_fds.extend([read_in,write_in]);read_out,write_out=os.pipe();owned_fds.extend([read_out,write_out])
        native=subprocess.Popen(command,stdin=read_in,stdout=write_out,stderr=None,close_fds=True,start_new_session=False)
        for fd in (read_in,write_out):owned_fds.remove(fd);close_descriptors([fd])
        forwarded=pump(connection,read_out,write_in,deadline,owned_fds,native,config['target_directory'])
        while os.waitid(os.P_PID,native.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None:
            if time.monotonic()>=deadline:raise TimeoutError('owned signaled native not terminal')
            time.sleep(.005)
        pid,status,_=os.wait4(native.pid,0)
        if pid!=native.pid:raise ValueError('native reap identity differs')
        native.returncode=os.waitstatus_to_exitcode(status)
        if native.returncode!=-signal.SIGKILL:raise ValueError('exact owned interruption outcome required')
        while owned_fds:close_descriptors([owned_fds.pop()])
        close_socket(connection);connection=None;close_socket(endpoint);endpoint=None
        return dict(schema='unison-generated-clone-interruption/1',server_command=command,
            server_pid=pid,server_returncode=native.returncode,server_reaped=True,server_group=os.getpid(),
            transport=forwarded,resource_release_authorized=False)
    except BaseException as error:
        carrier=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('clone interruption unresolved; retain actual server, pipes and sockets')
        if carrier is not error:carrier.original_failure=error
        carrier.interrupted_native=native;carrier.socket_owners=[x for x in (endpoint,connection) if x is not None]
        carrier.retained_fds=tuple(dict.fromkeys((*carrier.retained_fds,*owned_fds)))
        raise carrier from error if carrier is not error else None


def proxy_main(config):
    store=None
    try:
        store=Store(config['directory'],config['identity']);record=serve(config)
        store.write(config['stage']+'-PROXY.json',record);store.close();return 0
    except BaseException as error:
        retain_after_record(lambda:print('CLONE_INTERRUPT_PROXY_RETAIN',repr(error),flush=True))


def launcher_main():
    """Test-only peer-abort launcher; explicitly discards unsent bytes on EOF.

    Never used by ordinary transfers. Remote EOF is propagated to Unison; no
    successful protocol completion is inferred and no native child lives here.
    """
    connection=None
    try:
        binary=os.environ['UNISON_MERGE_BINARY'];deadline=float(os.environ['UNISON_MERGE_DEADLINE'])
        connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connection.connect(os.environ['UNISON_MERGE_SOCKET']);connection.sendall(header(__import__('sys').argv[1:],binary))
        connection.setblocking(False);os.set_blocking(0,False);os.set_blocking(1,False)
        incoming=bytearray();outgoing=bytearray();local_eof=remote_eof=shutdown=False
        while not remote_eof or incoming:
            if time.monotonic()>=deadline:raise TimeoutError('test launcher observation expired')
            readers=([0] if not local_eof and not remote_eof and len(outgoing)<BUFFER else [])+([connection] if not remote_eof and len(incoming)<BUFFER else [])
            writers=([1] if incoming else [])+([connection] if outgoing and not remote_eof else [])
            rr,ww,_=select.select(readers,writers,[],.025)
            if 0 in rr:
                try:block=os.read(0,min(65536,BUFFER-len(outgoing)))
                except BlockingIOError:block=None
                if block==b'':local_eof=True
                elif block is not None:outgoing.extend(block)
            if connection in rr:
                try:block=connection.recv(min(65536,BUFFER-len(incoming)))
                except BlockingIOError:block=None
                if block==b'':remote_eof=True;outgoing.clear()
                elif block is not None:incoming.extend(block)
            if 1 in ww:
                n=os.write(1,incoming)
                if n<=0:raise ValueError('launcher stdout stalled')
                del incoming[:n]
            if connection in ww and not remote_eof:
                n=connection.send(outgoing)
                if n<=0:raise ValueError('launcher socket stalled')
                del outgoing[:n]
            if local_eof and not outgoing and not shutdown and not remote_eof:connection.shutdown(socket.SHUT_WR);shutdown=True
        close_socket(connection);connection=None;return 0
    except BaseException as error:
        retain_after_record(lambda:print('CLONE_INTERRUPT_LAUNCHER_RETAIN',repr(error),flush=True))
