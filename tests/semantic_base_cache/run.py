#!/usr/bin/env python3
"""Actual CLI compact-base merging with original fixtures and mock validators."""
import argparse,hashlib,importlib.util,json,os,pathlib,struct,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--unison',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('paths',root/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.ADMISSION_OPTIONS[:]=['-semanticvolumejobs','1']
work=pathlib.Path(tempfile.mkdtemp(prefix='unison-compact-base-',dir='/private/tmp'));print('Workspace:',work,flush=True)
def fixture(rating='1',label='Blue',opaque=False):
 data=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
 packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"/></rdf:RDF>').encode();packet+=b' '*(8192-len(packet))
 for i,entry in enumerate([(273,4,1,12288),(279,4,1,len(data)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',data,10+12*i,*entry)
 struct.pack_into('<I',data,58,0);data[1024:9216]=packet
 if opaque:data[-1]^=1
 return bytes(data)
base,left,right,target=fixture(),fixture('2'),fixture(label='Gold'),fixture('2','Gold')
options=('-semanticmergebasecache','-merge','Name *.dng -> unison:dng-xmp-scalars/0')
cases=[]
def session(name):
 s=v.Session(work/name,a.unison);(s.left/'image.dng').write_bytes(base)
 s.sync(policy='off',options=options)
 assert (s.right/'image.dng').read_bytes()==base
 records=[f for f in (s.client_state/'semantic-merge-bases-v1').rglob('*') if f.is_file() and len(f.name)==64]
 assert records, 'no common metadata base captured'
 assert all(f.stat().st_size<16384 and f.stat().st_mode&0o777==0o600 for f in records)
 assert not (s.client_state/'backup').exists()
 return s,records
for name in ['converge','missing','damaged','permissive','symlink','stale-other-path','disabled','image-edit','competing','wrong-generation','wrong-policy','second-receiver-fail']:
 s,records=session(name);(s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(right)
 opts=options;success=name in ['converge']
 if name=='missing':
  for f in records:f.unlink()
 if name=='damaged':
  for f in records:
   data=bytearray(f.read_bytes());data[-1]^=1;f.write_bytes(data)
 if name=='permissive':
  for f in records:f.chmod(0o644)
 if name=='symlink':
  for f in records:
   saved=s.root/'original-cache';saved.write_bytes(f.read_bytes());saved.chmod(0o600);f.unlink();f.symlink_to(saved)
 if name=='stale-other-path':
  for f in records:f.rename(f.with_name('f'*64))
 if name=='disabled':opts=('-merge','Name *.dng -> unison:dng-xmp-scalars/0')
 if name=='image-edit':(s.right/'image.dng').write_bytes(fixture(label='Gold',opaque=True))
 if name=='competing':(s.right/'image.dng').write_bytes(fixture('3'))
 if name=='wrong-generation':
  common=fixture('3');(s.left/'image.dng').write_bytes(common);(s.right/'image.dng').write_bytes(common)
  s.sync(policy='off',options=options)
  fresh=[f for f in (s.client_state/'semantic-merge-bases-v1').rglob('*') if f.is_file() and len(f.name)==64 and f not in records]
  assert fresh,'new common generation not captured'
  for f in fresh:f.write_bytes(records[0].read_bytes())
  (s.left/'image.dng').write_bytes(fixture('4'));(s.right/'image.dng').write_bytes(fixture('3','Gold'))
 if name=='wrong-policy':
  for f in records:
   encoded=f.read_bytes();inner=encoded[40:-32]
   changed=inner[:-32].replace(b'org.firstpair.xmp-scalars-three-way/0',b'org.firstpair.xmp-scalars-three-way/9',1)
   changed+=hashlib.sha256(changed).digest();outer=encoded[:40]+changed
   f.write_bytes(outer+hashlib.sha256(outer).digest())
 before_left=(s.left/'image.dng').read_bytes()
 before_right=(s.right/'image.dng').read_bytes()
 if name=='second-receiver-fail':s.control('image.dng',server='error')
 log=s.sync(policy='require',options=opts,success=success)
 if success:
  assert (s.left/'image.dng').read_bytes()==(s.right/'image.dng').read_bytes()==target
  assert len(s.calls('client'))==len(s.calls('server'))==1
 elif name=='second-receiver-fail':
  assert (s.left/'image.dng').read_bytes()==target and (s.right/'image.dng').read_bytes()==right
  s.control('image.dng');s.sync(policy='require',options=options)
  assert (s.left/'image.dng').read_bytes()==(s.right/'image.dng').read_bytes()==target
 else:
  assert (s.left/'image.dng').read_bytes()==before_left and (s.right/'image.dng').read_bytes()==before_right
 cases.append({'case':name,'status':'passed','cache_records':[str(f) for f in records]})
 print('PASS',name,flush=True)
a.receipt.write_text(json.dumps({'workspace':str(work),'cases':cases,'binary_sha256':hashlib.sha256(pathlib.Path(a.unison).read_bytes()).hexdigest(),'scope':'actual CLI/loopback, original DNG-shaped bytes/mock validation only; no SDK'},indent=2)+'\n')
