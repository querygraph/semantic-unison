"""Complete original named-path case contract; source/planning only, no grants.

The legacy runner is parsed, never executed. A retained successor must preserve
all21 default cases, include deliberate producer interruption and client cancel,
and audit every actual child before retiring its IO/CPU ownership.
"""
import ast,hashlib,re
from copy import deepcopy
from pathlib import PurePosixPath

# family, arguments, logical name, declared maximum CLI/fake validators.
CASES=(
 ('resumed',('complete','pass'),'resume-complete-pass',3,1),
 ('resumed',('complete','error'),'resume-complete-error',4,2),
 ('resumed',('partial','pass'),'resume-partial-pass',3,1),
 ('resumed',('partial','error'),'resume-partial-error',4,2),
 ('external',('pass','require'),'external-pass-require',2,1),
 ('external',('error','require'),'external-error-require',3,2),
 ('external',('error','warn'),'external-error-warn',2,1),
 ('external',('error','off'),'external-error-off',2,0),
 ('external',('mutate','warn'),'external-mutate-warn',3,2),
 ('moved',('pass','require'),'reuse-pass-require',3,2),
 ('moved',('error','require'),'reuse-error-require',4,3),
 ('moved',('error','warn'),'reuse-error-warn',3,2),
 ('merged',('pass','pass'),'merge-pass-pass',3,3),
 ('merged',('error','pass'),'merge-error-pass',4,4),
 ('merged',('pass','error'),'merge-pass-error',4,5),
 ('merged',('pass','wrong-receipt'),'merge-pass-wrong-receipt',4,5),
 ('timed_out',('require',),'timeout-require',4,3),
 ('timed_out',('warn',),'timeout-warn',4,3),
 ('cancelled',('require',),'cancel-require',4,3),
 ('cancelled',('warn',),'cancel-warn',4,3),
 ('directory_admission',(),'directory-execution-admission',2,6),
)
LIMITS=dict(cpu_credits=8,endpoint_workers=2,owner_credits=2,compiler_jobs=0,
    cases=21,CLI_calls=69,fake_validator_calls=54,SDK_calls=0,
    declared_producer_interruptions=4,declared_client_SIGINT_controls=2,
    external_producer_calls=9,external_merge_calls=7,
    owner_observation_seconds=600,worker_observation_seconds=570,per_CLI_observation_seconds=90,
    declared_logical_IO_bytes=8*1024**3,physical_IO_cap=False,retry_outside_declared_cases=False)


def legacy_case_inventory(source):
    """Prove inclusion/order of the original default case invocations.

    Optional old helper-limiter mode is separate, not silently relabeled default.
    No source expression, function, import or subprocess is executed here.
    """
    tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    families={row[0] for row in CASES};result=[]
    def walk(statements):
        for statement in statements:
            if isinstance(statement,ast.Try):
                walk(statement.body)
                continue
            if isinstance(statement,ast.For):
                calls=[n for n in ast.walk(statement) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in families]
                if not calls:continue
                if len(calls)!=1:raise ValueError('one exact named case call per legacy default loop required')
                call=calls[0];values=ast.literal_eval(statement.iter)
                variables=[statement.target.id] if isinstance(statement.target,ast.Name) else [n.id for n in statement.target.elts]
                for value in values:
                    value=(value,) if len(variables)==1 else value
                    environment=dict(zip(variables,value))
                    arguments=tuple(environment[n.id] if isinstance(n,ast.Name) else ast.literal_eval(n) for n in call.args[2:])
                    result.append((call.func.id,arguments))
            elif isinstance(statement,ast.Assign) and isinstance(statement.value,ast.Call):
                call=statement.value
                if isinstance(call.func,ast.Name) and call.func.id in families:
                    if call.func.id!='directory_admission' or len(call.args)!=2:raise ValueError('unexpected direct legacy case')
                    result.append((call.func.id,()))
    walk(main.body)
    expected=[(row[0],row[1]) for row in CASES]
    if result!=expected:raise ValueError('legacy default case inventory changed; refuse omission/reordering')
    return result


def plan(source,workspace,compiler):
    if type(source) is not str or len(source.encode())>256*1024:raise ValueError('bounded original source required')
    if compiler not in ('stock','ox'):raise ValueError('one separately coordinated compiler run required')
    if type(workspace) is not str:raise ValueError('canonical fresh private namespace required')
    root=PurePosixPath(workspace)
    if str(root)!=workspace or root.parent!=PurePosixPath('/private/tmp') or re.fullmatch('u-vpath-[0-9a-f]{16}',root.name) is None:
        raise ValueError('canonical fresh named-path namespace required')
    legacy_case_inventory(source)
    rows=[dict(index=i,family=family,arguments=list(args),name=name,directory=str(root/name),
               max_CLI_calls=cli,max_fake_validator_calls=helpers) for i,(family,args,name,cli,helpers) in enumerate(CASES)]
    if sum(r['max_CLI_calls'] for r in rows)!=69 or sum(r['max_fake_validator_calls'] for r in rows)!=54:
        raise ValueError('complete declared per-compiler call budget differs')
    return dict(schema='unison-current-named-validation-case-contract/1',compiler=compiler,workspace=workspace,
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),rows=rows,limits=deepcopy(LIMITS),
        production_CLI_or_helper_invoked=False,runtime_admitted=False,SDK_calls=0,
        source_photos_or_retained_camera_inputs_allowed=False)
