"""Actual compiler-matched Runtime pool descriptor baseline; no semantic IO jobs."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-receipt',required=True);p.add_argument('--report',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];r=json.loads(Path(a.build_receipt).read_text());build=Path(r['workspace'])/'src'
assert r['complete'] and r['build_exit']==r['selftest_exit']==0
for name,digest in r['source_sha256'].items():
 if name.startswith('src/'):assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
text=(build/'Makefile.OCaml').read_text()
def objects(name):
 body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
 return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRuntime.cmx')+1];native=objects('COBJS')
work=Path(tempfile.mkdtemp(prefix='unison-pool-baseline-'));work.chmod(0o700);(work/'state').mkdir(mode=0o700);calls=[]
flags=[v for d in [build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for v in ['-I',str(d)]]+['-I','+unix','-I','+str']
def call(argv):
 c=subprocess.run(argv,cwd=work,env=dict(os.environ,UNISON=str(work/'state')),capture_output=True,text=True,timeout=30)
 calls.append(dict(argv=argv,exit=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,(c.returncode,c.stdout,c.stderr)
 return c
for name in ['baseline.ml','census.c']:shutil.copyfile(root/'tests/resource_lifetime'/name,work/name)
call([r['compiler'],*flags,'-c','census.c'])
call([r['compiler'],*flags,'unix.cmxa','str.cmxa']+[str(build/o) for o in modules+native]+['census.o','baseline.ml','-o','probe'])
for workers in [1,2,4]:
 c=call([str(work/'probe'),str(workers)]);print(c.stdout,end='',flush=True)
c=call([str(work/'probe'),'1','overflow']);print(c.stdout,end='',flush=True)
# Exact production Runtime minus only its baseline debit must fail before pool entry.
private=work/'negative';private.mkdir()
source=(build/'semanticRuntime.ml').read_text();old='let baseline=SemanticWorkers.fixed_resources in';assert source.count(old)==1
(private/'semanticRuntime.ml').write_text(source.replace(old,'let baseline : SemanticAdmission.cost = {payload_bytes=0;descriptors=0} in'))
shutil.copyfile(build/'semanticRuntime.cmi',private/'semanticRuntime.cmi')
shutil.copyfile(build/'semanticRuntime.mli',private/'semanticRuntime.mli')
call([r['compiler'],'-I',str(private),*flags,'-c',str(private/'semanticRuntime.ml')])
negative_modules=[str(private/'semanticRuntime.cmx') if o=='semanticRuntime.cmx' else str(build/o) for o in modules]
call([r['compiler'],'-I',str(private),*flags,'unix.cmxa','str.cmxa']+negative_modules+[str(build/o) for o in native]+['census.o','baseline.ml','-o','negative-probe'])
c=subprocess.run([str(work/'negative-probe'),'1'],cwd=work,env=dict(os.environ,UNISON=str(work/'state')),capture_output=True,text=True,timeout=30)
calls.append(dict(argv=[str(work/'negative-probe'),'1'],exit=c.returncode,stdout=c.stdout,stderr=c.stderr))
assert c.returncode==2 and 'DESIGNATED Runtime infrastructure not reserved' in c.stderr
with Path(a.report).open('x') as f:json.dump(dict(work=str(work),compiler=r['compiler'],calls=calls,scope='Native /dev/fd census excluding own enumeration descriptor, actual Runtime preflight/source+consumer minimum-budget progress/pool start/known shutdown and overflow refusal, plus designated omitted-baseline rejection; no semantic jobs/helpers/SDK/Photo/EXIO or peak/hard-cap claim.'),f,indent=2)
