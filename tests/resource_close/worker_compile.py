"""Typecheck isolated worker successor against pinned compiler-matched objects."""
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler']
 work=Path(tempfile.mkdtemp(prefix='unison-worker-close-typecheck-'))
 for name in ('ownedClose.mli','ownedClose.ml','ownedClose.ox.mli.in','semanticWorkers.mli','semanticWorkers.ml'):(work/name).write_bytes((ROOT/'src'/name).read_bytes())
 (work/'semantic_mode_filter.ml').write_bytes((ROOT/'src/semantic_mode_filter.ml').read_bytes())
 subprocess.run([compiler,'semantic_mode_filter.ml','-o','semantic_mode_filter'],cwd=work,check=True)
 flags=['-I',str(work)]
 for directory in (build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'):flags+=['-I',str(directory)]
 flags+=['-I','+unix']
 version=r.get('compiler_version') or subprocess.check_output([compiler,'-version'],text=True).strip()
 calls=[];success=True
 for name in ('ownedClose.mli','ownedClose.ml','semanticWorkers.mli','semanticWorkers.ml'):
  argv=[compiler,*flags]
  argv+=['-pp',str(work/'semantic_mode_filter')+' '+version]
  argv+=['-c',name]
  result=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=20)
  calls.append(dict(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
  if result.returncode:success=False;break
 records.append(dict(compiler=compiler,build=str(build),work=str(work),success=success,calls=calls))
value=dict(state='ISOLATED_TYPECHECK_ONLY',records=records,all_passed=all(r['success'] for r in records),sources={name:hashlib.sha256((ROOT/'src'/name).read_bytes()).hexdigest() for name in ('ownedClose.mli','ownedClose.ml','ownedClose.ox.mli.in','semantic_mode_filter.ml','semanticWorkers.mli','semanticWorkers.ml')})
with Path(a.report).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps(value))
