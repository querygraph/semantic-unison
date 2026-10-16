#!/usr/bin/env python3
"""Actual two-replica built-in DNG merge, on disposable synthetic containers."""
import argparse,hashlib,importlib.util,json,os,pathlib,struct,tempfile,sys
p=argparse.ArgumentParser();p.add_argument('--unison',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('receive_paths',r/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.ADMISSION_OPTIONS[:]=['-semanticvolumejobs','1']
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-built-in-dng-merge-')).resolve();results=[]
def fixture(rating='1',label='Blue',extra='',opaque=False,delete=False):
 b=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',b,0,b'II',42,8,4)
 packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}" {extra}/></rdf:RDF>').encode();packet=packet.replace(b'xmp:Rating="'+rating.encode()+b'"',b'') if delete else packet;packet+=b' '*(8192-len(packet))
 for i,e in enumerate([(273,4,1,12288),(279,4,1,len(b)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',b,10+12*i,*e)
 struct.pack_into('<I',b,58,0);b[1024:9216]=packet
 if opaque:b[-1]^=1
 return bytes(b)
base,left,right,target=fixture(),fixture('2'),fixture(label='Gold'),fixture('2','Gold')
opts=('-backupcurrent','Name *.dng','-merge','Name *.dng -> unison:dng-xmp-scalars/0')
def session(name,save=True):
 s=v.Session(w/name,a.unison);(s.left/'image.dng').write_bytes(base)
 s.sync(policy='off',options=opts if save else ())
 assert (s.right/'image.dng').read_bytes()==base
 return s
def run(name,lft,rgt,success,save=True,client='pass',server='pass'):
 s=session(name,save);(s.left/'image.dng').write_bytes(lft);(s.right/'image.dng').write_bytes(rgt)
 s.control('image.dng',client=client,server=server)
 log=s.sync(policy='require',options=opts,success=success)
 if success:
  assert (s.left/'image.dng').read_bytes()==target and (s.right/'image.dng').read_bytes()==target
  assert 'Built-in DNG scalar merge verified' in log
  assert len(s.calls('client'))==1 and len(s.calls('server'))==1
  for endpoint in ['client','server']:v.verify_call(s.calls(endpoint)[0],target,previous=lft if endpoint=='client' else rgt,endpoint=endpoint)
  s.sync(policy='require',options=opts)
  assert len(s.calls('client'))==1 and len(s.calls('server'))==1
 else:
  assert (s.left/'image.dng').read_bytes()==lft and (s.right/'image.dng').read_bytes()==rgt
 results.append(dict(name=name,status='passed',result='converged' if success else 'rejected',logs=[str(x) for x in s.root.glob('run-*.log')]))
 print('PASS',name,flush=True)
 return s
receipt=dict(schema='unison-built-in-dng-merge/1',work=str(w),binary=str(pathlib.Path(a.unison).resolve()),binarySha256=hashlib.sha256(pathlib.Path(a.unison).read_bytes()).hexdigest(),cases=results,cpuBudgetPerEndpoint=2,filesystemJobsPerEndpoint=1,scope='Actual CLI/loopback two-replica merge and synthetic validation drivers; no Adobe/Photo/native rendering.')
try:
 run('disjoint',left,right,True)
 run('swapped',right,left,True)
 run('competing',left,fixture('3'),False)
 run('opaque-payload',left,fixture(label='Gold',opaque=True),False)
 run('unknown-field',left,fixture(label='Gold',extra='xmp:CreatorTool="other"'),False)
 run('missing-base',left,right,False,save=False)
 run('first-receiver-reject',left,right,False,client='error')
 run('deleted-field',left,fixture(label='Gold',delete=True),False)
 s=session('stale-base');(s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(right)
 saved=s.client_state/'backup'/'image.dng';assert saved.read_bytes()==base;saved.write_bytes(fixture('5'))
 s.sync(policy='require',options=opts,success=False)
 assert (s.left/'image.dng').read_bytes()==left and (s.right/'image.dng').read_bytes()==right
 results.append(dict(name='stale-base',status='passed',result='rejected'))
 print('PASS stale-base',flush=True)
 s=session('second-receiver-reject');(s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(right)
 s.control('image.dng',server='error');s.sync(policy='require',options=opts,success=False)
 assert (s.left/'image.dng').read_bytes()==target and (s.right/'image.dng').read_bytes()==right
 assert len(s.calls('client'))==1 and len(s.calls('server'))==1
 s.control('image.dng');log=s.sync(policy='require',options=opts)
 assert 'Built-in DNG scalar merge verified' in log
 assert (s.left/'image.dng').read_bytes()==target and (s.right/'image.dng').read_bytes()==target
 assert len(s.calls('client'))==2 and len(s.calls('server'))==2
 results.append(dict(name='second-receiver-reject',status='passed',firstCommitted=True,retry='fresh merge and both receive gates'))
 print('PASS second-receiver-reject and retry',flush=True)
 s=session('policy-mismatch');(s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(right)
 mismatch=('-backupcurrent','Name *.dng','-merge','Name *.dng -> unison:dng-xmp-scalars/99')
 s.sync(policy='require',options=mismatch,success=False)
 assert (s.left/'image.dng').read_bytes()==left and (s.right/'image.dng').read_bytes()==right
 results.append(dict(name='policy-mismatch',status='passed',result='unimplemented command preserves conflict'))
 print('PASS policy-mismatch',flush=True)
 s=session('policy-disabled');(s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(right)
 s.sync(policy='require',options=('-backupcurrent','Name *.dng'),success=False)
 assert (s.left/'image.dng').read_bytes()==left and (s.right/'image.dng').read_bytes()==right
 results.append(dict(name='policy-disabled',status='passed',result='ordinary conflict preserved'))
 print('PASS policy-disabled',flush=True)
 if sys.platform=='darwin':
  s=session('resource-fork');(s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(right)
  fork=pathlib.Path(str(s.left/'image.dng')+'/..namedfork/rsrc');fork.write_bytes(b'private resource fork control')
  s.sync(policy='require',options=opts+('-rsrc','true'),success=False)
  assert (s.left/'image.dng').read_bytes()==left and (s.right/'image.dng').read_bytes()==right
  assert fork.read_bytes()==b'private resource fork control'
  results.append(dict(name='resource-fork',status='passed',result='unsupported fork preserved'))
  print('PASS resource-fork',flush=True)
 for directory in w.iterdir():
  if directory.is_dir():
   for replica in ['left','right']:
    assert not list((directory/replica).glob('.unison.merge*')),str(directory)
 receipt['status']='passed'
finally:
 receipt.setdefault('status','failed');a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');(w/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
