"""Metadata-only preflight; executable and DNG payloads are never opened here.

Current source/JSON receipts are authenticated by hash. Input files are fenced
with lstat only; their historical hashes remain declarations until cloned and
hashed under owned IO. Build bytes/selftests are not rerun by metadata checks.
"""
import hashlib
import json
import os
from pathlib import Path
from cached_benchmark.contract import read_bytes
from sdk_negative_receiving import admission as A
from sdk_merge_receiving.evidence import unique
from sdk_merge_receiving.inputs import FIELDS


def document(raw):
    return json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))


def checked(plan_ref,*,execution_sources,production_sources,expected_uid,
            read=read_bytes,observe=os.lstat):
    A.reference(plan_ref)
    A.require(Path(plan_ref['path']).suffix=='.json','JSON plan reference required')
    raw=read(plan_ref['path'],1048576)
    A.require(hashlib.sha256(raw).hexdigest()==plan_ref['sha256'],'plan metadata SHA differs')
    packet=document(raw)
    contract=A.validate(packet,execution_sources=execution_sources,
                        production_sources=production_sources,expected_uid=expected_uid)
    verified={};total=len(raw)
    for inventory in (packet['execution_sha256'],packet['production_sha256']):
        for name,sha in inventory.items():
            source=str(Path(packet['repository'])/name)
            data=read(source,16*1048576)
            A.require(hashlib.sha256(data).hexdigest()==sha,'current source changed: '+name)
            verified[source]=sha;total+=len(data)
    prerequisites={}
    for name,sha in packet['prerequisite_sha256'].items():
        A.require(Path(name).suffix=='.json','only reviewed JSON prerequisites before IO')
        data=read(name,1048576)
        A.require(hashlib.sha256(data).hexdigest()==sha,'prerequisite changed: '+name)
        value=document(data);A.require(type(value) is dict,'object prerequisite required')
        prerequisites[name]=value;total+=len(data)
    manifest=prerequisites[packet['input_manifest']['path']]
    A.require(set(manifest)=={'schema','cases','ancestry'}
        and manifest['schema']=='unison-current-sdk-merge-inputs/1'
        and A.exact(manifest['cases'],packet['cases'])
        and type(manifest['ancestry']) is list and 0<len(manifest['ancestry'])<=16,
        'exact generated scalar-state manifest and ancestry required')
    seen=set()
    for ref in manifest['ancestry']:
        A.reference(ref)
        A.require(ref['path'] not in seen and ref['path']!=packet['input_manifest']['path']
            and packet['prerequisite_sha256'].get(ref['path'])==ref['sha256'],
            'distinct authenticated generation ancestry required')
        seen.add(ref['path'])
    sdk=prerequisites[packet['sdk_manifest']['path']]
    A.require(sdk.get('executable')==packet['tool']['path']
        and sdk.get('executable_sha256')==packet['tool']['sha256']
        and sdk.get('build_id')==packet['tool']['build_id']
        and type(sdk.get('threads')) is int and sdk['threads']==1,
        'retained SDK manifest differs from qualified tool declaration')
    for label in ('stock','ox'):
        declared=packet['builds'][label];build=prerequisites[declared['receipt']['path']]
        A.require(build.get('complete') is True and build.get('selftest_requested') is True
            and type(build.get('build_exit')) is int and build['build_exit']==0
            and type(build.get('selftest_exit')) is int and build['selftest_exit']==0,
            'successful actual build/selftest receipt required')
        for key,expected in (('binary',packet['binaries'][label]['path']),
                             ('compiler',declared['compiler']['path'])):
            A.require(type(build.get(key)) is str and str(Path(build[key]).resolve())==expected,
                      'build artifact path declaration differs')
        A.require(build.get('binary_sha256')==packet['binaries'][label]['sha256']
            and build.get('compiler_sha256')==declared['compiler']['sha256'],
            'build artifact hash declaration differs')
        source_pins=build.get('source_sha256')
        A.require(type(source_pins) is dict and A.exact({n:s for n,s in source_pins.items()
            if n.startswith('src/')},packet['production_sha256']),
            'compiled source inventory differs from current production')
    for name,expected in packet['source_observations'].items():
        native=observe(name)
        A.require(A.exact({key:getattr(native,key) for key in FIELDS},expected),
                  'retained generated state epoch changed: '+name)
    return packet,contract,dict(metadata_bytes_read=total,source_files_verified=len(verified),
        prerequisites_verified=len(prerequisites),input_metadata_fences=12,
        input_payload_opened=False,execution_artifacts_opened=False,
        build_selftests_rerun=False,runtime_admitted=False)
