#!/usr/bin/env python3
"""Compact-base merge of retained SDK-generated containers, mock validation only."""
import argparse,hashlib,importlib.util,json,pathlib,struct,tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt',type=pathlib.Path,required=True)
p.add_argument('--sdk-result',type=pathlib.Path,required=True)
p.add_argument('--fixtures',type=pathlib.Path,required=True)
p.add_argument('--report',type=pathlib.Path,required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
build=json.loads(a.build_receipt.read_text());binary=pathlib.Path(build['binary'])
assert sha(binary.read_bytes())==build['binary_sha256']
for name,digest in build['source_sha256'].items():
 if name.startswith('src/'):assert sha((root/name).read_bytes())==digest,name
sdk=json.loads(a.sdk_result.read_text());assert sdk['complete'] and sdk['aggregate_lifecycle']['closed']
spec=importlib.util.spec_from_file_location('paths',root/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.ADMISSION_OPTIONS[:]=['-semanticvolumejobs','1']
work=pathlib.Path(tempfile.mkdtemp(prefix='unison-sdk-container-merge-',dir='/private/tmp'));print('Workspace:',work,flush=True)
options=('-semanticmergebasecache','-merge','Name *.dng -> unison:dng-xmp-scalars/0')
cases=[];inputs=[]
for fixture in sdk['fixtures']['fixtures']:
 source=a.fixtures/fixture['filename'];data=source.read_bytes();before=source.stat()
 assert len(data)==fixture['size_bytes'] and sha(data)==fixture['sha256']
 assert fixture['positive']['receipt']['raw-digest']=='valid'
 assert data[:2] in (b'II',b'MM');e='<' if data[:2]==b'II' else '>'
 assert struct.unpack_from(e+'H',data,2)[0]==42
 at=struct.unpack_from(e+'I',data,4)[0];count=struct.unpack_from(e+'H',data,at)[0];assert count<=128
 entries=[struct.unpack_from(e+'HHII',data,at+2+12*i) for i in range(count)]
 records=[entry for entry in entries if entry[0]==700];assert len(records)==1
 _,typ,size,offset=records[0];assert typ==1 and 4<size<=1048576 and offset+size<=len(data)
 original=data[offset:offset+size]
 anchor=b'rdf:about=""';assert original.count(anchor)==1
 extended=original.replace(anchor,anchor+b' xmp:Rating="1" xmp:Label="Blue"',1)
 growth=len(extended)-len(original);end=extended.index(b'</x:xmpmeta>')+len(b'</x:xmpmeta>')
 # Consume only whitespace after the XML root, preserving fixed region geometry.
 padding=extended.index(b' '*growth,end);base_packet=extended[:padding]+extended[padding+growth:]
 assert len(base_packet)==size
 def variant(rating=b'1',label=b'Blue',opaque=False):
  packet=base_packet.replace(b'xmp:Rating="1"',b'xmp:Rating="'+rating+b'"',1).replace(b'xmp:Label="Blue"',b'xmp:Label="'+label+b'"',1)
  assert len(packet)==size
  result=data[:offset]+packet+data[offset+size:]
  if opaque:result=result[:-1]+bytes([result[-1]^1])
  return result
 base,left,right,target=variant(),variant(rating=b'2'),variant(label=b'Gold'),variant(rating=b'2',label=b'Gold')
 inputs.append({'source':str(source),'source_sha256':sha(data),'base_sha256':sha(base),'target_sha256':sha(target),'xmp_offset':offset,'xmp_size':size,'provenance':'original generated container with inserted scalar attributes consuming only XMP padding; changed base/targets not SDK-validated'})
 for mode in ('disjoint','competing','protected-change','missing-base','partial-recovery'):
  s=v.Session(work/(fixture['codec']+'-'+mode),str(binary))
  (s.left/'image.dng').write_bytes(base);s.sync(policy='off',options=options)
  assert (s.right/'image.dng').read_bytes()==base
  records=[f for f in (s.client_state/'semantic-merge-bases-v1').rglob('*') if f.is_file() and len(f.name)==64]
  assert records and not (s.client_state/'backup').exists()
  assert all(f.stat().st_size<16384 and b'org.firstpair.dng-xmp/1' in f.read_bytes() for f in records)
  rhs=variant(rating=b'3') if mode=='competing' else variant(label=b'Gold',opaque=mode=='protected-change')
  (s.left/'image.dng').write_bytes(left);(s.right/'image.dng').write_bytes(rhs)
  if mode=='missing-base':
   for f in records:f.unlink()
  if mode=='partial-recovery':s.control('image.dng',server='error')
  log=s.sync(policy='require',options=options,success=mode=='disjoint')
  if mode=='disjoint':
   assert (s.left/'image.dng').read_bytes()==(s.right/'image.dng').read_bytes()==target
   assert 'Built-in DNG scalar merge verified' in log
   assert len(s.calls('client'))==len(s.calls('server'))==1
  elif mode=='partial-recovery':
   assert (s.left/'image.dng').read_bytes()==target and (s.right/'image.dng').read_bytes()==rhs
   s.control('image.dng');retry=s.sync(policy='require',options=options)
   assert 'Built-in DNG scalar merge verified' in retry
   assert (s.left/'image.dng').read_bytes()==(s.right/'image.dng').read_bytes()==target
   assert len(s.calls('client'))==len(s.calls('server'))==2
  else:
   assert (s.left/'image.dng').read_bytes()==left and (s.right/'image.dng').read_bytes()==rhs
   assert not s.calls('client') and not s.calls('server')
  if mode in ('disjoint','partial-recovery'):
   counts=(len(s.calls('client')),len(s.calls('server')))
   s.sync(policy='require',options=options)
   assert (len(s.calls('client')),len(s.calls('server')))==counts
  cases.append({'codec':fixture['codec'],'mode':mode,'cache_sizes':[f.stat().st_size for f in records if f.exists()],'status':'passed'})
  print('PASS',fixture['codec'],mode,flush=True)
 after=source.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert sha(source.read_bytes())==fixture['sha256']
a.report.write_text(json.dumps({'schema':'unison-sdk-container-compact-merge/1','workspace':str(work),'cases':cases,'inputs':inputs,'binary_sha256':build['binary_sha256'],'build_receipt_sha256':sha(a.build_receipt.read_bytes()),'sdk_result_sha256':sha(a.sdk_result.read_bytes()),'runner_sha256':sha(pathlib.Path(__file__).read_bytes()),'scope':'current production CLI/loopback with compact cache only, generated original codec containers modified solely in fixed XMP regions; mock validators; no SDK/Photo/Adobe calls or changed-output decode qualification'},indent=2)+'\n')
