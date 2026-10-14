#!/usr/bin/env python3
"""Receive existing SDK-generated originals; mock validators only, no SDK calls."""
import argparse,hashlib,importlib.util,json,pathlib,re,struct,tempfile
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
 if name.startswith('src/'):
  assert sha((root/name).read_bytes())==digest, 'production source changed: '+name
sdk=json.loads(a.sdk_result.read_text());assert sdk['complete'] and sdk['aggregate_lifecycle']['closed']
fixtures=sdk['fixtures']['fixtures']
spec=importlib.util.spec_from_file_location('paths',root/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
work=pathlib.Path(tempfile.mkdtemp(prefix='unison-sdk-container-receive-',dir='/private/tmp'));print('Workspace:',work,flush=True)
def xmp_region(data):
 # Independent restricted TIFF reader for the three known generated controls.
 assert data[:2] in (b'II',b'MM');e='<' if data[:2]==b'II' else '>'
 assert struct.unpack_from(e+'H',data,2)[0]==42
 at=struct.unpack_from(e+'I',data,4)[0];count=struct.unpack_from(e+'H',data,at)[0];assert count<=128
 entries=[struct.unpack_from(e+'HHII',data,at+2+12*i) for i in range(count)]
 records=[entry for entry in entries if entry[0]==700];assert len(records)==1
 _,typ,size,offset=records[0];assert typ==1 and 4<size<=1048576 and offset+size<=len(data)
 return offset,size
cases=[];inputs=[]
for fixture in fixtures:
 source=a.fixtures/fixture['filename'];data=source.read_bytes();before=source.stat()
 assert len(data)==fixture['size_bytes'] and sha(data)==fixture['sha256']
 assert fixture['positive']['receipt']['raw-digest']=='valid'
 offset,size=xmp_region(data);packet=data[offset:offset+size]
 # Same-size valid XML metadata change, preserving every byte outside tag700.
 assert packet.count(b'xmp:MetadataDate="')==1
 at=packet.index(b'xmp:MetadataDate="')+len(b'xmp:MetadataDate="')
 assert packet[at:at+4]==b'2026'
 edited=packet[:at]+b'2027'+packet[at+4:]
 target=data[:offset]+edited+data[offset+size:]
 inputs.append({'path':str(source),'sha256':sha(data),'size':len(data),'xmp_offset':offset,'xmp_size':size})
 for mode in ('semantic','clone-off','protected-change','validation-reject'):
  s=v.Session(work/(fixture['codec']+'-'+mode),str(binary));s.control('image.dng')
  (s.left/'image.dng').write_bytes(data)
  opts=('-semanticdng=true','-clone','off' if mode=='clone-off' else 'auto')
  s.sync(policy='off',options=opts)
  held=s.root/'held-old.dng';held.hardlink_to(s.right/'image.dng')
  changed=target
  if mode=='protected-change':changed=target[:-1]+bytes([target[-1]^1])
  (s.left/'image.dng').write_bytes(changed)
  if mode=='validation-reject':s.control('image.dng',server='error')
  log=s.sync(policy='require',options=opts,success=mode!='validation-reject')
  expected=data if mode=='validation-reject' else changed
  assert (s.right/'image.dng').read_bytes()==expected
  assert held.read_bytes()==data, 'receiver basis/hardlink changed'
  assert (s.left/'image.dng').read_bytes()==changed
  assert len(s.calls('server'))==1
  semantic='Remote semantic clone wrote' in log
  assert semantic==(mode in ('semantic','validation-reject')),log
  payload=None
  if semantic:
   match=re.search(r'Remote semantic clone wrote (\d+) logical metadata bytes in (\d+) write calls \((\d+) payload bytes;',log)
   assert match,log
   logical,writes,payload=map(int,match.groups());assert 0<logical<=size and writes>0 and payload==size
  if mode!='validation-reject':
   identity=(s.right/'image.dng').stat();s.sync(policy='require',options=opts)
   assert (s.right/'image.dng').stat().st_ino==identity.st_ino and len(s.calls('server'))==1
  cases.append({'codec':fixture['codec'],'mode':mode,'semantic':semantic,'metadata_payload_bytes':payload,'target_sha256':sha(expected),'status':'passed'})
  print('PASS',fixture['codec'],mode,flush=True)
 after=source.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert sha(source.read_bytes())==fixture['sha256']
a.report.write_text(json.dumps({'schema':'unison-existing-sdk-container-receive/1','workspace':str(work),'cases':cases,'inputs':inputs,'binary_sha256':build['binary_sha256'],'build_receipt_sha256':sha(a.build_receipt.read_bytes()),'sdk_result_sha256':sha(a.sdk_result.read_bytes()),'runner_sha256':sha(pathlib.Path(__file__).read_bytes()),'scope':'current production CLI/loopback/APFS and mock validation on retained SDK-generated originals; no SDK invocation, no target decode/current SDK receive qualification'},indent=2)+'\n')
