"""One exact generated batch sample under standing8/EXglobal after handover.

No SDK, originals, Photo, automatic successor, retry or resource timeout kill.
"""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from final_profile_owner import sha
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from corpus_workloads import plan
from batch_runtime import run
from batch_parent import audit


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact plan SHA required')
    packet=json.loads(raw)
    if packet['state']!='PREPARED_ONE_GENERATED_BATCH_AFTER_PHOTO_HANDOVER' or packet['repository']!=str(ROOT):raise ValueError('exact batch plan required')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('source changed: '+name)
    sources()
    kind=packet.get('sample_kind','corpus')
    if kind=='corpus':
        corpus=plan(**packet['corpus']);runtime_options={};audit_options={}
    elif kind=='recipe':
        from recipe_sample import plan as recipe_plan,sample as recipe_sample,validate_rows,verify_replica
        corpus=recipe_plan(**packet['corpus'])
        runtime_options=dict(sample_runner=recipe_sample)
        audit_options=dict(rows_validator=validate_rows,verify_replica=verify_replica)
    else:raise ValueError('known source-selected sample kind required')
    policy=ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
    if sha(policy)!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or tuple(authorized_unison_tokens(read_bytes(str(policy),1048576)))!=tuple(range(8)):
        raise ValueError('standing8 policy differs')
    pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
    io_pool=GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256)
    root=Path(packet['workspace']);root.mkdir(mode=0o700)
    store=io=cpu=None;runtime_attempted=False
    try:
        st=root.stat();store=Store(str(root),dict(device=st.st_dev,inode=st.st_ino))
        bundle=try_io_cpu_bundle(io_pool,pool,tuple(range(8)))
        if bundle is None:
            store.write('CONTENTION.json',dict(no_runtime_attempted=True));store.close();return 2
        io,cpu=bundle;sources()
        for ref in packet['build_receipts']:
            data=read_bytes(ref['path'],1048576)
            if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('build receipt differs')
            build=json.loads(data)
            if not(build['complete'] is True and build['build_exit']==0 and build['selftest_exit']==0):raise ValueError('unqualified build')
            if build['binary']!=packet['artifacts'][ref['compiler']]['path'] or build['binary_sha256']!=packet['artifacts'][ref['compiler']]['sha256']:
                raise ValueError('build/binary binding differs')
            for name,digest in build['source_sha256'].items():
                if name.startswith('src/') and sha(ROOT/name)!=digest:raise ValueError('production source changed')
        def artifacts():
            sources()
            for item in (*packet['artifacts'].values(),packet['interpreter']):
                if sha(item['path'],64*1048576)!=item['sha256']:raise ValueError('artifact changed')
        artifacts()
        rows=[]
        for fd in (*cpu.fds,*io.fds):
            value=os.fstat(fd);rows.append(dict(fd=fd,device=value.st_dev,inode=value.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=rows,
            cpu_indexes=list(range(8)),io_mode='EX_GLOBAL',purpose='one generated functional sample; no timing claim'))
        print('START',os.getpid(),str(root),flush=True)
        binaries=dict(client=packet['artifacts']['stock']['path'],server=packet['artifacts']['ox']['path'])
        runtime_attempted=True
        pin=run(corpus,binaries,str(root),repository=str(ROOT),mode=packet['mode'],workers=packet['workers'],
            store=store,resource_rows=rows,deadline=time.monotonic()+600,artifact_check=artifacts,**runtime_options)
        report=audit(store,pin,corpus,binaries,mode=packet['mode'],workers=packet['workers'],**audit_options)
        if report['external_children_settled'] is not True:raise ValueError('peer audit incomplete')
        artifacts();store.write('OWNER-RESULT.json',dict(complete=True,runtime=pin,audit=report,parent_tool_terminal_proved=False))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('CLOSED',len(corpus.files),str(root),flush=True);return 0
    except BaseException as error:
        if not runtime_attempted and not isinstance(error,UnresolvedOwnership):
            try:
                if store is not None and not store.closed:store.write('PREENTRY-REFUSED.json',dict(runtime_attempted=False,error=repr(error)));store.close()
                if cpu is not None and not cpu.closed:close_unstarted(cpu)
                if io is not None and not io.closed:close_unstarted(io)
            except BaseException as cleanup:retain_after_record(lambda:print('RETAIN_PREENTRY',repr(cleanup),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('RETAIN',repr(error),str(root),flush=True))


if __name__=='__main__':raise SystemExit(main())
