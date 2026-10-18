"""Original tracked-native-parent component controls, no transport/SDK."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
paths=[ROOT/'src'/name for name in ['stagePublication.ml','stagePublication.mli','stagePublication_stubs.c']]+[ROOT/'tests/stage_publication_owned/fixture.c',HERE/'parent_handoff_test.ml',Path(__file__).resolve()]
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};records=[]
for compiler in a.compiler:
 work=Path(tempfile.mkdtemp(prefix='unison-parent-handoff-'));calls=[]
 for path in paths[:5]:shutil.copyfile(path,work/path.name)
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=20);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 for name in ['stagePublication.mli','stagePublication.ml','fixture.c']:call([compiler,'-I','+unix','-c',name])
 call([compiler,'-I','+unix','unix.cmxa','fixture.o','stagePublication.cmx','parent_handoff_test.ml','-o',str(work/'fixed')])
 for phase in ['normal','ordinary','preentry','after','before','repeat','post-call']:
  case=work/phase;case.mkdir(mode=0o700);call([str(work/'fixed'),phase],cwd=case)
 # The same real native pre-entry branch with a deliberately wrong C mark must
 # fail. Only move the acknowledgement before the strict-uncertain check.
 bad=work/'early-mark';bad.mkdir()
 for path in paths[:5]:shutil.copyfile(path,bad/path.name)
 source=(bad/'stagePublication_stubs.c').read_text()
 marker='  if (tracked) Field(acknowledged, 0) = Val_true;';assert source.count(marker)==1
 source=source.replace(marker,'')
 marker='  if (context->strict_owner && context->uncertain_count != 0) caml_raise(context->ownership_exception);'
 start=source.index('static value adopt_publication(');position=source.index(marker,start)
 source=source[:position]+'  if (tracked) Field(acknowledged, 0) = Val_true;\n'+source[position:]
 (bad/'stagePublication_stubs.c').write_text(source)
 for name in ['stagePublication.mli','stagePublication.ml','fixture.c']:call([compiler,'-I','+unix','-c',name],cwd=bad)
 call([compiler,'-I','+unix','unix.cmxa','fixture.o','stagePublication.cmx','parent_handoff_test.ml','-o',str(bad/'wrong')],cwd=bad)
 case=bad/'case';case.mkdir(mode=0o700);failed=call([str(bad/'wrong'),'preentry'],cwd=case,expected=2)
 assert 'DESIGNATED rejected context falsely acknowledged parent' in failed.stderr
 generic=work/'generic';generic.mkdir()
 for path in paths[:3]:shutil.copyfile(path,generic/path.name)
 portable=(generic/'stagePublication_stubs.c').read_text()
 assert portable.count('#if defined(__APPLE__)')==2
 portable=portable.replace('#if defined(__APPLE__)','#if 0 /* private generic-branch compile control */')
 (generic/'stagePublication_stubs.c').write_text(portable)
 (generic/'probe.ml').write_text('let () = assert(not(StagePublication.available ())); let h=StagePublication.prepare_parent_handoff () in assert(not(StagePublication.parent_consumed h)); let refused=try ignore(StagePublication.prepare_owned ~working_dir:"/" ~stage:"stage" ~temporary:"temp");false with Unix.Unix_error(Unix.ENOSYS,_,_) -> true in assert refused; print_endline "PASS generic branch links tracked symbol and refuses unavailable preparation"\n')
 for name in ['stagePublication.mli','stagePublication.ml','stagePublication_stubs.c']:call([compiler,'-I','+unix','-c',name],cwd=generic)
 call([compiler,'-I','+unix','unix.cmxa','stagePublication_stubs.o','stagePublication.cmx','probe.ml','-o',str(generic/'probe')],cwd=generic)
 call([str(generic/'probe')],cwd=generic)
 records.append(dict(compiler=compiler,work=str(work),calls=calls,wrong_source_sha256=hashlib.sha256(source.encode()).hexdigest()))
assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with Path(a.report).open('x') as f:json.dump(dict(scope='Tracked parent API component only; actual native prepare/adopt/failure/publication and original close interposition; not SemanticRemote integration or observer/whole-resource qualification',sources=pins,records=records),f,indent=2)
print('PASS tracked native parent component and early-mark negative stock/Ox')
