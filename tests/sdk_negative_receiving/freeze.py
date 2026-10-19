"""Freeze current native merge metadata/request without opening artifacts or DNGs."""
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
from sdk_negative_receiving import admission as A,inventory,metadata
from sdk_merge_receiving.inputs import FIELDS
from sdk_merge_receiving.store import Store


def prepare(input_manifest,sdk_manifest,build_paths,output,*,prerequisites=(),read=read_bytes,observe=os.lstat):
    output=Path(output)
    A.require(output.parent==Path(A.REPOSITORY)/'doc' and output.name.startswith('current-sdk-negative-'),
              'one-use repository doc freeze directory required')
    refs={};documents={}
    def document(name):
        name=str(Path(name).resolve());A.path(name)
        A.require(Path(name).suffix=='.json','JSON metadata only during preparation')
        raw=read(name,1048576);value=metadata.document(raw)
        A.require(type(value) is dict,'object metadata prerequisite required')
        refs[name]=hashlib.sha256(raw).hexdigest();documents[name]=value
        return dict(path=name,sha256=refs[name]),value
    input_ref,inputs=document(input_manifest);sdk_ref,sdk=document(sdk_manifest)
    A.require(inputs.get('schema')=='unison-current-sdk-merge-inputs/1','exact generated input manifest required')
    for ref in inputs['ancestry']:
        A.reference(ref);actual,_=document(ref['path'])
        A.require(actual==ref,'generation ancestry changed')
    for name in prerequisites:document(name)
    builds={};binaries={}
    for label in ('stock','ox'):
        ref,receipt=document(build_paths[label])
        builds[label]=dict(receipt=ref,compiler=dict(path=str(Path(receipt['compiler']).resolve()),
                                                  sha256=receipt['compiler_sha256']))
        binaries[label]=dict(label=label,path=str(Path(receipt['binary']).resolve()),sha256=receipt['binary_sha256'])
    source_names=inventory.execution();production_names=inventory.production()
    def pins(names):return {name:hashlib.sha256(read(str(Path(A.REPOSITORY)/name),16*1048576)).hexdigest() for name in names}
    observations={}
    for case in inputs['cases']:
        for ref in case['states'].values():
            value=observe(ref['path']);observations[ref['path']]={k:getattr(value,k) for k in FIELDS}
    import uuid
    workspace='/private/tmp/u-snr-'+uuid.uuid4().hex[:16]
    A.require(not os.path.lexists(workspace),'fresh generated workspace already consumed')
    packet=dict(schema='unison-current-sdk-negative-receiving-execution/1',repository=A.REPOSITORY,workspace=workspace,
        interpreter=dict(path=A.PYTHON,sha256=A.PYTHON_SHA),binaries=binaries,
        tool=dict(path=sdk['executable'],sha256=sdk['executable_sha256'],build_id=sdk['build_id'],threads=sdk['threads']),
        builds=builds,cases=inputs['cases'],source_observations=observations,input_manifest=input_ref,sdk_manifest=sdk_ref,
        execution_sha256=pins(source_names),production_sha256=pins(production_names),prerequisite_sha256=refs,
        limits=dict(A.LIMITS),cpu_policy_sha256=A.POLICY,io_manifest_sha256=A.IO)
    A.validate(packet,execution_sources=source_names,production_sources=production_names,expected_uid=os.getuid())
    output.mkdir(mode=0o700);native=output.stat();store=Store(str(output),dict(device=native.st_dev,inode=native.st_ino))
    try:
        plan_pin=store.write('PLAN.json',packet)
        plan_ref=dict(path=str(output/'PLAN.json'),sha256=plan_pin['sha256'])
        # Authenticates all current source/JSON/input metadata again. The just-
        # written plan is read through its owned directory, never executable IO.
        def reread(name,limit):
            if name==plan_ref['path']:return store.read('PLAN.json',expected_sha256=plan_ref['sha256'],maximum=limit)
            return read(name,limit)
        metadata.checked(plan_ref,execution_sources=source_names,production_sources=production_names,
                         expected_uid=os.getuid(),read=reread,observe=observe)
        request=dict(schema='unison-current-sdk-negative-receiving-request/1',state='PREPARED_UNADMITTED',target='current-sdk-negative-receiving',
            plan=plan_ref,workspace=workspace,command=A.worker_command(packet,plan_ref),
            execution_sha256=packet['execution_sha256'],production_sha256=packet['production_sha256'],limits=packet['limits'])
        request_pin=store.write('REQUEST.json',request)
        index=dict(schema='unison-current-sdk-negative-receiving-freeze/1',state='PREPARED_UNADMITTED',plan=plan_ref,
            request=dict(path=str(output/'REQUEST.json'),sha256=request_pin['sha256']),workspace=workspace,
            launch_argv_template=[A.PYTHON,A.REPOSITORY+'/tests/sdk_negative_receiving/entry.py','--plan',plan_ref['path'],
                '--plan-sha256',plan_ref['sha256'],'--admission','ROOT_PUBLISHED_PATH_REQUIRED',
                '--admission-sha256','ROOT_PUBLISHED_SHA_REQUIRED'],runtime_admitted=False,sdk_invoked=False)
        store.write('INDEX.json',index)
        return index
    except UnresolvedOwnership as error:
        error.merge_freeze_store=store
        raise
    finally:
        if not isinstance(sys.exception(),UnresolvedOwnership):store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input-manifest','sdk-manifest','stock-build','ox-build','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--prerequisite',action='append',default=[]);args=parser.parse_args()
    print(json.dumps(prepare(args.input_manifest,args.sdk_manifest,dict(stock=args.stock_build,ox=args.ox_build),
        Path(args.output),prerequisites=args.prerequisite),indent=2))

if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        from sdk_merge_receiving.child_entry import diagnostic
        retain_after_record(lambda:print('MERGE-FREEZE-RETAINED '+json.dumps(diagnostic('freezer',error)),
                                         file=sys.stderr,flush=True))
