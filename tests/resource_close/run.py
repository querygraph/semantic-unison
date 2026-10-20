"""Finite original fake-descriptor compiler controls; no OS close fault injection."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',action='append',required=True)
p.add_argument('--report',required=True)
a=p.parse_args()
result={'scope':'Candidate only, no production worker integration or OS FD/RSS proof','compilers':[]}
for compiler in a.compiler:
    work=Path(tempfile.mkdtemp(prefix='unison-owned-close-'))
    for name in ('ownedClose.mli','ownedClose.ml','fixed.ml'):shutil.copyfile(HERE/name,work/name)
    rows=[]
    for argv in ([compiler,'-c','ownedClose.mli'],[compiler,'-c','ownedClose.ml'],
                 [compiler,'ownedClose.cmx','fixed.ml','-o','fixed'],[str(work/'fixed')]):
        completed=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=10)
        rows.append(dict(argv=argv,returncode=completed.returncode,stdout=completed.stdout,stderr=completed.stderr))
        if completed.returncode:raise RuntimeError(json.dumps(rows))
    result['compilers'].append(dict(path=compiler,sha256=hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),work=str(work),calls=rows))
result['sources']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('ownedClose.mli','ownedClose.ml','fixed.ml','run.py')}
with Path(a.report).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('PASS candidate close-ownership fixed controls both compilers')
