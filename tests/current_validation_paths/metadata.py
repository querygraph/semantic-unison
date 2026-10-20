"""Metadata-only named preflight; the binary/interpreter/compiler are never opened.

Source and the one JSON build receipt are authenticated by hash. Build bytes and
selftests are not rerun here; executables are hashed only under owned IO.
"""
import hashlib,os
from pathlib import Path
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.metadata import document
from current_validation_paths import admission as A


def checked(plan_ref,*,execution_sources,production_sources,read=read_bytes):
    A.reference(plan_ref)
    A.require(Path(plan_ref['path']).suffix=='.json','JSON plan reference required')
    raw=read(plan_ref['path'],1048576)
    A.require(hashlib.sha256(raw).hexdigest()==plan_ref['sha256'],'plan metadata SHA differs')
    packet=document(raw);A.require(type(packet) is dict,'object plan required')
    legacy=read(A.REPOSITORY+'/'+A.LEGACY,256*1024)
    contract=A.validate(packet,source=legacy.decode('utf-8'),execution_sources=execution_sources,production_sources=production_sources)
    total=len(raw)
    for pins in (packet['source_pins'],packet['production_sha256']):
        for name,sha in pins.items():
            data=read(str(Path(packet['repository'])/name),16*1048576)
            A.require(hashlib.sha256(data).hexdigest()==sha,'current source changed: '+name);total+=len(data)
    # The client build and, for a peered plan, the other compiler's server build.
    for owner in (packet,*([packet['peer']] if 'peer' in packet else [])):
        receipt=owner['build']['receipt'];data=read(receipt['path'],1048576)
        A.require(hashlib.sha256(data).hexdigest()==receipt['sha256'],'build receipt changed');total+=len(data)
        build=document(data)
        A.require(type(build) is dict and build.get('complete') is True and build.get('selftest_requested') is True
            and type(build.get('build_exit')) is int and build['build_exit']==0
            and type(build.get('selftest_exit')) is int and build['selftest_exit']==0,'successful actual build/selftest receipt required')
        for key,expected in (('binary',owner['binary']['path']),('compiler',owner['build']['compiler']['path'])):
            A.require(type(build.get(key)) is str and str(Path(build[key]).resolve())==expected,'build artifact path declaration differs')
        A.require(build.get('binary_sha256')==owner['binary']['sha256'] and build.get('compiler_sha256')==owner['build']['compiler']['sha256'],
            'build artifact hash declaration differs')
        pins=build.get('source_sha256')
        A.require(type(pins) is dict and A.exact({n:s for n,s in pins.items() if n.startswith('src/')},packet['production_sha256']),
            'compiled source inventory differs from current production')
    return packet,contract,dict(metadata_bytes_read=total,source_files_verified=len(packet['source_pins'])+len(packet['production_sha256']),
        build_receipt_verified=True,executables_opened=False,build_selftests_rerun=False,runtime_admitted=False,uid=os.getuid())
