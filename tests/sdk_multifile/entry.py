"""Metadata-only exact plan guard; no runtime CLI/dispatcher grant yet."""
import os
from pathlib import Path
import re
import stat
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_io_pool import read_manifest
from shared_execute import sources as shared_sources
from invocation import artifact_sha,SCRIPT_NAMES
from sdk_multifile.plan import plan as command_plan,BUILD
from sdk_multifile.clone import FIELDS

TARGET='sdk-multifile-receive'
PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PYTHON_SHA='56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'
PARAMETERS=dict(cpu_credits=8,cases=2,cli_calls=2,sdk_calls=4,endpoint_workers=3,
                observation_seconds=600,worker_seconds=570,per_cli_seconds=120,per_sdk_seconds=90,
                declared_logical_io_bytes=16*1073741824,io_budget_enforced=False)


def require(value,message):
    if not value:raise ValueError(message)


def sources():
    result=shared_sources()
    result.update({str(p):artifact_sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))})
    return result


def checked_plan(path,digest):
    path=Path(path);require(path.is_absolute() and path.resolve()==path,'canonical plan path required')
    d=read_manifest(path,digest)
    require(set(d)=={'schema','workspace','parameters','execution_source_sha256','binaries','tool','inputs','sources','transport_source_sha256','interpreter'},'exact multi-file plan fields required')
    require(d['schema']=='unison-sdk-multifile-plan/1' and d['parameters']==PARAMETERS
            and all(type(d['parameters'][k]) is type(v) for k,v in PARAMETERS.items()),'fixed finite limits required')
    require(d['execution_source_sha256']==sources(),'current execution closure differs')
    require(sys.executable==PYTHON and d['interpreter']==dict(path=PYTHON,sha256=PYTHON_SHA),'qualified interpreter required')
    w=Path(d['workspace']);require(w.parent==Path('/private/tmp') and w.name.startswith('u-smr-') and 8<len(w.name)<=32,'fresh short namespace required')
    require(set(d['binaries'])=={'stock','ox'},'fixed compiler pair required')
    for label,item in d['binaries'].items():
        require(set(item)=={'label','path','sha256'} and item['label']==label,'exact binary metadata required')
    tool=d['tool'];require(set(tool)=={'path','sha256','build_id','threads','manifest','manifest_sha256'}
                          and tool['build_id']==BUILD and type(tool['threads']) is int and tool['threads']==1,'qualified single-thread SDK required')
    for item in [*d['binaries'].values(),tool]:
        q=Path(item['path']);require(q.is_absolute() and q.resolve()==q and type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}',item['sha256']),'canonical pinned tool/binary required')
    manifest=Path(tool['manifest'])
    require(manifest.is_absolute() and manifest.resolve()==manifest and type(tool['manifest_sha256']) is str
            and re.fullmatch('[0-9a-f]{64}',tool['manifest_sha256']),'canonical SDK manifest pin required')
    m=read_manifest(tool['manifest'],tool['manifest_sha256'])
    require(m['executable']==tool['path'] and m['executable_sha256']==tool['sha256'] and m['build_id']==BUILD,'SDK manifest binding differs')
    require(type(d['inputs']) is list and len(d['inputs'])==2 and type(d['sources']) is list and len(d['sources'])==2,'two fixed generated inputs required')
    ids=set();hashes=set()
    for item,source,name in zip(d['inputs'],d['sources'],['uncompressed.dng','jpeg.dng']):
        require(set(item)=={'candidate_id','path','sha256','identity'} and item['candidate_id']==name,'fixed generated input mapping required')
        q=Path(item['path']);identity=item['identity'];digest=item['sha256']
        require(q.is_absolute() and q.resolve()==q and q.is_relative_to('/private/tmp'),'retained private generated input path required')
        require(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest)
                and type(identity) is dict and set(identity)==set(FIELDS)
                and all(type(v) is int for v in identity.values()),'typed source identity/SHA required')
        s=os.lstat(q);require(all(getattr(s,k)==v for k,v in identity.items()) and stat.S_ISREG(s.st_mode)
                             and stat.S_IMODE(s.st_mode) in (0o400,0o644) and s.st_nlink==1 and s.st_uid==os.getuid()
                             and 0<s.st_size<=128*1048576,'generated source epoch/type/mode differs')
        require(type(source) is dict and type(source.get('bytes')) is int
                and source==dict(candidate_id=name,sha256=digest,bytes=s.st_size),'receiving candidate identity differs')
        require((s.st_dev,s.st_ino) not in ids and digest not in hashes,'distinct generated inputs required')
        ids.add((s.st_dev,s.st_ino));hashes.add(digest)
    require(d['transport_source_sha256']=={n:d['execution_source_sha256'][str(ROOT/'bench/sync'/n)] for n in SCRIPT_NAMES},'copied transport pins differ')
    for label in ['stock','ox']:command_plan(d['binaries'][label],tool,w/label)
    return d
