"""Typecheck current remote owner module against a compiler-matched snapshot."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
r=json.loads(a.receipt.read_text());build=Path(r['workspace'])/'src';work=Path(tempfile.mkdtemp(prefix='unison-remote-owner-typecheck-'))
for name in ['semanticRemote.ml','semanticRemote.mli']:shutil.copyfile(ROOT/'src'/name,work/name)
assert (ROOT/'src/semanticRemote.mli').read_bytes()==(build/'semanticRemote.mli').read_bytes()
shutil.copyfile(build/'semanticRemote.cmi',work/'semanticRemote.cmi')
flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
argv=[r['compiler'],*flags,'-c','semanticRemote.ml'];c=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=30)
with a.report.open('x') as f:json.dump({'scope':'Typecheck only, not full build/runtime qualification','source_sha256':hashlib.sha256((work/'semanticRemote.ml').read_bytes()).hexdigest(),'argv':argv,'returncode':c.returncode,'stdout':c.stdout,'stderr':c.stderr,'work':str(work)},f,indent=2)
print(c.stderr);raise SystemExit(c.returncode)
