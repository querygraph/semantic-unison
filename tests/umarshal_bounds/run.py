"""Fixed Umarshal reader bounds, legacy wire parity and guarded allocation counterexample."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',required=True);p.add_argument('--report',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];work=Path(tempfile.mkdtemp(prefix='unison-umarshal-bounds-'));work.chmod(0o700);calls=[]
def call(argv,expected=0):
 c=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr))
 assert c.returncode==expected,(c.returncode,c.stdout,c.stderr)
 return c
for name,src in [('umarshal.ml','src/ubase/umarshal.ml'),('umarshal.mli','src/ubase/umarshal.mli'),('bytearray_stubs.c','src/bytearray_stubs.c'),('probe.ml','tests/umarshal_bounds/probe.ml')]:shutil.copyfile(root/src,work/name)
current=(work/'umarshal.ml').read_text()
for old in ['let buffer = Bytes.create length in','let res = Bigarray.(Array1.create char c_layout length) in','let res = Bigarray.(Array1.create int32 c_layout length) in']:
 assert current.count(old)==1
 current=current.replace(old,'if length>65536 then failwith "DESIGNATED current oversized allocation reached";\n        '+old)
(work/'umarshal.ml').write_text(current)
reference=subprocess.run(['git','show','dcaa1e08:src/ubase/umarshal.ml'],cwd=root,capture_output=True,text=True,check=True).stdout
old='let buffer = Bytes.create length in';assert reference.count(old)==1
reference=reference.replace(old,'if length>65536 then failwith "DESIGNATED oversized allocation reached";\n        '+old)
(work/'umarshalReference.ml').write_text(reference)
for source in ['bytearray_stubs.c','umarshal.mli','umarshal.ml','umarshalReference.ml']:call([a.compiler,'-c',source])
call([a.compiler,'umarshal.cmx','umarshalReference.cmx','bytearray_stubs.o','probe.ml','-o','probe'])
c=call([str(work/'probe')]);print(c.stdout,end='')
with Path(a.report).open('x') as f:json.dump(dict(work=str(work),compiler=a.compiler,calls=calls,reference_commit='dcaa1e08',controlled_current_sha256=hashlib.sha256(current.encode()).hexdigest(),controlled_reference_sha256=hashlib.sha256(reference.encode()).hexdigest(),binary_sha256=hashlib.sha256((work/'probe').read_bytes()).hexdigest(),scope='Finite synthetic framed values and poisoned lengths; both current/reference large-allocation sites guarded; current rejection must be typed Error before that guard, while reference reaches it. No unsafe reference offsets or actual large allocations. No camera/SDK/Photo/transport/EXIO/wholeRSS claim.'),f,indent=2)
