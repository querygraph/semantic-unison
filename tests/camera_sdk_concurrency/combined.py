"""Pure two-candidate helper/live/receipt join; CLI/worker/FD closure is separate."""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'camera_sdk_receiving'))
import sdk_audit
from live_records import parse as parse_live, bound, IncompleteEvidence


def census(log, expected, endpoint):
    if endpoint not in ('client','server') or type(expected) is not list or len(expected)!=2:
        raise IncompleteEvidence('exact two-helper endpoint census required')
    ids=set();pids=set()
    for row in expected:
        if (type(row) is not dict or set(row)!={'candidate_id','helper_pid','sha256','bytes'}
                or type(row['candidate_id']) is not str or not 1<=len(row['candidate_id'])<=512
                or type(row['helper_pid']) is not int or not 0<row['helper_pid']<2**31
                or type(row['bytes']) is not int or not 0<row['bytes']<2**63
                or type(row['sha256']) is not str or re.fullmatch('[0-9a-f]{64}',row['sha256']) is None
                or row['candidate_id'] in ids or row['helper_pid'] in pids):
            raise IncompleteEvidence('distinct typed candidate/helper bindings required')
        ids.add(row['candidate_id']);pids.add(row['helper_pid'])
    processes=sdk_audit.records.parse(log);groups=sdk_audit.records.parse_groups(log)
    if len(processes)!=2 or len(groups)!=2:
        raise IncompleteEvidence('exact process/group census required')
    result=[]
    for row in expected:
        ps=[p for p in processes if p.pid==row['helper_pid']]
        gs=[g for g in groups if g.pid==row['helper_pid']]
        if len(ps)!=1 or len(gs)!=1:raise IncompleteEvidence('duplicate or missing process/group identity')
        p,g=ps[0],gs[0]
        if (p.endpoint!=endpoint or g.endpoint!=endpoint or p.candidate_sha256!=row['sha256']
                or g.candidate_sha256!=row['sha256'] or p.candidate_bytes!=row['bytes']
                or p.status is None or p.status[0] not in ('exit','signal')
                or g.observation!='observed' or g.other_members!=0):
            raise IncompleteEvidence('helper/candidate binding or group settlement unknown')
        result.append((row,p,g))
    return result


def settlements(log, *, expected, endpoint='server'):
    return [dict(candidate_id=row['candidate_id'],helper_pid=p.pid,wait_status=list(p.status),
                 other_group_members_before_reap=0,settlement_only=True)
            for row,p,_ in census(log,expected,endpoint)]


def audit_success(log, *, expected, owner_pid, endpoint='server', build_id=sdk_audit.BUILD):
    joined=census(log,expected,endpoint);live=parse_live(log)
    if len(live)!=2:raise IncompleteEvidence('exact live-span census required')
    reports=[];spans=[]
    for row,p,_ in joined:
        if p.outcome!='completed' or p.status!=('exit',0) or not p.complete_capture:
            raise IncompleteEvidence('successful full-capture helper required')
        report=sdk_audit.receipt(p.stdout,candidate_sha256=row['sha256'],candidate_bytes=row['bytes'],build_id=build_id)
        selected=[r for r in live if r.pid==p.pid]
        if len(selected)!=1:raise IncompleteEvidence('duplicate or missing live helper record')
        spans.append(bound(selected[0],endpoint=endpoint,owner_pid=owner_pid,helper_pid=p.pid,
                           candidate_sha256=row['sha256'],candidate_bytes=row['bytes']))
        reports.append(dict(candidate_id=row['candidate_id'],helper_pid=p.pid,report=report))
    common=max(0,min(s['last_ns'] for s in spans)-max(s['first_ns'] for s in spans))
    return dict(reports=reports,helper_settlements=settlements(log,expected=expected,endpoint=endpoint),
                overlap_ns=common,overlap_observed=common>0,
                cli_worker_fd_closure_proved=False,pixel_equivalence_proved=False,
                timestamp_producer_authenticated=False,sdk_activity_overlap_proved=False,
                throughput_qualified=False,semantic_eligibility_proved=False)
