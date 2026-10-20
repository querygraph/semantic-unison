"""Source-bound supplemental audit of saved Darwin pre-reap census receipts.

Never mutates raw results, releases an FD, signals a process or infers the
aggregate/parent terminal. Only the exact producer revision below is accepted.
"""
import copy
import hashlib
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench/sync'))
import timed_shared

OWNERSHIP_SHA='eba29bdcef1f1c1d99422fd56a9df8dab7c60b622d3b0d4070b3bfaf141d47d3'


def audit(result, source):
    if hashlib.sha256(source).hexdigest()!=OWNERSHIP_SHA:
        raise ValueError('unqualified Darwin producer source')
    if result['host']['system']!='Darwin':raise ValueError('Darwin result required')
    view=copy.deepcopy(result);derived=[]
    def qualify(owner,where):
        if owner.get('other_group_members_absent_before_reap') is True:return
        if not (owner.get('other_group_members_absent_before_reap','MISSING') is None
                and owner.get('group_cleanup_result') in ('only_owned_leader_zombie_darwin','no_members_darwin')
                and owner.get('observation_error','MISSING') is None
                and owner.get('cancel_reason','MISSING') is None
                and owner.get('hard_kill_required') is False
                and owner.get('group_cleanup_before_leader_reap') is True
                and owner.get('reaped') is True
                and type(owner.get('pid')) is int and owner['pid']>0
                and type(owner.get('returncode')) is int and owner['returncode']==0):
            raise ValueError('unqualified pre-reap census: '+str(where))
        derived.append(dict(location=where,pid=owner['pid'],raw_boolean=None,
                            source_census_branch=owner['group_cleanup_result'],
                            inference='Pinned producer qualified only its own reserved zombie or no members before wait4'))
        owner['other_group_members_absent_before_reap']=True
    for index,entry in enumerate(view['invocations']):
        for key in ('client_cleanup','supervisor_cleanup'):
            qualify(entry['outcome'][key],['invocations',index,'outcome',key])
    for index,row in enumerate(view['samples']):
        for stage in ('seed_sync','update_sync','noop_sync'):
            for key in ('client_cleanup','supervisor_cleanup'):
                qualify(row[stage][key],['samples',index,stage,key])
    proof=timed_shared.audit(view)
    return dict(schema='unison-saved-darwin-census-audit/1',state='SOURCE_DERIVED_SUPPLEMENT_RAW_UNCHANGED',
                producer_sha256=OWNERSHIP_SHA,derived_receipt_locations=derived,matrix=proof,
                parent_terminal_or_worker_reap_inferred=False),view
