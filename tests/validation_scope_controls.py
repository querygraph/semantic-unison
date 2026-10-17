"""Current-object real scanner and private endpoint composition over generated roots."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from shared_process_owner import retain_after_record
from shared_cpu_pool import UnresolvedOwnership
from private_maker_execute import save
from mixed_validation.execute import document
from dataclasses import asdict
sys.path.insert(0,str(ROOT/'tests/validation_process'))
import records


def main():
    root=Path(tempfile.mkdtemp(prefix='unison-validation-scope-',dir='/private/tmp'));calls=[];artifacts={};source_pins={}
    for label in ('stock','ox'):
        report=document('/private/tmp/unison-validation-scope-'+label+'-006-20261017/RESULT.json')
        assert report['complete'] and report['build_exit']==0
        src=Path(report['workspace'])/'src';compiler=report['compiler']
        assert hashlib.sha256(Path(compiler).read_bytes()).hexdigest()==report['compiler_sha256']
        make=(src/'Makefile.OCaml').read_text()
        def objects(name):
            match=re.search('^'+name+r' = (.*?)(?=\n\n)',make,re.M|re.S);assert match
            return match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
        modules=objects('OCAMLOBJS');modules=modules[:modules.index('uicommon.cmx')+1]
        for row in modules:
            for suffix in ('.ml','.mli'):
                path=Path(row).with_suffix(suffix)
                original=ROOT/'src'/path
                if not (src/path).exists():
                    assert suffix=='.mli';continue  # Modules without an explicit interface.
                actual=(src/path).read_bytes()
                if path.as_posix()!='ubase/projectInfo.ml':assert original.read_bytes()==actual,path
                source_pins[str(src/path)]=hashlib.sha256(actual).hexdigest()
            for suffix in ('.cmi','.cmx','.o'):
                artifact=(src/row).with_suffix(suffix);artifacts[str(artifact)]=hashlib.sha256(artifact.read_bytes()).hexdigest()
        native=objects('COBJS')
        for name in native:artifacts[str(src/name)]=hashlib.sha256((src/name).read_bytes()).hexdigest()
        work=root/label;work.mkdir(mode=0o700);(work/'state').mkdir(mode=0o700)
        shutil.copyfile(ROOT/'tests/validation_scope.ml',work/'scan.ml')
        shutil.copyfile(ROOT/'tests/validation_warning/helper.ml',work/'helper.ml')
        flags=[word for p in (src,src/'ubase',src/'system',src/'system/generic',src/'lwt',src/'lwt/generic') for word in ('-I',str(p))]
        command=[compiler,*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa',*[str(src/m) for m in modules],
                 'scan.ml',*[str(src/n) for n in native],'-o','scan-test']
        previous=Path.cwd()
        try:
            os.chdir(work)
            helper_command=[compiler,'-I','+unix','-I',str(src),'unix.cmxa',str(src/'semanticHash.cmx'),'helper.ml',str(src/'semanticHash_stubs.o'),'-o','helper']
            for argv in (helper_command,command,[str(work/'scan-test'),str(work/'helper')]):
                outcome=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1',UNISON=str(work/'state')),time.monotonic()+60)
                calls.append(dict(label=label,outcome=outcome));save(root/('CALL-'+str(len(calls))+'.json'),calls[-1])
                proof=outcome['client_cleanup'];assert proof['reaped'] and proof['other_group_members_absent_before_reap']
                assert outcome['returncode']==0 and not outcome['capture_truncated']
            log=outcome['stdout']+'\n'+outcome['stderr']
            processes=records.parse(log);groups=records.parse_groups(log)
            helper_rows=(work/'helper.calls').read_text().splitlines()
            pids={int(row.split('\t')[0]) for row in helper_rows}
            expected=hashlib.sha256(b'TOY0 claimed DNG').hexdigest()
            assert len(helper_rows)==len(pids)==len(processes)==len(groups)==2
            for process in processes:
                assert process.pid in pids and process.status==('exit',0) and process.outcome=='completed' and process.complete_capture
                assert process.candidate_sha256==expected and process.candidate_bytes==len(b'TOY0 claimed DNG')
                assert b'raw-digest missing\n' in process.stdout and b'errors 0\n' in process.stdout
                assert any(g.pid==process.pid and g.candidate_sha256==expected and g.other_members==0 for g in groups)
            artifacts[str(work/'helper')]=hashlib.sha256((work/'helper').read_bytes()).hexdigest()
        finally:os.chdir(previous)
    for p in (ROOT/'tests/validation_scope.ml',ROOT/'tests/validation_warning/helper.ml',ROOT/'tests/validation_process/records.py',Path(__file__).resolve()):source_pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    result=dict(calls=calls,source_pins=source_pins,linked_artifact_sha256=artifacts,workspace=str(root),
                SDK_invoked=False,photo_payload_opened=False,scan_scope_enabled=True,
                scope='Current production scanner objects/generated private roots. Actual scan RPC scope enabled; generated data/in-process original fake validators and unavailable-driver policy only. Four actual original fake-driver helpers total, with independent candidate SHA checks and raw process/group receipt binding. No SDK/Photo payload or real Adobe acceptance.')
    save(root/'RESULT.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
