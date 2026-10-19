"""Actual IO-owned worker composition; no CLI/admission or resource acquisition.

Call only after current preflight, actual parent binding and artifact verification
under owned IO. entry retains every exception and owns inherited FD closure.
"""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import time
from cached_benchmark.contract import read_bytes
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving import admission as A
from sdk_merge_receiving.plan import schedule,require
from sdk_merge_receiving.data import Cases,native_clone
from sdk_merge_receiving.journal import Journal
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.bound_call import call
from sdk_merge_receiving.worker import execute


def program(path,text):
    raw=text.encode();require(0<len(raw)<=65536,'bounded generated shim required')
    compile(text,str(path),'exec')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o700)
    try:
        at=0
        while at<len(raw):
            n=os.write(fd,raw[at:]);require(n>0,'shim write stalled');at+=n
        os.fsync(fd)
    finally:close_descriptors([fd])
    sha=hashlib.sha256(raw).hexdigest()
    require(hashlib.sha256(read_bytes(str(path),65536)).hexdigest()==sha,'generated shim differs')
    return dict(path=str(path),sha256=sha)


def proxy_command(packet,row):
    return [A.PYTHON,'-B',row['directory']+'/'+row['stage']+'-proxy.py']


def child_environment(root,state):
    return dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LANG='C',LC_ALL='C',
        HOME=str(root/'home'),TMPDIR=str(root/'tmp'),UNISON=str(root/state),PYTHONNOUSERSITE='1')


def run(packet,store,start_record,deadline,*,clone=native_clone,pair_call=call):
    """Default adapters are real. Test adapters must be original source doubles."""
    rows=schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']
    fds=tuple(r['fd'] for r in start_record['inherited_resource_fds'])
    require(len(fds)==9 and len(set(fds))==9,'exact already-verified inherited grant required')
    cases=Cases(packet,clone=clone);codec_stores={};scripts={};preparation_pins={}
    journal=Journal(store,{(r['codec'],r['stage']):proxy_command(packet,r) for r in rows})
    source_paths=[packet['repository']+'/tests',packet['repository']+'/tests/sdk_host_matrix',
                  packet['repository']+'/bench/sync']
    imports='#!'+A.PYTHON+'\nimport sys\nsys.path[:0]='+repr(source_paths)+'\n'
    def prepare(row):
        require(time.monotonic()<deadline,'worker observation expired before new phase')
        candidate=cases.prepare(row);root=Path(row['directory'])
        if row['stage']=='seed':
            for name in ('home','tmp','state-client','state-server'):(root/name).mkdir(mode=0o700)
            st=root.stat();codec_stores[row['codec']]=Store(str(root),dict(device=st.st_dev,inode=st.st_ino))
            scripts[str(root/'launcher.py')]=program(root/'launcher.py',imports+
                'from sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n')
        # Every call hashes the peer/tool artifacts under the already-owned IO.
        for item in (*packet['binaries'].values(),packet['tool']):
            require(hashlib.sha256(read_bytes(item['path'],256*1048576)).hexdigest()==item['sha256'],
                    'execution artifact changed before call')
        phase_deadline=min(deadline,time.monotonic()+packet['limits']['per_cli_seconds'])
        st=root.stat()
        config=dict(directory=str(root),identity=dict(device=st.st_dev,inode=st.st_ino),stage=row['stage'],
            binary=packet['binaries']['ox']['path'],flags=row['server_flags'],deadline=phase_deadline,
            worker_pid=os.getpid(),resource_fds=deepcopy(start_record['inherited_resource_fds']))
        path=root/(row['stage']+'-proxy.py')
        scripts[str(path)]=program(path,imports+'from sdk_merge_receiving.child_entry import proxy_main\n'+
                                   'raise SystemExit(proxy_main('+repr(config)+'))\n')
        os.fsync(codec_stores[row['codec']].fd)
        preparation_pins[row['codec'],row['stage']]=store.write(row['codec']+'-'+row['stage']+'-PREPARED.json',dict(
            data=deepcopy(cases.history[-1]),proxy_config=config,script_pins=deepcopy(scripts)))
        return candidate
    def invoke(row):
        root=Path(row['directory']);script=root/(row['stage']+'-proxy.py')
        for path in (str(script),str(root/'launcher.py')):
            require(hashlib.sha256(read_bytes(path,65536)).hexdigest()==scripts[path]['sha256'],
                    'generated shim changed before dispatch')
        # The configured absolute deadline is part of the pinned script bytes;
        # keep it rather than silently extending observations at invocation.
        prepared=store.read_json(row['codec']+'-'+row['stage']+'-PREPARED.json',expected_sha256=
            preparation_pins[row['codec'],row['stage']]['sha256'])
        phase_deadline=prepared['proxy_config']['deadline']
        env=child_environment(root,'state-client')
        env.update(UNISON_MERGE_BINARY=packet['binaries']['ox']['path'],
            UNISON_MERGE_SOCKET=str(root/(row['stage']+'.sock')),UNISON_MERGE_DEADLINE=str(phase_deadline))
        return pair_call(row,env,proxy_command=proxy_command(packet,row),
            proxy_environment=child_environment(root,'state-server'),socket_path=str(root/(row['stage']+'.sock')),
            deadline=phase_deadline,pass_fds=fds,
            read_proxy_bytes=lambda:codec_stores[row['codec']].read(row['stage']+'-PROXY.json',maximum=65536),
            persist=journal.persist_pair)
    def verify(row,candidate):
        cases.verify(row,candidate)
        store.write(row['codec']+'-'+row['stage']+'-OUTPUTS.json',deepcopy(cases.history[-1]))
    try:
        result=execute(packet['binaries'],packet['tool'],packet['workspace'],prepare=prepare,
            invoke=invoke,audit_transport=journal.audit_transport,verify_outputs=verify,persist=journal.persist)
        require(cases.index==9,'data callback matrix incomplete')
        store.write('WORKER-RESULT.json',dict(result=result,events=journal.events,pair_pins=journal.pair_pins,
            data_history=cases.history,script_pins=scripts,
            preparation_pins={codec+'-'+stage:pin for (codec,stage),pin in preparation_pins.items()},
            resource_release_authorized=False))
        for value in codec_stores.values():value.close()
        store.write('WORKER-DIRECTORIES-CLOSED.json',dict(codec_directories_closed=3,
            inherited_resource_fds_closed=False,resource_release_authorized=False))
        return result
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'merge runtime incomplete; retain inherited resources and every owner')
        if retained is not error:retained.original_failure=error
        retained.merge_runtime=dict(store=store,codec_stores=codec_stores,cases=cases,journal=journal,scripts=scripts)
        known=list(retained.retained_fds)+list(fds)
        if not store.closed:known.append(store.fd)
        known.extend(s.fd for s in codec_stores.values() if not s.closed)
        excluded=set(getattr(retained,'uncertain_fds',()))
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        if retained is error:raise
        raise retained from error
