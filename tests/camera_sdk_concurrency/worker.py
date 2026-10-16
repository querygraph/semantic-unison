"""Two synthetic compiler cases; requires a separately admitted parent, no CLI."""
import copy
import hashlib
import os
import stat
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'bench/sync'))
from invocation_journal import Journal
from invocation import Invoker,SCRIPT_NAMES,FIELDS,close_descriptors
from synthetic_case import execute as execute_case,BUILD,create_file,UnresolvedOwnership
from result_audit import audit
ROOT=Path(__file__).resolve().parents[2]


def prepare_scripts(directory,pins):
    if set(pins)!=set(SCRIPT_NAMES):raise ValueError('exact copied transport pins required')
    for name in SCRIPT_NAMES:
        path=ROOT/'bench/sync'/name
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        try:
            before=os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=1048576:raise ValueError('bounded source script required')
            data=b''
            while len(data)<before.st_size:
                block=os.read(fd,before.st_size-len(data))
                if not block:raise ValueError('short transport source')
                data+=block
            if os.read(fd,1) or any(getattr(before,k)!=getattr(now,k)
                    for now in (os.fstat(fd),os.lstat(path)) for k in FIELDS):
                raise ValueError('transport source epoch changed')
        finally:close_descriptors([fd])
        if hashlib.sha256(data).hexdigest()!=pins[name]:raise ValueError('transport source pin differs')
        target=Path(directory)/name;create_file(target,data)
        if name=='launcher.py':os.chmod(target,0o700)
    return dict(pins)


def execute(plan,workspace,deadline,*,persist):
    workspace=Path(workspace)
    if (plan['workspace']!=str(workspace) or plan['tool']['build_id']!=BUILD
            or set(plan['binaries'])!={'stock','ox'} or workspace.is_symlink() or not workspace.is_dir()):
        raise ValueError('exact admitted synthetic worker scope required')
    result=dict(schema='unison-concurrent-synthetic-worker/1',complete=False,
                phase='PREPARING_NO_CALL',cases=[],sdk_validation_claimed=False,semantic_eligibility_claimed=False)
    def save():
        if result['invocations'] and not result['complete']:result['phase']='CALL_MAY_HAVE_STARTED'
        persist(copy.deepcopy(result))
    journal=Journal(result,save);save()
    try:
        for label in ('stock','ox'):
            directory=workspace/label;directory.mkdir(mode=0o700)
            for name in ('left','right','state'):(directory/name).mkdir(mode=0o700)
            pins=prepare_scripts(directory,plan['transport_source_sha256'])
            row=dict(label=label,case=None);result['cases'].append(row);save()
            invoke=Invoker(directory,binary=plan['binaries'][label],tool=plan['tool'],
                           journal=journal,script_pins=pins,deadline=deadline)
            def save_case(value):row['case']=value;save()
            row['case']=execute_case(directory,tool_build_id=BUILD,invoke=invoke,persist=save_case)
            save()
        candidate=dict(result,complete=True,phase='FINISHED')
        proof=audit(candidate,plan,workspace)
        result.update(complete=True,phase='FINISHED',call_audit=proof);save()
        return result
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result['failure']=repr(error);save();raise
