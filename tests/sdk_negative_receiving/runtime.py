"""Admitted worker wiring; no acquisition, standalone execution or release grant."""
from copy import deepcopy
import hashlib,os,time
from pathlib import Path
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.runtime import program,child_environment
from sdk_merge_receiving.data import native_clone
from sdk_negative_receiving import admission as A
from sdk_negative_receiving.plan import schedule,require
from sdk_negative_receiving.data import Cases
from sdk_negative_receiving.bound_call import call
from sdk_negative_receiving.pair import audit as audit_pair
from sdk_negative_receiving.worker import execute


def key(row):return row['codec']+'-'+row['policy']+'-'+row['stage']
def proxy_command(packet,row):return [A.PYTHON,'-B',row['directory']+'/'+row['stage']+'-proxy.py']


def run(packet,store,start_record,deadline,*,clone=native_clone,pair_call=call):
    rows=schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']
    fds=tuple(r['fd'] for r in start_record['inherited_resource_fds'])
    require(len(fds)==9 and len(set(fds))==9,'exact previously verified inherited grant required')
    cases=Cases(packet,clone=clone);directories={};scripts={};preps={};pairs={};outputs={};events=[]
    paths=[packet['repository']+'/tests',packet['repository']+'/tests/sdk_host_matrix',packet['repository']+'/bench/sync']
    imports='#!'+A.PYTHON+'\nimport sys\nsys.path[:0]='+repr(paths)+'\n'
    def prepare(row):
        require(time.monotonic()<deadline,'negative receiving observation expired before new phase')
        candidate=cases.prepare(row);root=Path(row['directory']);group=(row['codec'],row['policy'])
        if row['stage']=='seed':
            for name in ('home','tmp','state-client','state-server'):(root/name).mkdir(mode=0o700)
            native=root.lstat();directories[group]=Store(str(root),dict(device=native.st_dev,inode=native.st_ino))
            scripts[str(root/'launcher.py')]=program(root/'launcher.py',imports+
                'from sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n')
        for ref in (*packet['binaries'].values(),packet['tool']):
            require(hashlib.sha256(read_bytes(ref['path'],256*1048576)).hexdigest()==ref['sha256'],'execution artifact changed before negative receive')
        native=root.lstat();config=dict(directory=str(root),identity=dict(device=native.st_dev,inode=native.st_ino),
            stage=row['stage'],binary=packet['binaries']['ox']['path'],flags=row['server_flags'],
            deadline=min(deadline,time.monotonic()+packet['limits']['per_cli_seconds']),
            worker_pid=os.getpid(),resource_fds=deepcopy(start_record['inherited_resource_fds']))
        path=root/(row['stage']+'-proxy.py')
        scripts[str(path)]=program(path,imports+'from sdk_merge_receiving.child_entry import proxy_main\n'+
            'raise SystemExit(proxy_main('+repr(config)+'))\n')
        os.fsync(directories[group].fd)
        preps[key(row)]=store.write(key(row)+'-PREPARED.json',dict(data=deepcopy(cases.history[-1]),
            proxy_config=config,script_pins=deepcopy(scripts)))
        return candidate
    def persist_pair(row,pair,raw):
        name=key(row);require(name not in pairs,'one-use negative pair already recorded')
        require(type(raw) is bytes and 0<len(raw)<=65536,'bounded raw proxy evidence required')
        pairs[name]=store.write(name+'-PAIR.json',dict(identity=deepcopy(row['identity']),pair=deepcopy(pair),raw_proxy_hex=raw.hex()))
    def invoke(row):
        root=Path(row['directory']);name=key(row)
        for path in (str(root/'launcher.py'),str(root/(row['stage']+'-proxy.py'))):
            require(hashlib.sha256(read_bytes(path,65536)).hexdigest()==scripts[path]['sha256'],'generated command shim changed')
        prep=store.read_json(name+'-PREPARED.json',expected_sha256=preps[name]['sha256'])
        phase=prep['proxy_config']['deadline'];group=(row['codec'],row['policy'])
        env=child_environment(root,'state-client')
        env.update(UNISON_MERGE_BINARY=packet['binaries']['ox']['path'],UNISON_MERGE_SOCKET=str(root/(row['stage']+'.sock')),UNISON_MERGE_DEADLINE=str(phase))
        return pair_call(row,env,proxy_command=proxy_command(packet,row),proxy_environment=child_environment(root,'state-server'),
            socket_path=str(root/(row['stage']+'.sock')),deadline=phase,pass_fds=fds,
            read_proxy_bytes=lambda:directories[group].read(row['stage']+'-PROXY.json',maximum=65536),persist=persist_pair)
    def audit(row,outcome,candidate):
        name=key(row);record=store.read_json(name+'-PAIR.json',expected_sha256=pairs[name]['sha256'])
        require(set(record)=={'identity','pair','raw_proxy_hex'} and A.exact(record['identity'],row['identity']),
                'durable negative pair identity differs')
        raw=bytes.fromhex(record['raw_proxy_hex'])
        require(raw.hex()==record['raw_proxy_hex'] and A.exact(record['pair'],outcome[0]) and raw==outcome[1],
                'independent saved pair differs from invocation')
        return audit_pair(row,record['pair'],raw,candidate,proxy_command=proxy_command(packet,row))
    def verify(row,candidate):
        publication=cases.verify(row,candidate)
        outputs[key(row)]=store.write(key(row)+'-OUTPUTS.json',deepcopy(cases.history[-1]))
        return publication
    def persist(snapshot):
        require(len(events)<25,'negative receive event count exceeded')
        name='EVENT-%02d.json'%len(events)
        events.append(store.write(name,dict(snapshot=deepcopy(snapshot),pair_pins=deepcopy(pairs),resource_release_authorized=False)))
    try:
        result=execute(packet['binaries'],packet['tool'],packet['workspace'],prepare=prepare,invoke=invoke,
            audit_transport=audit,verify_outputs=verify,persist=persist)
        require(cases.index==12,'negative data matrix incomplete')
        store.write('WORKER-RESULT.json',dict(result=result,pair_pins=pairs,event_pins=events,data_history=cases.history,
            script_pins=scripts,preparation_pins=preps,output_pins=outputs,resource_release_authorized=False))
        for directory in directories.values():directory.close()
        store.write('WORKER-DIRECTORIES-CLOSED.json',dict(codec_policy_directories_closed=6,
            inherited_resource_fds_closed=False,resource_release_authorized=False))
        return result
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('negative runtime incomplete; retain every owner')
        if retained is not error:retained.original_failure=error
        retained.negative_runtime=dict(store=store,directories=directories,cases=cases,pairs=pairs,scripts=scripts)
        known=list(retained.retained_fds)+list(fds)
        if not store.closed:known.append(store.fd)
        known.extend(s.fd for s in directories.values() if not s.closed)
        excluded=set(getattr(retained,'uncertain_fds',()))
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        if retained is error:raise
        raise retained from error
