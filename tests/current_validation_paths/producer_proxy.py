"""Generated-stage receiver-crash proxy; no SDK, admission or timeout kill.

The direct native receiver remains unreaped while the exact durable stage is
observed. Only then is that owned child SIGKILLed, followed by a one-use marker
letting the external copy fixture return normally to its native supervisor.
No counter/helper PID is ever signalled. All ambiguous outcomes retain owners.
"""
import json,os,select,signal,socket,struct,subprocess,time
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.proxy import close_socket,BUFFER
from sdk_merge_receiving.store import Store
from sdk_host_matrix.shared_binding import descriptors
from clone_interruption_transport import interrupt_owned as interrupt_reserved
from current_validation_paths.producer_observation import Observer


def interrupt_owned(native,proxy_pid):
    sent=interrupt_reserved(native,proxy_pid)
    return dict(sent,reason='observed generated external-copy stage; owned receiver interruption')


def pump(connection,read_fd,write_fd,deadline,owned_fds,native,observer):
    incoming=bytearray();outgoing=bytearray();client_eof=server_eof=shutdown=False
    connection.setblocking(False);os.set_blocking(read_fd,False);os.set_blocking(write_fd,False)
    counts=dict(client_to_server_bytes=0,server_to_client_bytes=0,discarded_client_bytes=0)
    event=None
    try:
        while not (client_eof and server_eof and not incoming and not outgoing):
            if time.monotonic()>=deadline:raise TimeoutError('producer interruption observation expired; retain without signals')
            observed=observer.observe() if event is None else None
            if observed is not None:
                # This helper consumes the actual unreaped Popen owned by this
                # proxy, validates its group, and never accepts a counter PID.
                event=dict(stage=observed,signal=None,release=None)
                sent=interrupt_owned(native,os.getpid());event['signal']=sent
                event['release']=observer.release(sent)
                counts['discarded_client_bytes']+=len(incoming);incoming.clear()
                owned_fds.remove(write_fd);close_descriptors([write_fd])
            readers=([connection] if not client_eof and len(incoming)<BUFFER else [])
            if not server_eof and len(outgoing)<BUFFER:readers.append(read_fd)
            writers=([write_fd] if incoming and event is None else [])
            if outgoing:writers.append(connection)
            rr,ww,_=select.select(readers,writers,[],.005)
            if connection in rr:
                try:block=connection.recv(min(65536,BUFFER-len(incoming)))
                except BlockingIOError:block=None
                if block==b'':client_eof=True
                elif block is not None:
                    if event is None:incoming.extend(block)
                    else:counts['discarded_client_bytes']+=len(block)
            if read_fd in rr:
                try:block=os.read(read_fd,min(65536,BUFFER-len(outgoing)))
                except BlockingIOError:block=None
                if block==b'':server_eof=True
                elif block is not None:outgoing.extend(block)
            if write_fd in ww:
                try:n=os.write(write_fd,incoming)
                except BlockingIOError:n=None
                if n is not None:
                    if n<=0:raise ValueError('native input stalled')
                    del incoming[:n];counts['client_to_server_bytes']+=n
            if connection in ww:
                try:n=connection.send(outgoing)
                except BlockingIOError:n=None
                if n is not None:
                    if n<=0:raise ValueError('client output stalled')
                    del outgoing[:n];counts['server_to_client_bytes']+=n
            if client_eof and not incoming and write_fd in owned_fds:
                owned_fds.remove(write_fd);close_descriptors([write_fd])
            if server_eof and not outgoing and not shutdown:connection.shutdown(socket.SHUT_WR);shutdown=True
        if event is None:raise ValueError('no durable stage observed; no interruption qualified')
        return dict(event=event,counts=counts,client_eof_observed=True,server_eof_observed=True,
            input_eof_forwarded=False,discard_permitted_only_after_owned_signal=True)
    except BaseException as error:
        error.producer_event=event
        error.producer_pump_state=dict(client_eof=client_eof,server_eof=server_eof,counts=dict(counts),
            incoming_bytes=len(incoming),outgoing_bytes=len(outgoing))
        raise


def serve(config):
    expected={'directory','identity','stage','binary','flags','deadline','worker_pid','resource_fds','producer_observer'}
    if set(config)!=expected:raise ValueError('exact generated producer proxy configuration required')
    if os.getppid()!=config['worker_pid'] or os.getpgrp()!=os.getpid():raise ValueError('actual retained proxy parent/group required')
    descriptors(config['resource_fds']);deadline=config['deadline']
    if type(deadline) not in (int,float) or not time.monotonic()<deadline<float('inf'):raise ValueError('fresh observation required')
    endpoint=connection=native=observer=None;owned_fds=[]
    try:
        observer=Observer(config['producer_observer'])
        endpoint=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);endpoint.bind(config['directory']+'/'+config['stage']+'.sock')
        endpoint.listen(1);endpoint.settimeout(.025)
        while connection is None:
            if time.monotonic()>=deadline:raise TimeoutError('proxy accept expired')
            try:connection,_=endpoint.accept()
            except socket.timeout:pass
        connection.settimeout(.025)
        def exact(n):
            raw=bytearray()
            while len(raw)<n:
                if time.monotonic()>=deadline:raise TimeoutError('proxy header expired')
                try:block=connection.recv(n-len(raw))
                except socket.timeout:continue
                if not block:raise ValueError('short native header')
                raw.extend(block)
            return bytes(raw)
        size=struct.unpack('>I',exact(4))[0]
        if not 0<size<=8192:raise ValueError('bounded exact header required')
        command=json.loads(exact(size))
        if command!=[config['binary'],'-server','__new-rpc-mode']:raise ValueError('exact native command required')
        command+=config['flags']
        read_in,write_in=os.pipe();owned_fds.extend([read_in,write_in]);read_out,write_out=os.pipe();owned_fds.extend([read_out,write_out])
        native=subprocess.Popen(command,stdin=read_in,stdout=write_out,stderr=None,close_fds=True,start_new_session=False)
        if os.getpgid(native.pid)!=os.getpid():raise ValueError('native not in reserved proxy group')
        for fd in (read_in,write_out):owned_fds.remove(fd);close_descriptors([fd])
        forwarded=pump(connection,read_out,write_in,deadline,owned_fds,native,observer)
        while os.waitid(os.P_PID,native.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None:
            if time.monotonic()>=deadline:raise TimeoutError('signalled native not terminal; retain')
            time.sleep(.005)
        pid,status,_=os.wait4(native.pid,0)
        if pid!=native.pid:raise ValueError('native reap identity differs')
        native.returncode=os.waitstatus_to_exitcode(status)
        if native.returncode!=-signal.SIGKILL:raise ValueError('exact owned receiver crash outcome required')
        while owned_fds:close_descriptors([owned_fds.pop()])
        close_socket(connection);connection=None;close_socket(endpoint);endpoint=None
        observer.close()
        return dict(schema='unison-generated-producer-interruption/1',server_command=command,server_pid=pid,
            server_returncode=native.returncode,server_reaped=True,server_group=os.getpid(),transport=forwarded,
            resource_release_authorized=False)
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('generated receiver interruption unresolved')
        if retained is not error:retained.original_failure=error
        retained.interrupted_native=native;retained.producer_observer=observer
        retained.socket_owners=[p for p in (endpoint,connection) if p is not None]
        excluded=set(getattr(retained,'uncertain_fds',()))
        known=[*retained.retained_fds,*owned_fds]
        if observer is not None and not observer.files.closed:known.append(observer.files.fd)
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        if retained is error:raise
        raise retained from error


def proxy_main(config):
    store=None
    try:
        store=Store(config['directory'],config['identity']);frame=serve(config)
        store.write(config['stage']+'-PROXY.json',frame);store.close();return 0
    except BaseException as error:
        # Closure is never inferred from a recorded failure, including prestart.
        retain_after_record(lambda:print('PRODUCER_PROXY_RETAINED',repr(error),flush=True))
