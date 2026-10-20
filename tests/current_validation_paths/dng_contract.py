"""Built-in DNG merge receiving contract; source/planning only, no grants.

Successor of the bare `tests/dng_merge/run.py` harness. Per-case call and
fake-validator counts come from that harness's last actual run directories;
every failed call names the exact client diagnostic that proves its decline.
"""
import re
from copy import deepcopy
from pathlib import PurePosixPath

OPTS=['-backupcurrent','Name *.dng','-merge','Name *.dng -> unison:dng-xmp-scalars/0']
MISMATCH=['-backupcurrent','Name *.dng','-merge','Name *.dng -> unison:dng-xmp-scalars/99']
DISABLED=['-backupcurrent','Name *.dng']
FORK=[*OPTS,'-rsrc','true']
OPTIONS=([],OPTS,MISMATCH,DISABLED,FORK)
SCHEMA='unison-current-dng-merge-receiving-execution/1'
PROFILE='Failed [image.dng]: DNG scalar merge: no compatible fixed-region profile: '
BASE='Failed [image.dng]: DNG scalar merge requires a saved common version; enable backupcurrent before synchronization'
# name, maximum CLI calls, fake validator calls, seed saves a common version.
CASES=(
 ('disjoint',3,2),('swapped',3,2),('competing',2,0),('opaque-payload',2,0),('unknown-field',2,0),
 ('missing-base',2,0),('first-receiver-reject',2,1),('deleted-field',2,0),('stale-base',2,0),
 ('second-receiver-reject',3,4),('policy-mismatch',2,0),('policy-disabled',2,0),('resource-fork',2,0),
)
DESIGNATED={
 'competing':PROFILE+'competing scalar edits',
 'opaque-payload':PROFILE+'reconciliation protected bytes changed',
 'unknown-field':PROFILE+'non-allowlisted packet bytes changed',
 'deleted-field':PROFILE+'non-allowlisted packet bytes changed',
 'missing-base':BASE,'stale-base':BASE,
 'policy-mismatch':'Failed [image.dng]: Unknown built-in merge policy unison:dng-xmp-scalars/99; supported: unison:dng-xmp-scalars/0',
 'policy-disabled':'(0 items transferred, 1 skipped, 0 failed)',
 'resource-fork':'Failed [image.dng]: DNG scalar merge: regular files without resource forks are required',
}
LIMITS=dict(cpu_credits=8,endpoint_workers=2,owner_credits=2,compiler_jobs=0,
    cases=13,CLI_calls=29,fake_validator_calls=9,SDK_calls=0,
    declared_producer_interruptions=0,declared_client_SIGINT_controls=0,
    external_producer_calls=0,external_merge_calls=0,
    owner_observation_seconds=600,worker_observation_seconds=570,per_CLI_observation_seconds=90,
    declared_logical_IO_bytes=1024**3,physical_IO_cap=False,retry_outside_declared_cases=False)
TOTALS=dict(cli_calls=29,fake_validators=9,copy=0,merge=0,producer_interruptions=0,client_cancellations=0)


def plan(workspace,compiler):
    if compiler not in ('stock','ox'):raise ValueError('one separately coordinated compiler run required')
    if type(workspace) is not str:raise ValueError('canonical fresh private namespace required')
    root=PurePosixPath(workspace)
    if str(root)!=workspace or root.parent!=PurePosixPath('/private/tmp') or re.fullmatch('u-dmerge-[0-9a-f]{16}',root.name) is None:
        raise ValueError('canonical fresh DNG merge namespace required')
    rows=[dict(index=i,family=name,arguments=[],name=name,directory=str(root/name),max_CLI_calls=cli,max_fake_validator_calls=helpers)
          for i,(name,cli,helpers) in enumerate(CASES)]
    if sum(r['max_CLI_calls'] for r in rows)!=29 or sum(r['max_fake_validator_calls'] for r in rows)!=9:
        raise ValueError('complete declared per-compiler call budget differs')
    return dict(schema='unison-current-dng-merge-case-contract/1',compiler=compiler,workspace=workspace,rows=rows,
        limits=deepcopy(LIMITS),production_CLI_or_helper_invoked=False,runtime_admitted=False,SDK_calls=0)


def call(name,sequence):
    """(policy, options, client mode, server mode, expected exit, designated line) of one call."""
    if sequence==1:return 'off',([] if name=='missing-base' else OPTS),'pass','pass',0,None
    if sequence==2:
        options={'policy-mismatch':MISMATCH,'policy-disabled':DISABLED,'resource-fork':FORK}.get(name,OPTS)
        client='error' if name=='first-receiver-reject' else 'pass'
        server='error' if name=='second-receiver-reject' else 'pass'
        code=0 if name in ('disjoint','swapped') else 1 if name=='policy-disabled' else 2
        return 'require',options,client,server,code,DESIGNATED.get(name)
    if sequence==3 and name in ('disjoint','swapped','second-receiver-reject'):return 'require',OPTS,'pass','pass',0,None
    raise ValueError('undeclared DNG merge case call')
