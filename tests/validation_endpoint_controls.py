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


def main():
    root=Path(tempfile.mkdtemp(prefix='unison-validation-endpoint-',dir='/private/tmp'));calls=[];artifacts={};source_pins={}
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
        shutil.copyfile(ROOT/'tests/validation_endpoint.ml',work/'scan.ml')
        flags=[word for p in (src,src/'ubase',src/'system',src/'system/generic',src/'lwt',src/'lwt/generic') for word in ('-I',str(p))]
        command=[compiler,*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa',*[str(src/m) for m in modules],
                 'scan.ml',*[str(src/n) for n in native],'-o','scan-test']
        previous=Path.cwd()
        try:
            os.chdir(work)
            for argv in (command,[str(work/'scan-test')]):
                outcome=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1',UNISON=str(work/'state')),time.monotonic()+60)
                calls.append(dict(label=label,outcome=outcome));save(root/('CALL-'+str(len(calls))+'.json'),calls[-1])
                proof=outcome['client_cleanup'];assert proof['reaped'] and proof['other_group_members_absent_before_reap']
                assert outcome['returncode']==0 and not outcome['capture_truncated']
        finally:os.chdir(previous)
    for p in (ROOT/'tests/validation_endpoint.ml',Path(__file__).resolve()):source_pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    result=dict(calls=calls,source_pins=source_pins,linked_artifact_sha256=artifacts,workspace=str(root),
                SDK_invoked=False,photo_payload_opened=False,scan_scope_enabled=False,
                scope='Current production scanner objects/generated private roots. Internal coverage and serial isolated endpoint composition exercised; fake in-process validators only. No helper/Adobe/SDK or user-facing scope enabled.')
    save(root/'RESULT.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
