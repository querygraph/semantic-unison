"""One prepared two-candidate receiving case; injected owned transport only."""
import copy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/camera_sdk_concurrency')]
from invocation import artifact_sha
from shared_cpu_pool import UnresolvedOwnership
from combined import sdk_audit,settlements
from sdk_multifile.receipts import audit,BUILD


def execute(directory,*,sources,invoke,persist):
    d=Path(directory)
    names=['uncompressed.dng','jpeg.dng']
    if not d.is_absolute() or d.is_symlink() or not d.is_dir():raise ValueError('prepared private namespace required')
    if type(sources) is not list or len(sources)!=2 or [s.get('candidate_id') for s in sources]!=names:
        raise ValueError('exact two generated-input candidate names required')
    for side in ['left','right']:
        if (d/side).is_symlink() or not (d/side).is_dir():raise ValueError('prepared regular receiving roots required')
    if sorted(p.name for p in (d/'left').iterdir())!=sorted(names) or any((d/'right').iterdir()):
        raise ValueError('exact prepared inputs and unused destination required')
    result=dict(schema='unison-sdk-multifile-case/1',complete=False,phase='PREPARING_NO_CALL',sources=copy.deepcopy(sources),
                semantic_eligibility_claimed=False,pixel_equivalence_claimed=False)
    def save():persist(copy.deepcopy(result))
    def unknown(message,error=None):
        e=UnresolvedOwnership(message);e.result=copy.deepcopy(result)
        raise e from error
    save()
    try:
        for source in sources:
            if type(source.get('bytes')) is not int or not 0<source['bytes']<=128*1048576:
                raise ValueError('bounded generated-input size required')
            path=d/'left'/source['candidate_id']
            if path.lstat().st_size!=source['bytes'] or artifact_sha(path)!=source['sha256']:
                raise ValueError('prepared input differs from pinned candidate')
        result['phase']='CALL_MAY_HAVE_STARTED';save()
        invoke_error=None
        try:outcome=invoke()
        except UnresolvedOwnership:raise
        except BaseException as error:
            if not hasattr(error,'outcome'):unknown('possible receiving call without outcome',error)
            outcome=error.outcome;invoke_error=error
        result['outcome']=outcome
        try:save()
        except BaseException as error:unknown('returned receiving outcome persistence failed',error)
        log=outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
        expected=[]
        try:
            processes=sdk_audit.records.parse(log)
            for source in sources:
                matches=[p for p in processes if p.candidate_sha256==source['sha256'] and p.candidate_bytes==source['bytes']]
                if len(matches)!=1 or matches[0].pid is None:raise ValueError('helper census differs')
                expected.append(dict(source,helper_pid=matches[0].pid))
            result['helper_settlements']=settlements(log,expected=expected)
        except BaseException as error:unknown('two-candidate helper settlement unresolved',error)
        result['phase']='HELPER_SETTLEMENT_RECORDED';save()
        if invoke_error is not None:raise invoke_error
        if outcome['returncode']!=0 or outcome['timed_out'] or outcome['capture_truncated'] or outcome['supervisor_capture_truncated']:
            raise ValueError('receiving CLI failed')
        result['validation']=audit(log,expected=expected,owner_pid=outcome['proxy']['server_pid'],build_id=BUILD)
        for source in sources:
            for side in ['left','right']:
                path=d/side/source['candidate_id']
                if path.lstat().st_size!=source['bytes'] or artifact_sha(path)!=source['sha256']:
                    raise ValueError('source/received candidate bytes differ')
        result.update(complete=True,phase='VERIFIED_TWO_GENERATED_CANDIDATES');save()
        return result
    except UnresolvedOwnership:raise
    except BaseException as error:
        result.update(complete=False,failure=repr(error))
        try:save()
        except BaseException as persist_error:unknown('failed receiving result persistence unknown',persist_error)
        raise
