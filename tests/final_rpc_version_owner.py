"""Actual pinned current server handshake rejection/acceptance, not v0 transfer."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.runtime import program,child_environment
from sdk_merge_receiving.admission import PYTHON
from shared_child import start
from final_clone_stage_owner import write_bytes
from final_profile_owner import sha,closed

VERSIONS=(0,1,999)


def validate_reply(version,stdout):
    if type(version) is not int or version not in VERSIONS or type(stdout) is not str:raise ValueError('exact generated version and captured text required')
    greeting='Unison RPC\nVERSIONS 1\n'
    if not stdout.startswith(greeting):raise ValueError('actual current RPC1 advertisement required')
    rest=stdout[len(greeting):]
    if version==1:
        if not rest.startswith('OK\n'):raise ValueError('RPC1 must be accepted')
    else:
        expected='NOK Client RPC version not supported. Version received from client: "'+str(version)+'". Supported RPC versions: "1"\n'
        if not rest.startswith(expected):raise ValueError('exact unsupported-version refusal required')
    return dict(version=version,accepted=version==1,ordinary_transfer_or_semantic_fallback_proved=False)


def shim_text():
    # Same PID exec: no unrecorded native child or separately owned process.
    return '''import os,sys
from private_camera_receiving.close import close_descriptors
from shared_process_owner import retain_after_record
try:
 binary,source=sys.argv[1:]
 fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 os.dup2(fd,0)
 close_descriptors([fd])
 os.execve(binary,[binary,'-server'],dict(os.environ))
except BaseException as error:
 retain_after_record(lambda:print('RPC_EXEC_RETAIN',repr(error),file=sys.stderr,flush=True))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact version probe plan SHA required')
    packet=json.loads(raw)
    if packet['schema']!='unison-final-rpc-version-plan/1' or packet['repository']!=str(ROOT) or sys.executable!=PYTHON or set(packet['artifacts'])!={'stock','ox'}:
        raise ValueError('exact current pair and qualified interpreter required')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('version-probe source changed '+name)
    sources();root=Path(packet['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-rpc-version-'):raise ValueError('new generated private version-probe workspace required')
    indexes=authorized_unison_tokens(read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576))
    if indexes!=tuple(range(8)):raise ValueError('standing8 differs')
    root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));io=cpu=None;attempted=False
    try:
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,indexes)
        if bundle is None:store.write('CONTENTION.json',dict(native_attempted=False));store.close();return 2
        io,cpu=bundle;production={}
        for ref in packet['build_receipts']:
            data=read_bytes(ref['path'],1048576)
            if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('build receipt changed')
            build=json.loads(data);binary=packet['artifacts'][ref['compiler']]
            if not(build['complete'] is True and build['build_exit']==0 and build['selftest_exit']==0 and build['binary']==binary['path'] and build['binary_sha256']==binary['sha256']):raise ValueError('current build/binary binding differs')
            for name,digest in build['source_sha256'].items():
                if name.startswith('src/'):
                    if name in production and production[name]!=digest:raise ValueError('mixed production inventory')
                    production[name]=digest
        def artifacts():
            sources()
            for name,digest in production.items():
                if sha(ROOT/name)!=digest:raise ValueError('production source changed')
            for ref in (*packet['artifacts'].values(),packet['interpreter']):
                if sha(ref['path'],64*1048576)!=ref['sha256']:raise ValueError('version-probe binary/interpreter changed')
        artifacts();resources=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resources,calls=6,scope='version0/1/999 handshake only; no transfer/SDK/Photo'))
        imports='import sys\nsys.path[:0]='+repr([str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')])+'\n'
        shim=root/'exec-server.py';pin=program(shim,imports+shim_text());deadline=time.monotonic()+90;records=[]
        print('RPC_VERSION_START',os.getpid(),str(root),flush=True)
        for label in ('stock','ox'):
            for version in VERSIONS:
                artifacts();name=label+'-'+str(version);directory=root/name;directory.mkdir(mode=0o700)
                for sub in ('home','tmp','state'):(directory/sub).mkdir(mode=0o700)
                inputfile=directory/'input.txt';write_bytes(inputfile,('VERSION '+str(version)+'\n').encode())
                if sha(shim,65536)!=pin['sha256']:raise ValueError('samePID exec shim changed')
                argv=[PYTHON,'-B',str(shim),packet['artifacts'][label]['path'],str(inputfile)]
                intent=store.write(name+'-INTENT.json',dict(command=argv,native_exec_argv=[packet['artifacts'][label]['path'],'-server'],input_sha256=sha(inputfile),shim=pin,resource_rows=resources))
                attempted=True;child=start(argv,child_environment(directory,'state'),pass_fds=(*cpu.fds,*io.fds),capture_limit=65536)
                outcome=child.finish(min(deadline,time.monotonic()+20));capture=store.write(name+'-CHILD.json',outcome);closed(outcome,0)
                proof=validate_reply(version,outcome['stdout']);record=dict(label=label,version=version,intent=intent,child=capture,proof=proof)
                records.append(record);store.write(name+'-RESULT.json',record);print('RPC_VERSION_CLOSED',label,version,flush=True)
        artifacts();store.write('RESULT.json',dict(complete=True,rows=records,source_pins=packet['source_pins'],production_pins=production,semantic_or_transfer_fallback_proved=False,no_SDK_or_Photo=True))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('RPC_VERSION_ALL_CLOSED',str(root),flush=True);return 0
    except BaseException as error:
        if not attempted and not isinstance(error,UnresolvedOwnership):
            try:
                store.write('PREENTRY-REFUSED.json',dict(native_attempted=False,error=repr(error)));store.close()
                if cpu is not None and not cpu.closed:close_unstarted(cpu)
                if io is not None and not io.closed:close_unstarted(io)
            except BaseException as cleanup:retain_after_record(lambda:print('RPC_PREENTRY_RETAIN',repr(cleanup),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('RPC_VERSION_RETAIN',repr(error),str(root),flush=True))

if __name__=='__main__':raise SystemExit(main())
