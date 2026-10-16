"""Caller-admitted finite comparison worker; no CLI or implicit SDK grant."""
import copy
import math
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync'),str(ROOT/'tests/camera_sdk_concurrency')]
from invocation_journal import Journal
from shared_cpu_pool import UnresolvedOwnership
from camera_sdk_concurrency.worker import prepare_scripts
from sdk_multifile.case import execute as execute_case
from sdk_throughput.plan import comparison
from sdk_throughput.transport import Invoker
from sdk_throughput.audit import audit


def execute(plan,workspace,deadline,*,prepare_sources,read_proxy,persist,check_sources=lambda:None):
    w=Path(workspace)
    if str(w)!=plan['workspace'] or not w.is_absolute() or w.is_symlink() or not w.is_dir():
        raise ValueError('exact prepared comparison namespace required')
    if type(deadline) not in (int,float) or not math.isfinite(deadline):raise ValueError('finite comparison deadline required')
    scheduled=comparison(plan['binaries'],plan['tool'],w)['rows']
    result=dict(schema='unison-sdk-receiving-comparison-worker/1',complete=False,phase='PREPARING_NO_CALL',cases=[],
                semantic_eligibility_claimed=False,pixel_equivalence_claimed=False,throughput_qualified=False)
    def save():
        if result.get('invocations') and not result['complete']:result['phase']='CALL_MAY_HAVE_STARTED'
        persist(copy.deepcopy(result))
    journal=Journal(result,save);save();rounds=set()
    try:
        for row in scheduled:
            # This stop is before preparation, case publication and invocation
            # intent. Earlier settled calls remain auditable as a failed prefix.
            if time.monotonic()+135>=deadline:raise ValueError('insufficient observation headroom before next comparison row')
            check_sources();directory=Path(row['directory'])
            if row['round'] not in rounds:
                directory.parent.mkdir(mode=0o700);rounds.add(row['round'])
            directory.mkdir(mode=0o700)
            for name in ('left','right','state'):(directory/name).mkdir(mode=0o700)
            pins=prepare_scripts(directory,plan['transport_source_sha256'])
            preparation=prepare_sources(directory,copy.deepcopy(row))
            case_row=dict(schedule=copy.deepcopy(row),preparation=preparation,case=None);result['cases'].append(case_row);save()
            call=Invoker(row,binary=plan['binaries'][row['label']],tool=plan['tool'],journal=journal,script_pins=pins,deadline=deadline)
            def save_case(value):case_row['case']=value;save()
            case_row['case']=execute_case(directory,sources=plan['sources'],invoke=call,persist=save_case)
            check_sources();save()
        candidate=dict(result,complete=True,phase='FINISHED')
        proxies=[read_proxy(Path(row['directory'])/'seed-proxy.json') for row in scheduled]
        proof=audit(candidate,plan,raw_proxy_receipts=proxies)
        result.update(complete=True,phase='FINISHED',parent_audit=proof);save();return result
    except UnresolvedOwnership:raise
    except BaseException as error:
        result.update(complete=False,failure=repr(error))
        try:save()
        except BaseException as record_error:
            e=UnresolvedOwnership('comparison failure record persistence unknown');e.result=copy.deepcopy(result)
            raise e from record_error
        raise
