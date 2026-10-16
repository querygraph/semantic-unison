"""Fresh original fake processes through the durable two-probe worker."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from camera_sdk_concurrency.persistence import save
from audit import audit,audit_prefix
from worker import execute


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def epoch(path):
    s=os.lstat(path)
    return [getattr(s,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns',
                                  'st_ctime_ns','st_mode','st_nlink','st_uid')]


def main():
    report=Path(sys.argv[1])
    qualification=ROOT/'tests/qualification/mixed-validation-memory-admission-actual-20261016.json'
    original=json.loads(qualification.read_text())
    rows=[r for r in original['rows'] if r['label'] in ('stock','ox')]
    work=Path(tempfile.mkdtemp(prefix='unison-mixed-journal-process-'))
    pins={str(ROOT/'tests/mixed_validation'/name):sha(ROOT/'tests/mixed_validation'/name)
          for name in ('probe.ml','audit.py','worker.py','journal_controls.py')}
    scenarios=[]
    for mode in ('pass','sdk-error'):
        directory=work/mode;directory.mkdir(mode=0o700)
        commands=[];identities={};helper_ledgers={}
        for index,row in enumerate(rows):
            old=row['report'];oldwork=Path(old['workspace'])
            # Existing private executable is bound to its qualified source and
            # build objects; never select an installed/native SDK executable.
            for source,digest in old['sources'].items():
                if sha(source)!=digest:raise ValueError('qualified fake source changed')
            for obj,digest in old['objects'].items():
                if sha(obj)!=digest:raise ValueError('qualified production object changed')
            labeldir=directory/row['label'];labeldir.mkdir(mode=0o700)
            local=labeldir/(mode if index==0 else 'pass');local.mkdir(mode=0o700)
            fakecase=oldwork/(mode if index==0 else 'pass')
            for name,source in [('probe',oldwork/'probe'),('validator.py',fakecase/'validator.py'),
                                ('metadata.py',fakecase/'metadata.py'),('private.dng',fakecase/'private.dng')]:
                shutil.copyfile(source,local/name)
                if name!='private.dng':(local/name).chmod(0o700)
                if sha(source)!=sha(local/name):raise ValueError('fake preparation copy differs')
                pins[str(local/name)]=sha(local/name)
            candidate=local/'private.dng';identities[index]=epoch(candidate)
            commands.append([str(local/'probe'),str(local/'validator.py'),str(local/'metadata.py'),
                             str(candidate),sha(local/'validator.py'),'synthetic-mixed-v1',sha(candidate),str(candidate.stat().st_size)])
            helper_ledgers[index]=[local/'validator.calls',local/'metadata.calls']

        def sources():
            for name,digest in pins.items():
                if sha(name)!=digest:raise ValueError('pinned source/input/tool changed: '+name)
        def verify(index,command):
            if epoch(command[3])!=identities[index]:raise ValueError('private candidate epoch changed')
        def call(index,command,deadline):
            return invoke(command,dict(os.environ,UNISON=str(Path(command[0]).parent/'state')),
                          min(deadline,time.monotonic()+20))
        failure=None
        try:
            execute(commands,deadline=time.monotonic()+90,headroom=20,
                    metadata_version='synthetic-only',prepare=lambda *a:None,
                    invoke=call,persist=lambda r:save(directory,r),
                    check_sources=sources,verify_input=verify)
        except UnresolvedOwnership:raise
        except ValueError as error:failure=repr(error)
        result=json.loads((directory/'RESULT.json').read_text())
        try:
            proof=audit_prefix(result,commands=commands,metadata_version='synthetic-only',require_admission=True)
            if result['complete']!=(mode=='pass'):raise ValueError('unexpected scenario outcome')
            if proof['attempted_probes']!=(2 if mode=='pass' else 1):raise ValueError('wrong attempted prefix')
            for entry in result['invocations']:
                index=entry['index'];sdk,metadata=helper_ledgers[index]
                audit(entry['outcome'],command=commands[index],metadata_version='synthetic-only',
                      expected_helpers=dict(sdk=int(sdk.read_text()),metadata=int(metadata.read_text())),require_admission=True)
                verify(index,commands[index])
            if mode!='pass' and any(p.exists() for p in helper_ledgers[1]):raise ValueError('successor unexpectedly invoked')
            sources()
        except BaseException as error:
            raise UnresolvedOwnership('actual mixed journal prefix unresolved') from error
        scenarios.append(dict(mode=mode,result=result,audit=proof,failure=failure))
    receipt=dict(scope='Three fresh private fake probes/six fake helpers/48hash tasks; no SDK/ExifTool/Photo/EXIO',
                 workspace=str(work),prerequisite=dict(path=str(qualification),sha256=sha(qualification)),
                 sources=pins,scenarios=scenarios)
    with report.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print('PASS durable fresh fake-process success and failed-first prefix',flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print('MIXED_JOURNAL_RETAINED '+repr(error),flush=True))
