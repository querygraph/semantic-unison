"""Original accounted-decoder controls and designated callback-omission participant."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',required=True);p.add_argument('--report',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];work=Path(tempfile.mkdtemp(prefix='unison-umarshal-accounting-'));work.chmod(0o700);calls=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def call(argv,cwd=work,expected=0):
 c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30)
 calls.append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr))
 assert c.returncode==expected,(c.returncode,c.stdout,c.stderr)
 return c
files={'umarshal.ml':root/'src/ubase/umarshal.ml','umarshal.mli':root/'src/ubase/umarshal.mli','bytearray_stubs.c':root/'src/bytearray_stubs.c','probe.ml':Path(__file__).with_name('probe.ml'),'allocation_witness.ml':Path(__file__).with_name('allocation_witness.ml')}
record=dict(status='failed',scope='Selected preallocation callback and local bounds on original tiny values. Caller owns partial/success charges; no automatic release/RSS/liveness/RPC integration/SDK/Photo/transport/EXIO.',workspace=str(work),compiler=str(Path(a.compiler).resolve()),compiler_sha256=sha(Path(a.compiler)),source_pins={str(x.relative_to(root)):sha(x) for x in [*files.values(),Path(__file__)]},calls=calls)
try:
 for name,path in files.items():shutil.copyfile(path,work/name)
 original=(work/'umarshal.ml').read_text()
 def guarded(source):
  for anchor in ['let buffer = Bytes.create length in','let res = Bigarray.(Array1.create char c_layout length) in']:
   assert source.count(anchor)==1
   source=source.replace(anchor,'Allocation_witness.before_payload length;\n        '+anchor,1)
  return source
 (work/'umarshal.ml').write_text(guarded(original))
 for name in ['allocation_witness.ml','bytearray_stubs.c','umarshal.mli','umarshal.ml']:call([a.compiler,'-c',name])
 call([a.compiler,'allocation_witness.cmx','umarshal.cmx','bytearray_stubs.o','probe.ml','-o','probe'])
 positive=call([str(work/'probe')]);print(positive.stdout,end='')
 mutations=[('negative','(match input.reserve with None->() | Some reserve->reserve ~bytes ~elements);','(match input.reserve with None->() | Some _->());','DESIGNATED external decode reservation missing'),
            ('ordering-negative','preflight recv length;claim_scaled recv length 2 0;\n        let buffer = Bytes.create length in','preflight recv length;\n        let buffer = Bytes.create length in\n        claim_scaled recv length 2 0;','DESIGNATED payload allocation preceded owner reservation')]
 record['negative_participants']={}
 for label,needle,replacement,witness in mutations:
  assert original.count(needle)==1
  private=work/label;private.mkdir(mode=0o700)
  for name in ['umarshal.mli','probe.ml','allocation_witness.ml','bytearray_stubs.o']:shutil.copyfile(work/name,private/name)
  (private/'umarshal.ml').write_text(guarded(original.replace(needle,replacement)))
  for command in [[a.compiler,'-c','allocation_witness.ml'],[a.compiler,'-c','umarshal.mli'],[a.compiler,'-c','umarshal.ml'],[a.compiler,'allocation_witness.cmx','umarshal.cmx','bytearray_stubs.o','probe.ml','-o',label]]:call(command,cwd=private)
  bad=call([str(private/label)],cwd=private,expected=2);assert witness in bad.stderr
  record['negative_participants'][label]={'source_sha256':sha(private/'umarshal.ml'),'binary_sha256':sha(private/label),'exit_code':bad.returncode,'witness':witness}
 record['controlled_source_sha256']=sha(work/'umarshal.ml')
 record['status']='passed'
finally:
 if (work/'probe').is_file():record['binary_sha256']=sha(work/'probe')
 with Path(a.report).open('x')as f:json.dump(record,f,indent=2);f.write('\n')
