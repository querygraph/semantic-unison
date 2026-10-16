"""Link current Make objects and run finite two-worker generated snapshot cases."""
import ast
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
from shared_process_owner import retain_after_record
from shared_cpu_pool import UnresolvedOwnership
from private_maker_execute import save
from mixed_validation.execute import document


def main():
    # Reuse the existing component's explicit source order, without executing it.
    tree=ast.parse((ROOT/'tests/workers/run.py').read_text())
    rows=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='sources' for t in n.targets))[:-1]
    index=rows.index('src/semanticWorkers.mli')
    rows[index:index]=['src/wholeFileClone_stubs.c','src/wholeFileClone.mli','src/wholeFileClone.ml',
                       'src/validationSnapshot.mli','src/validationSnapshot.ml']
    rows += ['src/fileObservation_stubs.c','src/fileObservation.mli','src/fileObservation.ml','src/validationStage.mli','src/validationStage.ml','src/validationStageWork.mli','src/validationStageWork.ml']
    root=Path(tempfile.mkdtemp(prefix='unison-stage-work-',dir='/private/tmp'));calls=[];artifacts={}
    for label in ('stock','ox'):
        report=document('/private/tmp/unison-snapshot-worker-'+label+'-select-005-20261017/RESULT.json')
        assert report['complete'] and report['build_exit']==0
        compiler=report['compiler'];assert hashlib.sha256(Path(compiler).read_bytes()).hexdigest()==report['compiler_sha256']
        work=root/label;work.mkdir(mode=0o700);actual=Path(report['workspace'])/'src';objects=[]
        for name in rows:
            source=ROOT/name;compiled=actual/name.removeprefix('src/')
            assert source.read_bytes()==compiled.read_bytes(),name
            extensions=['.cmi','.cmx','.o'] if source.suffix=='.ml' else ['.cmi'] if source.suffix=='.mli' else ['.o']
            for extension in extensions:
                artifact=compiled.with_suffix(extension);raw=artifact.read_bytes()
                artifacts[str(artifact)]=hashlib.sha256(raw).hexdigest()
                shutil.copyfile(artifact,work/artifact.name)
            if source.suffix in ('.ml','.c'):objects.append(compiled.stem+('.cmx' if source.suffix=='.ml' else '.o'))
        shutil.copyfile(ROOT/'tests/workers/stage_work.ml',work/'stage_work.ml')
        commands=[[compiler,'-I','+unix','unix.cmxa',*objects,'stage_work.ml','-o','stage-work-test'],[str(work/'stage-work-test')]]
        previous=Path.cwd()
        try:
            os.chdir(work)
            for command in commands:
                outcome=invoke(command,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+60)
                calls.append(dict(label=label,outcome=outcome));save(root/('CALL-'+str(len(calls))+'.json'),calls[-1])
                proof=outcome['client_cleanup'];assert proof['reaped'] and proof['other_group_members_absent_before_reap']
                assert outcome['returncode']==0 and not outcome['capture_truncated']
        finally:os.chdir(previous)
    result=dict(calls=calls,linked_artifact_sha256=artifacts,workspace=str(root),SDK_invoked=False,
        source_pins={str(ROOT/p):hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
            for p in rows+['tests/workers/run.py','tests/workers/stage_work.ml',str(Path(__file__).resolve().relative_to(ROOT))]},
        scope='Current production Make objects; actual snapshot workers plus asynchronous private-stage validation doubles. Cleanup uncertainty is injected EBADF; symbolic admission deliberately remains held until test-process exit. No SDK/photos/scan integration.')
    save(root/'RESULT.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
