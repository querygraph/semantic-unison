"""Freeze one compiler's named receiving metadata/request; never opens executables."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.store import Store
from current_validation_paths import admission as A,inventory,metadata
from current_validation_paths.contract import LIMITS,plan as case_plan
from current_validation_paths import successors,dng_contract,fs_contract,cross_contract
SUITES=dict(named=('current-named-receiving-','/private/tmp/u-vpath-','unison-current-named-receiving-execution/1'),
    **{name:successors.SUITES[c.SCHEMA][2:]+(c.SCHEMA,) for name,c in (('dng_merge',dng_contract),('fs_properties',fs_contract),('cross_peer',cross_contract))})


def prepare(compiler,build_receipt,output,*,read=read_bytes,workspace=None,suite='named',peer_build_receipt=None):
    output=Path(output);A.require(suite in SUITES,'known receiving suite required');prefix,space,schema=SUITES[suite]
    A.require(output.parent==Path(A.REPOSITORY)/'doc' and output.name.startswith(prefix+compiler+'-'),
              'one-use repository doc freeze directory required')
    A.require(compiler in A.COMPILERS,'one exact compiler label required')
    name=str(Path(build_receipt).resolve());A.path(name)
    A.require(Path(name).suffix=='.json','JSON build receipt only during preparation')
    raw=read(name,1048576);receipt=metadata.document(raw)
    A.require(type(receipt) is dict,'object build receipt required')
    A.require((peer_build_receipt is not None)==successors.peered(schema),'a peer build receipt exactly for a peered suite')
    legacy=read(A.REPOSITORY+'/'+A.LEGACY,256*1024)
    source_names=inventory.execution();production_names=inventory.production()
    def pins(names):return {n:hashlib.sha256(read(str(Path(A.REPOSITORY)/n),16*1048576)).hexdigest() for n in names}
    if workspace is None:
        import uuid
        workspace=space+uuid.uuid4().hex[:16]
    A.require(not os.path.lexists(workspace),'fresh named workspace already consumed')
    successor=successors.contract(schema)
    rows=(successor.plan(workspace,compiler) if successor else case_plan(legacy.decode('utf-8'),workspace,compiler))['rows']
    packet=dict(schema=schema,repository=A.REPOSITORY,workspace=workspace,compiler=compiler,
        interpreter=dict(path=A.PYTHON,sha256=A.PYTHON_SHA),binary=dict(path=str(Path(receipt['binary']).resolve()),sha256=receipt['binary_sha256']),
        build=dict(receipt=dict(path=name,sha256=hashlib.sha256(raw).hexdigest()),
            compiler=dict(path=str(Path(receipt['compiler']).resolve()),sha256=receipt['compiler_sha256'])),
        legacy_source=dict(path=A.REPOSITORY+'/'+A.LEGACY,bytes=len(legacy),sha256=hashlib.sha256(legacy).hexdigest()),
        rows=rows,limits=dict(successor.LIMITS if successor else LIMITS),source_pins=pins(source_names),production_sha256=pins(production_names),
        prerequisite_sha256={name:hashlib.sha256(raw).hexdigest()},cpu_policy_sha256=A.POLICY,io_manifest_sha256=A.IO)
    if peer_build_receipt is not None:
        peer_name=str(Path(peer_build_receipt).resolve());A.path(peer_name)
        A.require(Path(peer_name).suffix=='.json','JSON peer build receipt only during preparation')
        peer_raw=read(peer_name,1048576);peer=metadata.document(peer_raw)
        A.require(type(peer) is dict and peer.get('compiler') is not None,'object peer build receipt required')
        label=next((k for k,v in A.COMPILERS.items() if v==str(Path(peer['compiler']).resolve())),None)
        packet['peer']=dict(compiler=label,binary=dict(path=str(Path(peer['binary']).resolve()),sha256=peer['binary_sha256']),
            build=dict(receipt=dict(path=peer_name,sha256=hashlib.sha256(peer_raw).hexdigest()),
                compiler=dict(path=str(Path(peer['compiler']).resolve()),sha256=peer['compiler_sha256'])))
        packet['prerequisite_sha256'][peer_name]=hashlib.sha256(peer_raw).hexdigest()
    A.validate(packet,source=legacy.decode('utf-8'),execution_sources=source_names,production_sources=production_names)
    output.mkdir(mode=0o700);native=output.stat();store=Store(str(output),dict(device=native.st_dev,inode=native.st_ino))
    try:
        plan_pin=store.write('PLAN.json',packet)
        plan_ref=dict(path=str(output/'PLAN.json'),sha256=plan_pin['sha256'])
        # Re-authenticate all metadata; the new plan is read through its owned directory.
        def reread(path,limit):
            if path==plan_ref['path']:return store.read('PLAN.json',expected_sha256=plan_ref['sha256'],maximum=limit)
            return read(path,limit)
        metadata.checked(plan_ref,execution_sources=source_names,production_sources=production_names,read=reread)
        request=dict(schema='unison-current-named-receiving-request/1',state='PREPARED_UNADMITTED',target=A.TARGET,
            plan=plan_ref,workspace=workspace,compiler=compiler,command=A.worker_command(packet,plan_ref),
            source_pins=packet['source_pins'],production_sha256=packet['production_sha256'],limits=packet['limits'])
        request_pin=store.write('REQUEST.json',request)
        index=dict(schema='unison-current-named-receiving-freeze/1',state='PREPARED_UNADMITTED',compiler=compiler,plan=plan_ref,
            request=dict(path=str(output/'REQUEST.json'),sha256=request_pin['sha256']),workspace=workspace,
            launch_argv_template=[A.PYTHON,A.REPOSITORY+'/tests/current_validation_paths/entry.py','--plan',plan_ref['path'],
                '--plan-sha256',plan_ref['sha256'],'--admission','ADMISSION_PATH_REQUIRED','--admission-sha256','ADMISSION_SHA_REQUIRED'],
            runtime_admitted=False,executables_opened=False)
        store.write('INDEX.json',index)
        return index
    except UnresolvedOwnership as error:
        error.named_freeze_store=store
        raise
    finally:
        if not isinstance(sys.exception(),UnresolvedOwnership):store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',required=True,choices=sorted(A.COMPILERS))
    parser.add_argument('--build-receipt',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--suite',choices=sorted(SUITES),default='named');parser.add_argument('--peer-build-receipt')
    args=parser.parse_args()
    print(json.dumps(prepare(args.compiler,args.build_receipt,Path(args.output),suite=args.suite,peer_build_receipt=args.peer_build_receipt),indent=2))

if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        from sdk_merge_receiving.child_entry import diagnostic
        retain_after_record(lambda:print('NAMED-FREEZE-RETAINED '+json.dumps(diagnostic('freezer',error)),
                                         file=sys.stderr,flush=True))
