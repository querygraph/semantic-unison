"""Stock<->OxCaml cross-compiler peer receiving contract; source/planning only, no grants.

The plan's compiler is the client; its pinned peer, built by the other
compiler, serves the right replica. Cases cover seed, delta update, reverse
deletion, a skipped conflict, xattr/ACL properties and a gated DNG receive at
each endpoint, so both directions cross the RPC boundary.
"""
import re
from copy import deepcopy
from pathlib import PurePosixPath

SCHEMA='unison-current-cross-peer-receiving-execution/1'
PROPS=['-xattrs','-acl']
OPTIONS=([],PROPS)
SKIPPED='(0 items transferred, 1 skipped, 0 failed)'
# name, CLI calls, fake validator calls.
CASES=(('seed-update',3,0),('reverse-deletion',2,0),('conflict-skip',2,0),('properties',2,0),('dng-receive',3,2))
LIMITS=dict(cpu_credits=8,endpoint_workers=2,owner_credits=2,compiler_jobs=0,
    cases=5,CLI_calls=12,fake_validator_calls=2,SDK_calls=0,
    declared_producer_interruptions=0,declared_client_SIGINT_controls=0,
    external_producer_calls=0,external_merge_calls=0,
    owner_observation_seconds=600,worker_observation_seconds=570,per_CLI_observation_seconds=90,
    declared_logical_IO_bytes=1024**3,physical_IO_cap=False,retry_outside_declared_cases=False)
TOTALS=dict(cli_calls=12,fake_validators=2,copy=0,merge=0,producer_interruptions=0,client_cancellations=0)


def plan(workspace,compiler):
    if compiler not in ('stock','ox'):raise ValueError('one separately coordinated client compiler required')
    if type(workspace) is not str:raise ValueError('canonical fresh private namespace required')
    root=PurePosixPath(workspace)
    if str(root)!=workspace or root.parent!=PurePosixPath('/private/tmp') or re.fullmatch('u-xpeer-[0-9a-f]{16}',root.name) is None:
        raise ValueError('canonical fresh cross-peer namespace required')
    rows=[dict(index=i,family=name,arguments=[],name=name,directory=str(root/name),max_CLI_calls=cli,max_fake_validator_calls=helpers)
          for i,(name,cli,helpers) in enumerate(CASES)]
    if sum(r['max_CLI_calls'] for r in rows)!=12 or sum(r['max_fake_validator_calls'] for r in rows)!=2:
        raise ValueError('complete declared per-compiler call budget differs')
    return dict(schema='unison-current-cross-peer-case-contract/1',compiler=compiler,workspace=workspace,rows=rows,
        limits=deepcopy(LIMITS),production_CLI_or_helper_invoked=False,runtime_admitted=False,SDK_calls=0)


def call(name,sequence):
    """(policy, options, client mode, server mode, expected exit, designated line) of one call."""
    calls={n:c for n,c,_ in CASES}
    if name not in calls or type(sequence) is not int or not 1<=sequence<=calls[name]:raise ValueError('undeclared cross-peer case call')
    if name=='conflict-skip' and sequence==2:return 'require',[],'pass','pass',1,SKIPPED
    if name=='dng-receive' and sequence==1:return 'off',[],'pass','pass',0,None
    return 'require',(PROPS if name=='properties' else []),'pass','pass',0,None
