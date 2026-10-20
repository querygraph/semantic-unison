"""Pure named receiving plan/admission contract; no lock, IO or execution grant.

One plan covers one compiler: its binary is both client and server. Callers
authenticate metadata first and hash executables only under owned IO. The
owner consumes the one-use workspace and retains unknown process/FD state.
"""
import hashlib,math,re
from sdk_merge_receiving.plan import require,path,digest
from sdk_negative_receiving.admission import PYTHON,PYTHON_SHA,POLICY,IO,REPOSITORY,COMPILERS,exact,reference,inventory
from current_validation_paths.contract import plan as case_plan,LIMITS
from current_validation_paths import successors
SCHEMAS={'unison-current-named-receiving-execution/1':'named',**{schema:'successor' for schema in successors.SUITES}}

TARGET='current-named-receiving'
LEGACY='tests/validation_paths/run.py'


def validate(packet,*,source,execution_sources,production_sources):
    fields={'schema','repository','workspace','compiler','interpreter','binary','build','legacy_source','rows','limits',
            'source_pins','production_sha256','prerequisite_sha256','cpu_policy_sha256','io_manifest_sha256'}
    if type(packet) is dict and packet.get('schema') in SCHEMAS and successors.peered(packet['schema']):fields=fields|{'peer'}
    require(type(packet) is dict and set(packet)==fields and packet['schema'] in SCHEMAS,
            'exact named execution packet required')
    successor=successors.contract(packet['schema'])
    require(packet['repository']==REPOSITORY,'exact reviewed owner repository required')
    require(exact(packet['interpreter'],dict(path=PYTHON,sha256=PYTHON_SHA)),'qualified pinned interpreter required')
    require(packet['cpu_policy_sha256']==POLICY and packet['io_manifest_sha256']==IO,'exact standing8/EXglobal pins required')
    require(packet['compiler'] in COMPILERS,'one exact compiler label required')
    require(type(source) is str,'original legacy source text required')
    raw=source.encode()
    require(exact(packet['legacy_source'],dict(path=REPOSITORY+'/'+LEGACY,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())),
            'exact original legacy case source required')
    contract=successor.plan(packet['workspace'],packet['compiler']) if successor else case_plan(source,packet['workspace'],packet['compiler'])
    require(exact(packet['rows'],contract['rows']) and exact(packet['limits'],successor.LIMITS if successor else LIMITS),'complete original ordered cases/limits required')
    inventory(packet['source_pins'],execution_sources);inventory(packet['production_sha256'],production_sources)
    require(packet['source_pins'].get(LEGACY)==packet['legacy_source']['sha256'],'legacy source must be pinned execution')
    build=packet['build'];binary=packet['binary']
    require(type(build) is dict and set(build)=={'receipt','compiler'},'exact build/compiler references required')
    reference(build['receipt']);reference(build['compiler']);reference(binary)
    require(build['compiler']['path']==COMPILERS[packet['compiler']],'canonical compiler executable required')
    receipts={build['receipt']['path']:build['receipt']['sha256']}
    executables=[PYTHON,binary['path'],build['compiler']['path']]
    if 'peer' in packet:
        peer=packet['peer']
        require(type(peer) is dict and set(peer)=={'compiler','binary','build'} and peer['compiler'] in COMPILERS
            and peer['compiler']!=packet['compiler'] and type(peer['build']) is dict and set(peer['build'])=={'receipt','compiler'},
            'exact other-compiler peer build required')
        reference(peer['build']['receipt']);reference(peer['build']['compiler']);reference(peer['binary'])
        require(peer['build']['compiler']['path']==COMPILERS[peer['compiler']],'canonical peer compiler executable required')
        receipts[peer['build']['receipt']['path']]=peer['build']['receipt']['sha256']
        executables+=[peer['binary']['path'],peer['build']['compiler']['path']]
    require(exact(packet['prerequisite_sha256'],receipts),
            'exactly the authenticated build receipt prerequisites required')
    require(len(set(executables))==len(executables),'distinct interpreter/binary/compiler required')
    return contract


def worker_command(packet,plan_ref):
    reference(plan_ref)
    return [PYTHON,packet['repository']+'/tests/current_validation_paths/entry.py','--worker',
            '--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256'],'--workspace',packet['workspace']]


def check(admission,packet,*,request_ref,plan_ref,command,now):
    """Exact reviewed declarations only; a deadline is a start condition, not a cancel."""
    reference(request_ref);reference(plan_ref)
    require(exact(command,worker_command(packet,plan_ref)),'exact owner-derived worker argv required')
    fields={'schema','state','request','plan','workspace','compiler','command','source_pins','production_sha256',
            'limits','cpu_token_indexes','cpu_policy_sha256','io_manifest_sha256','start_deadline_unix','nonce'}
    require(type(admission) is dict and set(admission)==fields
        and admission['schema']=='unison-current-named-receiving-admission/1'
        and admission['state']=='ADMITTED_ONE_CURRENT_NAMED_RECEIVING','fresh exact named admission required')
    require(exact(admission['request'],request_ref) and exact(admission['plan'],plan_ref)
        and admission['workspace']==packet['workspace'] and admission['compiler']==packet['compiler']
        and exact(admission['command'],command) and exact(admission['source_pins'],packet['source_pins'])
        and exact(admission['production_sha256'],packet['production_sha256'])
        and exact(admission['limits'],packet['limits']) and exact(admission['cpu_token_indexes'],list(range(8)))
        and admission['cpu_policy_sha256']==POLICY and admission['io_manifest_sha256']==IO,
        'admission differs from exact reviewed command/source/resource declarations')
    deadline=admission['start_deadline_unix']
    require(type(now) in (int,float) and math.isfinite(now) and type(deadline) in (int,float)
        and math.isfinite(deadline) and now<deadline,'expired or nonfinite start deadline; no renewal/replay')
    require(type(admission['nonce']) is str and re.fullmatch('[0-9a-f]{32}',admission['nonce']) is not None,
            'exact fresh owner nonce required')
    return tuple(range(8))
