"""Filesystem property transitions receiving contract; source/planning only, no grants.

End-to-end remote synchronization of a zero-length file, a punched-hole file,
an extended attribute and an ACL, each through create/change/remove, with the
default-off preference controls. No fake validator runs: these are not DNGs.
"""
import re
from copy import deepcopy
from pathlib import PurePosixPath

SCHEMA='unison-current-fs-properties-receiving-execution/1'
XATTRS=['-xattrs']
ACL=['-acl']
OPTIONS=([],XATTRS,ACL)
# name, CLI calls; every call is expected to exit 0.
CASES=(('zero-length',4),('holes',2),('xattr-default-off',2),('xattr',4),('acl-default-off',2),('acl',3))
LIMITS=dict(cpu_credits=8,endpoint_workers=2,owner_credits=2,compiler_jobs=0,
    cases=6,CLI_calls=17,fake_validator_calls=0,SDK_calls=0,
    declared_producer_interruptions=0,declared_client_SIGINT_controls=0,
    external_producer_calls=0,external_merge_calls=0,
    owner_observation_seconds=600,worker_observation_seconds=570,per_CLI_observation_seconds=90,
    declared_logical_IO_bytes=1024**3,physical_IO_cap=False,retry_outside_declared_cases=False)
TOTALS=dict(cli_calls=17,fake_validators=0,copy=0,merge=0,producer_interruptions=0,client_cancellations=0)


def plan(workspace,compiler):
    if compiler not in ('stock','ox'):raise ValueError('one separately coordinated compiler run required')
    if type(workspace) is not str:raise ValueError('canonical fresh private namespace required')
    root=PurePosixPath(workspace)
    if str(root)!=workspace or root.parent!=PurePosixPath('/private/tmp') or re.fullmatch('u-fsprop-[0-9a-f]{16}',root.name) is None:
        raise ValueError('canonical fresh filesystem properties namespace required')
    rows=[dict(index=i,family=name,arguments=[],name=name,directory=str(root/name),max_CLI_calls=cli,max_fake_validator_calls=0)
          for i,(name,cli) in enumerate(CASES)]
    if sum(r['max_CLI_calls'] for r in rows)!=17:raise ValueError('complete declared per-compiler call budget differs')
    return dict(schema='unison-current-fs-properties-case-contract/1',compiler=compiler,workspace=workspace,rows=rows,
        limits=deepcopy(LIMITS),production_CLI_or_helper_invoked=False,runtime_admitted=False,SDK_calls=0)


def call(name,sequence):
    """(policy, options, client mode, server mode, expected exit, designated line) of one call."""
    calls=dict(CASES)
    if name not in calls or type(sequence) is not int or not 1<=sequence<=calls[name]:raise ValueError('undeclared filesystem properties case call')
    options=XATTRS if name=='xattr' else ACL if name=='acl' else []
    return 'require',options,'pass','pass',0,None
