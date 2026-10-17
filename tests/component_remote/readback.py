"""Separate post-run metadata audit; no payload, process signal or lock release.

This tool is deliberately outside the frozen runtime source closure. Trusted
callers provide plan/admission pins; those pins do not authenticate a parent
terminal. Use actual owning-tool evidence separately, even when this passes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.contract import CASES, PARAMETERS
from component_remote.io import load, read
from component_remote.audit import audit_prefix
from component_remote.coordinator import inherited_identities
from shared_cpu_pool import require, unique_object
from shared_io_pool import read_manifest

def compare(plan,plan_sha,admission,admission_sha,records,calls,canonical_ids):
    require(plan['schema']=='unison-component-remote/1' and plan['parameters']==PARAMETERS,
            'fixed frozen component plan required')
    require(admission['state']=='ROOT_ADMITTED_ONE_COMPONENT_RPC_JOB' and
      admission['plan_sha256']==plan_sha and admission['workspace']==plan['workspace'],
      'admission does not bind this plan/workspace')
    attempt=records['ATTEMPT'];start=records['START'];closed=records['AGGREGATE-CLOSED']
    settled=records['REMOTE-SETTLED'];result=records['WORKER-RESULT'];packet=records['WORKER-PACKET']
    owner=start['owner_pid'];worker=start['worker_pid']
    require(type(owner) is int and owner>0 and type(worker) is int and worker>0 and worker!=owner and
      attempt['owner_pid']==owner and packet['parent_pid']==owner and packet['plan']==plan,
      'owner/worker/packet binding differs')
    require(attempt['admission_sha256']==start['admission_sha256']==admission_sha and
      start['cpu_indexes']==list(range(8)) and start['io_mode']=='EX_GLOBAL',
      'wrong admission or shared resource range')
    inherited=start['inherited_fds']
    require(inherited==packet['inherited_fds'] and len(inherited)==9 and
      all(type(row['fd']) is int and row['fd']>=0 for row in inherited) and
      len({row['fd'] for row in inherited})==9 and
      [(row['device'],row['inode']) for row in inherited]==canonical_ids,
      'canonical inherited IO+CPU descriptions differ')
    proof=closed['worker']
    require(proof['pid']==worker and proof['reaped'] is True and type(proof['returncode']) is int and
      proof['other_group_members_absent_before_reap'] is True and proof['timed_out'] is False,
      'worker actual wait/group proof missing')
    require(settled['worker_finished_starting_calls'] is True and settled['calls']==closed['calls']==calls and
      closed['cpu_closed'] is True and closed['io_closed'] is True,'call or bundle settlement differs')
    passed=proof['returncode']==0
    require(type(closed['functional_pass']) is bool and closed['functional_pass'] is passed and
      settled['functional_pass'] is passed and result['complete'] is passed,
      'functional pass/failed-prefix status mismatch')
    for row in calls:
        if not row.get('no_dispatch'):
            require(not {row['client_pid'],row['supervisor_pid'],row['server_pid']}.intersection({owner,worker}),
                    'child identity aliases its retained ancestor')
    if passed:
        require(len(calls)==len(result['cases'])==len(CASES) and all(
          not row['no_dispatch'] and not row['server_not_created'] for row in calls),
          'successful result lacks all eight actual calls')
    return {'scope':'metadata child/worker/bundle report binding only',
      'attempted_case_records':len(calls),'worker_reported_exit':proof['returncode'],
      'functional_pass_reported':passed,'functional_inputs_independently_rehashed':False,
      'parent_terminal_authenticated':False,'resource_release_authorized':False,
      'canonical_ID_observations_match':True,
      'next_evidence':'actual owning-tool terminal; input/functional audit under authorized IO'}

def inspect(plan_path,plan_sha,admission_path,admission_sha):
    raw=read(plan_path);require(hashlib.sha256(raw).hexdigest()==plan_sha,'frozen plan byte pin differs')
    plan=json.loads(raw,object_pairs_hook=unique_object);admission=read_manifest(admission_path,admission_sha)
    workspace=Path(plan['workspace'])
    require(workspace.parent==Path('/private/tmp') and re.fullmatch(r'u-cr-[0-9a-f]{8,16}',workspace.name)
      is not None,'unexpected result namespace')
    value=os.lstat(workspace)
    require(stat.S_ISDIR(value.st_mode) and value.st_uid==os.getuid() and
      stat.S_IMODE(value.st_mode)==0o700,'owned result workspace missing/replaced')
    require(not any((workspace/name).exists() for name in ('OWNER-UNKNOWN.json','WORKER-UNKNOWN.json')),
            'unresolved ownership marker present')
    names=('ATTEMPT','START','WORKER-PACKET','WORKER-RESULT','REMOTE-SETTLED','AGGREGATE-CLOSED')
    records={name:load(workspace/(name+'.json')) for name in names}
    calls=audit_prefix(plan,workspace) # independent raw proxy/intent/outcome reparse; no input payloads
    return compare(plan,plan_sha,admission,admission_sha,records,calls,inherited_identities())

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('plan','plan-sha256','admission','admission-sha256'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.plan,args.plan_sha256,args.admission,args.admission_sha256),indent=2))
