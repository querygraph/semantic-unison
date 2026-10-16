"""Caller-admitted two-compiler worker; preparation must settle before return.

No CLI or implicit native admission. prepare_sources must produce clone-only
inputs under owned IO and retain uncertainty rather than orphan child/FD work.
"""
import copy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync'),str(ROOT/'tests/camera_sdk_concurrency')]
from invocation_journal import Journal
from shared_cpu_pool import UnresolvedOwnership
from camera_sdk_concurrency.worker import prepare_scripts
from sdk_multifile.transport import Invoker
from sdk_multifile.case import execute as execute_case
from sdk_multifile.parent import audit


def execute(plan,workspace,deadline,*,prepare_sources,read_proxy,persist,check_sources=lambda:None):
    w=Path(workspace)
    if str(w)!=plan['workspace'] or not w.is_absolute() or w.is_symlink() or not w.is_dir():
        raise ValueError('exact prepared worker namespace required')
    result=dict(schema='unison-sdk-multifile-worker/1',complete=False,phase='PREPARING_NO_CALL',
                cases=[],semantic_eligibility_claimed=False,pixel_equivalence_claimed=False)
    def save():
        if result.get('invocations') and not result['complete']:result['phase']='CALL_MAY_HAVE_STARTED'
        persist(copy.deepcopy(result))
    journal=Journal(result,save);save()
    try:
        for label in ['stock','ox']:
            check_sources()
            directory=w/label;directory.mkdir(mode=0o700)
            for name in ['left','right','state']:(directory/name).mkdir(mode=0o700)
            pins=prepare_scripts(directory,plan['transport_source_sha256'])
            preparation=prepare_sources(directory,label)
            row=dict(label=label,preparation=preparation,case=None);result['cases'].append(row);save()
            call=Invoker(directory,binary=plan['binaries'][label],tool=plan['tool'],
                         journal=journal,script_pins=pins,deadline=deadline)
            def save_case(value):row['case']=value;save()
            row['case']=execute_case(directory,sources=plan['sources'],invoke=call,persist=save_case)
            check_sources();save()
        candidate=dict(result,complete=True,phase='FINISHED')
        proxies=[read_proxy(w/label/'seed-proxy.json') for label in ['stock','ox']]
        proof=audit(candidate,plan,raw_proxy_receipts=proxies)
        result.update(complete=True,phase='FINISHED',parent_audit=proof);save()
        return result
    except UnresolvedOwnership:raise
    except BaseException as error:
        result.update(complete=False,failure=repr(error))
        try:save()
        except BaseException as record_error:
            e=UnresolvedOwnership('worker failure record persistence unknown');e.result=copy.deepcopy(result)
            raise e from record_error
        raise
