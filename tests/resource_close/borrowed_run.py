"""Compile candidate bridge against actual Lwt/BorrowedWork/admission functions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',action='append',required=True)
p.add_argument('--report',required=True)
a=p.parse_args()
paths=[ROOT/'src/lwt/lwt.mli',ROOT/'src/lwt/lwt.ml',ROOT/'src/borrowedWork.mli',ROOT/'src/borrowedWork.ml',ROOT/'src/semanticAdmission.ml']
paths+=list(HERE/name for name in ('ownedClose.mli','ownedClose.ml','borrowedClose.mli','borrowedClose.ml','borrowed_fixed.ml','borrowed_run.py'))
sources={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
text=(ROOT/'src/semanticAdmission.ml').read_text()
start=text.index('let finish_borrow r =');end=text.index('let with_lease ',start)
actual=text[start:end]
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
    work=Path(tempfile.mkdtemp(prefix='unison-borrowed-close-'))
    for path in paths:
        if path.name not in ('semanticAdmission.ml','borrowed_run.py'):
            (work/path.name).write_bytes(path.read_bytes())
    # Only the timer dependency is stubbed. No setup-fault polling is claimed.
    (work/'lwt_unix.ml').write_text('let sleep (_:float) = Lwt.wait ()\n')
    (work/'admissionFixture.ml').write_text(prefix+actual)
    calls=[]
    units=['lwt.mli','lwt.ml','lwt_unix.ml','borrowedWork.mli','borrowedWork.ml',
           'ownedClose.mli','ownedClose.ml','borrowedClose.mli','borrowedClose.ml','admissionFixture.ml']
    commands=[[compiler,'-c',unit] for unit in units]
    commands+=[[compiler,'lwt.cmx','lwt_unix.cmx','borrowedWork.cmx','ownedClose.cmx',
               'borrowedClose.cmx','admissionFixture.cmx','borrowed_fixed.ml','-o','fixed'],[str(work/'fixed')]]
    for argv in commands:
        completed=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=10)
        calls.append(dict(argv=argv,returncode=completed.returncode,stdout=completed.stdout,stderr=completed.stderr))
        if completed.returncode:raise RuntimeError(json.dumps(calls))
    rows.append(dict(compiler=compiler,work=str(work),calls=calls))
with Path(a.report).open('x') as f:
    json.dump(dict(scope='Candidate bridge + exact with_borrow body/real Lwt; fake descriptors and gate, timer stub; not worker/native/RSS qualification',sources=sources,admission_body_sha256=hashlib.sha256(actual.encode()).hexdigest(),compilers=rows),f,indent=2);f.write('\n')
print('PASS actual borrowed admission functions, both compilers')
