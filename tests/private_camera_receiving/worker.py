"""Prepared receiving worker kernel; no CLI, default input or admission grant.

An exact admitted parent must verify plan/source/artifact pins, own IO+CPU and
bind inherited descriptors before invoking this kernel. It must retain unknown
child/FD outcomes and audit this journal before aggregate reap or lease release.
"""
import os
from close import UnresolvedOwnership
from pathlib import Path
import sys

import case
import clone
import transport

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
from invocation_journal import Journal, audit_attempted
from run import save


def execute(plan,workspace,deadline_monotonic):
    workspace=Path(workspace)
    case.require(workspace.is_absolute() and workspace.is_dir() and not workspace.is_symlink(),
                 'admitted existing private workspace required')
    case.require(set(plan['binaries'])=={'stock','ox'},'fixed compiler pair required')
    source=Path(plan['source']['path']);expected=plan['source']['identity']
    result={'schema':'unison-camera-receiving-worker/1','complete':False,
            'phase':'PREPARING_NO_TRANSPORT_DISPATCH','cases':[],
            'camera_validity_claimed':False,'semantic_eligibility_claimed':False}
    output=workspace/'RESULT.json'
    journal=Journal(result,lambda:save(output,result))
    save(output,result)
    borrowed=None
    def check():
        case.require(clone.stamp(os.fstat(borrowed))==expected==clone.stamp(os.lstat(source)),
                     'borrowed source native epoch changed')
    try:
        borrowed=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        check()
        # These are same-compiler cases, deliberately not all four wire pairs.
        for label in ('stock','ox'):
            check()
            directory=workspace/label
            directory.mkdir(mode=0o700)
            for name in ('left','right','state'):(directory/name).mkdir(mode=0o700)
            script_pins=transport.prepare(directory)
            prepared=clone.prepare(source,expected,directory/'left')
            case.require(prepared['backend']=='native-fclonefileat-only',
                         'runtime worker forbids fake or fallback clone backend')
            check()
            record={'label':label,'clone':prepared,'case':None}
            result['cases'].append(record)
            result['phase']='TRANSPORT_MAY_HAVE_STARTED'
            save(output,result) # Irreversible conservative marker before call hook.
            item=plan['binaries'][label]
            invoker=transport.Invoker(directory,item,item,journal,script_pins,deadline_monotonic)
            def save_case(value):
                record['case']=value
                save(output,result)
            record['case']=case.exercise(directory,
                    initial_sha256=plan['source']['historical_sha256'],check_borrowed=check,
                    invoke=invoker,save=save_case,
                    deadline_monotonic=deadline_monotonic)
            save(output,result)
        check()
        proof=audit_attempted(result)
        case.require(proof['attempted_cli_invocations']==6
                     and proof['server_not_created_invocations']==0,'six successful transport calls required')
        case.require(all(row['case']['complete'] for row in result['cases']),
                     'both exact receiving cases required')
        result.update(complete=True,phase='FINISHED',call_lifecycle=proof)
        save(output,result)
        return result
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result['complete']=False
        result['failure']=repr(error)
        save(output,result)
        raise
    finally:
        # An admitted entrypoint must retain an uncertain-close carrier rather
        # than exiting and discarding it. Do not retry the numeric descriptor.
        if borrowed is not None:
            clone.close_descriptors([borrowed])
