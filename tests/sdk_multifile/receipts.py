"""Independent two-candidate SDK verdict/group join; no process ownership."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/camera_sdk_concurrency'))
from combined import census,settlements,sdk_audit
from live_records import parse,bound

BUILD='unison-sdk171-2724-v1-single'


def audit(log,*,expected,owner_pid,build_id):
    if build_id!=BUILD or type(owner_pid) is not int or not 0<owner_pid<2**31:
        raise ValueError('qualified reference build and actual endpoint owner required')
    joined=census(log,expected,'server')
    if len({r['sha256'] for r,_,_ in joined})!=2:
        raise ValueError('two distinct generated input identities required')
    reports=[]
    for row,p,_ in joined:
        if p.outcome!='completed' or p.status!=('exit',0) or not p.complete_capture:
            raise ValueError('both SDK helpers must complete with full captures')
        report=sdk_audit.receipt(p.stdout,candidate_sha256=row['sha256'],candidate_bytes=row['bytes'],build_id=build_id)
        if report['raw_digest_verified'] is not True:
            raise ValueError('generated inputs require actual valid raw digest')
        reports.append(dict(candidate_id=row['candidate_id'],helper_pid=p.pid,report=report))
    records=parse(log);spans=[]
    if len(records)>2:raise ValueError('extra live helper records')
    for row,p,_ in joined:
        matches=[r for r in records if r.pid==p.pid]
        if len(matches)>1:raise ValueError('duplicate live helper record')
        if not matches:continue
        r=matches[0]
        if (r.endpoint,r.owner_pid,r.candidate_sha256,r.candidate_bytes)!=('server',owner_pid,row['sha256'],row['bytes']):
            raise ValueError('live diagnostic differs from independently joined helper')
        if not r.valid or r.samples<2:continue
        try:spans.append(bound(r,endpoint='server',owner_pid=owner_pid,helper_pid=p.pid,
                              candidate_sha256=row['sha256'],candidate_bytes=row['bytes']))
        except ValueError:
            # Insufficient conservative clock width is missing timing evidence,
            # never a substitute for the mandatory process/group settlement.
            continue
    if any(r.pid not in {p.pid for _,p,_ in joined} for r in records):
        raise ValueError('unbound live helper diagnostic')
    overlap=None if len(spans)!=2 else max(0,min(s['last_ns'] for s in spans)-max(s['first_ns'] for s in spans))
    return dict(reports=reports,helper_settlements=settlements(log,expected=expected),
                known_live_overlap_ns=overlap,known_live_overlap_observed=None if overlap is None else overlap>0,
                timing_coverage_complete=len(spans)==2,raw_digests_verified=True,
                cli_worker_fd_closure_proved=False,process_record_producer_authenticated=False,
                sdk_compute_overlap_proved=False,semantic_eligibility_proved=False,
                pixel_equivalence_proved=False,throughput_qualified=False)
