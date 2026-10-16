"""Prepared two-file case kernel; original bytes/fake validator only, no entry point."""
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership
from invocation import artifact_sha
from combined import audit_success,settlements,sdk_audit,IncompleteEvidence
BUILD='unison-concurrency-synthetic-v1'
FILES={'one.dng':b'original first synthetic candidate\0'*32,
       'two.dng':b'independent second synthetic candidate\0'*32}


def create_file(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        at=0
        while at<len(data):
            count=os.write(fd,data[at:])
            if count<=0:raise OSError('short synthetic fixture write')
            at+=count
    finally:
        close_descriptors([fd])


def execute(directory,*,tool_build_id,invoke,persist):
    d=Path(directory)
    if tool_build_id!=BUILD:raise ValueError('synthetic-only case; no SDK/camera mode')
    if not d.is_absolute() or d.is_symlink() or not d.is_dir():
        raise ValueError('already admitted/prepared private namespace required')
    for name in ('left','right'):
        if (d/name).is_symlink() or not (d/name).is_dir() or any((d/name).iterdir()):
            raise ValueError('unused prepared receiving roots required')
    result={'schema':'unison-two-synthetic-receiving-case/1','complete':False,
            'phase':'PREPARING_NO_CALL','sources':[],'semantic_eligibility_claimed':False,
            'sdk_validation_claimed':False}
    persist(result.copy())
    try:
        for name,data in FILES.items():
            create_file(d/'left'/name,data)
            result['sources'].append(dict(candidate_id=name,sha256=artifact_sha(d/'left'/name),bytes=len(data)))
        result['phase']='CALL_MAY_HAVE_STARTED';persist(result.copy())
        invoke_error=None
        try:outcome=invoke()
        except UnresolvedOwnership:
            raise
        except BaseException as error:
            if not hasattr(error,'outcome'):
                raise UnresolvedOwnership('possible call without returned outcome; retain owner') from error
            outcome=error.outcome;invoke_error=error
        result['outcome']=outcome;persist(result.copy())
        try:
            log=outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
            processes=sdk_audit.records.parse(log)
            expected=[]
            for source in result['sources']:
                matched=[p for p in processes if p.candidate_sha256==source['sha256'] and p.candidate_bytes==source['bytes']]
                if len(matched)!=1 or matched[0].pid is None:
                    raise ValueError('helper identity unresolved')
                expected.append(dict(source,helper_pid=matched[0].pid))
            proof=settlements(log,expected=expected)
        except BaseException as error:
            raise UnresolvedOwnership('synthetic helper/group settlement unresolved') from error
        result['helper_settlements']=proof;persist(result.copy())
        if invoke_error is not None:raise invoke_error
        if (outcome['returncode']!=0 or outcome['timed_out'] or outcome['capture_truncated']
                or outcome['supervisor_capture_truncated'] or outcome['proxy'].get('fault') is not None):
            raise ValueError('two-file receiving call did not succeed completely')
        result['validation']=audit_success(log,expected=expected,
            owner_pid=outcome['proxy']['server_pid'],build_id=BUILD)
        for source in result['sources']:
            if artifact_sha(d/'left'/source['candidate_id'])!=source['sha256'] or artifact_sha(d/'right'/source['candidate_id'])!=source['sha256']:
                raise ValueError('synthetic receiving output/input mismatch')
        result.update(complete=True,phase='VERIFIED_TWO_SYNTHETIC_CANDIDATES')
        persist(result.copy());return result
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result['failure']=repr(error);persist(result.copy());raise
