"""Pure shared8 experimental comparison proposal; no hashing, IO or execution."""
import copy
from plan import matrix,EXPERIMENTAL,require
REFERENCE='unison-sdk171-2724-v1-single'

def shared_matrix(reference,experimental,fixtures,memory_bytes):
    require(type(reference) is dict and reference.get('build_id')==REFERENCE,
            'qualified reference build identity required')
    require(type(experimental) is dict and experimental.get('build_id')==EXPERIMENTAL,
            'explicit unqualified experimental build identity required')
    # Reuse the established protocol/codec command constructor. Do not change
    # historical 18-credit matrix requests or turn this into a native entrypoint.
    cases=copy.deepcopy(matrix(reference,experimental,fixtures,memory_bytes))
    for case in cases:
        if case['backend']=='experimental' and case['threads_including_caller']==18:
            case['threads_including_caller']=2
            index=case['command'].index('--threads')+1
            require(case['command'][index]=='18','unexpected constructor thread layout')
            case['command'][index]='2'
        case['reserved_cpu_credits']=8
        case['owner_cpu_credits']=2
        require(case['threads_including_caller']+2<=8,'SDK and owner exceed shared8')
    cases.sort(key=lambda c: (('uncompressed','jpeg','jxl').index(c['codec']),
                             0 if c['backend']=='reference' else c['threads_including_caller']))
    return dict(schema='unison-shared-sdk-host-matrix-proposal/1',cases=cases,
        limits=dict(calls=12,inputs=3,sequential_calls=True,cpu_credits=8,
            token_indexes=list(range(8)),owner_credits=2,native_thread_targets=[1,2,6]),
        runtime_admitted=False,runtime_qualified=False,hard_os_thread_cap=False,
        rss_cap=False,requires_fresh_owned_executor=True,
        old_18_credit_plan_modified=False)
