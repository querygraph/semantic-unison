"""Fixed owner guard controls against actual Lwt and extracted admission bodies."""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',action='append',required=True)
p.add_argument('--report',required=True)
a=p.parse_args()
paths=[ROOT/'src'/x for x in ['lwt/lwt.mli','lwt/lwt.ml','borrowedWork.mli','borrowedWork.ml','retainedOwnership.mli','retainedOwnership.ml','semanticAdmission.ml']]+[HERE/'retained_fixed.ml',Path(__file__).resolve()]
pins={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
s=(ROOT/'src/semanticAdmission.ml').read_text()
body=s[s.index('let finish_borrow r ='):s.index('let with_lease ')]
prefix='''open Lwt
exception Failed of string
type cost={payload_bytes:int;descriptors:int}
type state=Held|Retiring|Retired
type gate={mutable releases:int}
type reservation={gate:gate;cost:cost;mutable state:state;mutable borrowing:bool}
let release gate _ = gate.releases <- gate.releases + 1
let retire_requested r = r.state <- Retiring
'''
rows=[]
for compiler in a.compiler:
    work=Path(tempfile.mkdtemp(prefix='unison-retained-guard-'))
    for path in paths:
        if path.suffix in ('.ml','.mli') and path.name!='semanticAdmission.ml':
            (work/path.name).write_bytes(path.read_bytes())
    lwt=(work/'lwt.ml').read_text()
    needle='let add_waiter t f = t.waiters <- f :: t.waiters'
    assert lwt.count(needle)==1
    (work/'lwt.ml').write_text(lwt.replace(needle,'let add_waiter t f = ScopeFault.before_waiter (); t.waiters <- f :: t.waiters'))
    (work/'scopeFault.ml').write_text('exception Observer\nlet armed=ref false\nlet before_waiter () = if !armed then (armed:=false;raise Observer)\n')
    (work/'lwt_unix.ml').write_text('let sleep (_:float) = Lwt.wait ()\n')
    (work/'admissionFixture.ml').write_text(prefix+body)
    units=['scopeFault.ml','lwt.mli','lwt.ml','lwt_unix.ml','borrowedWork.mli','borrowedWork.ml','retainedOwnership.mli','retainedOwnership.ml','admissionFixture.ml']
    commands=[[compiler,'-c',x] for x in units]
    commands.append([compiler,'scopeFault.cmx','lwt.cmx','lwt_unix.cmx','borrowedWork.cmx','retainedOwnership.cmx','admissionFixture.cmx','retained_fixed.ml','-o','fixed'])
    commands.extend([[str(work/'fixed'),case] for case in ['success','ordinary','sync','async','observer','classifier','callback']])
    calls=[]
    for argv in commands:
        c=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=15)
        calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
        if c.returncode: raise RuntimeError(json.dumps(calls))
    rows.append(dict(compiler=compiler,work=str(work),calls=calls))
assert pins=={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
with Path(a.report).open('x') as f:
    json.dump(dict(scope='Actual guard/Lwt/BorrowedWork/extracted admission bodies; injected one waiter-install error, fake reservation gate, timer stub; not complete Runtime/pool/FD/RSS qualification',sources=pins,compilers=rows),f,indent=2)
print('PASS seven fixed guard scenarios per compiler')
