"""Pure current merge plan/admission contract; no lock, IO or execution grant.

Callers independently enumerate trusted source inventories, authenticate bounded
metadata, then verify build/artifact bytes under owned IO. The final owner must
consume the one-use workspace atomically and retain all unknown process/FD state.
"""
import math
import re
from pathlib import Path
from sdk_merge_receiving.plan import schedule,require,path,digest,LIMITS
from sdk_merge_receiving.inputs import bind

PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PYTHON_SHA='56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'
POLICY='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352'
IO='f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636'
REPOSITORY=str(Path(__file__).resolve().parents[2])
COMPILERS={'stock':'/Users/alexy/.opam/default/bin/ocamlopt.opt',
           'ox':'/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt.opt'}


def exact(left,right):
    """JSON equality without Python's bool/int coercion."""
    import json
    return json.dumps(left,sort_keys=True,allow_nan=False,separators=(',',':'))==json.dumps(
        right,sort_keys=True,allow_nan=False,separators=(',',':'))


def reference(value):
    require(type(value) is dict and set(value)=={'path','sha256'},'exact metadata reference required')
    path(value['path']);digest(value['sha256'])


def inventory(value,names):
    require(type(value) is dict and value and set(value)==set(names),'complete trusted source inventory required')
    for name,sha in value.items():
        require(type(name) is str and not name.startswith('/') and '..' not in name.split('/')
                and all(part not in ('','.') for part in name.split('/')),
                'canonical repository-relative source required')
        digest(sha)


def validate(packet,*,execution_sources,production_sources,expected_uid):
    fields={'schema','repository','workspace','interpreter','binaries','tool','builds',
            'cases','source_observations','input_manifest','sdk_manifest','execution_sha256',
            'production_sha256','prerequisite_sha256','limits','cpu_policy_sha256','io_manifest_sha256'}
    require(type(packet) is dict and set(packet)==fields
            and packet['schema']=='unison-current-sdk-merge-execution/1','exact execution packet required')
    path(packet['repository'])
    require(packet['repository']==REPOSITORY,'exact reviewed owner repository required')
    require(exact(packet['interpreter'],dict(path=PYTHON,sha256=PYTHON_SHA)),
            'qualified pinned interpreter required')
    require(packet['cpu_policy_sha256']==POLICY and packet['io_manifest_sha256']==IO
            and exact(packet['limits'],LIMITS),'exact standing8/EXglobal/finite limits required')
    contract=schedule(packet['binaries'],packet['tool'],packet['workspace'])
    inventory(packet['execution_sha256'],execution_sources)
    inventory(packet['production_sha256'],production_sources)
    prerequisites=packet['prerequisite_sha256']
    require(type(prerequisites) is dict and prerequisites,'authenticated prerequisites required')
    for name,sha in prerequisites.items():path(name);digest(sha)
    require(type(packet['builds']) is dict and set(packet['builds'])=={'stock','ox'},'both qualified builds required')
    references=[packet['input_manifest'],packet['sdk_manifest']]
    for label in ('stock','ox'):
        build=packet['builds'][label]
        require(type(build) is dict and set(build)=={'receipt','compiler'},'exact build/compiler references required')
        reference(build['compiler'])
        require(build['compiler']['path']==COMPILERS[label],'canonical compiler executable required')
        references.append(build['receipt'])
    seen=set()
    for item in references:
        reference(item)
        require(item['path'] not in seen and prerequisites.get(item['path'])==item['sha256'],
                'distinct referenced prerequisite absent or changed')
        seen.add(item['path'])
    rows=bind(packet['cases'],packet['source_observations'],expected_uid=expected_uid)
    artifact_paths={PYTHON,packet['tool']['path'],*(v['path'] for v in packet['binaries'].values()),
                    *(b['compiler']['path'] for b in packet['builds'].values())}
    require(len(artifact_paths)==6 and not artifact_paths.intersection(row['path'] for row in rows),
            'distinct interpreter/tool/peer/compiler/source identities required')
    return contract


def worker_command(packet,plan_ref):
    reference(plan_ref)
    return [PYTHON,packet['repository']+'/tests/sdk_merge_receiving/entry.py','--worker',
            '--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256'],
            '--workspace',packet['workspace']]


def check(admission,packet,*,request_ref,plan_ref,command,now):
    """Check exact reviewed declarations, not current files or consumed state.

    packet must already pass validate + current metadata checks. A deadline is a
    start condition, not permission to cancel an owner or release on expiry.
    """
    reference(request_ref);reference(plan_ref)
    require(exact(command,worker_command(packet,plan_ref)),
            'exact owner-derived worker argv required')
    fields={'schema','state','request','plan','workspace','command','execution_sha256',
            'production_sha256','limits','cpu_token_indexes','cpu_policy_sha256',
            'io_manifest_sha256','start_deadline_unix','nonce'}
    require(type(admission) is dict and set(admission)==fields
        and admission['schema']=='unison-current-sdk-merge-admission/1'
        and admission['state']=='ROOT_ADMITTED_ONE_CURRENT_SDK_MERGE','fresh exact merge admission required')
    require(exact(admission['request'],request_ref) and exact(admission['plan'],plan_ref)
        and admission['workspace']==packet['workspace'] and exact(admission['command'],command)
        and exact(admission['execution_sha256'],packet['execution_sha256'])
        and exact(admission['production_sha256'],packet['production_sha256'])
        and exact(admission['limits'],LIMITS) and exact(admission['cpu_token_indexes'],list(range(8)))
        and admission['cpu_policy_sha256']==POLICY and admission['io_manifest_sha256']==IO,
        'admission differs from exact reviewed command/source/resource declarations')
    deadline=admission['start_deadline_unix']
    require(type(now) in (int,float) and math.isfinite(now)
        and type(deadline) in (int,float) and math.isfinite(deadline) and now<deadline,
        'expired or nonfinite start deadline; no renewal/replay')
    require(type(admission['nonce']) is str and re.fullmatch('[0-9a-f]{32}',admission['nonce']),
            'exact fresh owner nonce required')
    return tuple(range(8))
