#!/usr/bin/env python3
"""Independent normative SDB bytes and finite compatibility controls, no SDK."""
import argparse,hashlib,json,pathlib,shutil,struct,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];work=pathlib.Path(tempfile.mkdtemp(prefix='unison-cache-kernel-',dir='/private/tmp'));print('Workspace:',work,flush=True)
version=subprocess.check_output([a.compiler,'-version'],text=True).strip();mods=['semanticHash','semanticFile','formatExtension','xmpObservation','xmpMerge','dngSemantic','semanticDelta']
for module in mods:
 for suffix in ['.mli','.ml','.ox.mli.in']:shutil.copyfile(root/'src'/(module+suffix),work/(module+suffix))
for name in ['semanticHash_stubs.c','semanticFile_stubs.c','semantic_mode_filter.ml']:shutil.copyfile(root/'src'/name,work/name)
subprocess.run([a.compiler,'semantic_mode_filter.ml','-o','filter'],cwd=work,check=True)
for module in mods:
 for suffix in ['.mli','.ml']:
  path=work/(module+suffix);path.write_bytes(subprocess.check_output([str(work/'filter'),version,str(path)]))
test=(root/'tests/semantic_base_cache/kernel.ml').read_text()
if '+ox' in version:test=test.replace('let () = controls ()','let () = let domain=Domain.Safe.spawn(fun () -> controls ()) in Domain.join domain')
(work/'kernel.ml').write_text(test)
u=lambda value:struct.pack('>Q',value)
sha=lambda value:hashlib.sha256(value).digest()
def fixture(rating,label):
 data=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
 packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"/></rdf:RDF>').encode();packet+=b' '*(8192-len(packet))
 for i,e in enumerate([(273,4,1,12288),(279,4,1,len(data)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',data,10+12*i,*e)
 struct.pack_into('<I',data,58,0);data[1024:9216]=packet
 return bytes(data),packet
for name,args in [('base',(1,'Blue')),('left',(2,'Blue')),('right',(1,'Gold')),('target',(2,'Gold'))]:(work/(name+'.dng')).write_bytes(fixture(*args)[0])
data,packet=fixture(1,'Blue');name=b'org.firstpair.dng-xmp/0';policy=b'org.firstpair.xmp-scalars-three-way/0;parser=1'
preserved=sha(b'SDE/0-preserved\0'+u(len(data))+u(1)+u(1024)+u(8192)+u(0)+u(1024)+data[:1024]+u(9216)+u(len(data)-9216)+data[9216:])
request=b'SDR'+bytes(5)+bytes(32)+u(len(name))+name+u(len(data))+sha(data)+preserved+u(1)+u(1024)+u(8192)+sha(packet)
fields=[];shell=bytearray();at=0
for field,value in [('Rating',b'1'),('Label',b'Blue')]:
 first=packet.index(('xmp:'+field+'="').encode())+len(('xmp:'+field+'="').encode());last=first+len(value)
 shell+=packet[at:first]+b'\0';at=last
 expanded=('{http://ns.adobe.com/xap/1.0/}'+field).encode()
 fields.append(u(len(expanded))+expanded+sha(value)+u(first)+u(last))
shell+=packet[at:];parsed=sha(shell)+u(2)+b''.join(fields)
payload=b'SDB'+bytes(4)+b'\1'+u(len(policy))+policy+u(len(request))+request+u(len(packet))+packet+u(len(parsed))+parsed
valid=payload+sha(payload);(work/'golden.sdb').write_bytes(valid)
def bad(name,position,reseal=True):
 altered=bytearray(payload);altered[position]^=1;body=bytes(altered);(work/(name+'.sdb')).write_bytes(body+(sha(body) if reseal else sha(payload)))
bad('bad-checksum',-1,False);bad('bad-version',7);bad('bad-policy',16);bad('bad-nonce',16+len(policy)+8+8)
bad('bad-parsed',len(payload)-1);bad('bad-packet',16+len(policy)+8+len(request)+8)
(work/'truncated.sdb').write_bytes(valid[:-1]);(work/'oversized.sdb').write_bytes(bytes(1048576+8192+257))
command=[a.compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c',*[module+suffix for module in mods for suffix in ['.mli','.ml']],'kernel.ml','-o','kernel']
for kind,command in [('compile',command),('test',[str(work/'kernel')])]:
 result=subprocess.run(command,cwd=work,capture_output=True,text=True);(work/(kind+'.log')).write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
 print(result.stdout,end='')
a.report.write_text(json.dumps({'workspace':str(work),'version':version,'mode_checked':'+ox' in version,'cases':13,'golden_sha256':hashlib.sha256(valid).hexdigest(),'scope':'independent finite SDB bytes and exact reconciliation; no storage authority/SDK','source_pins':{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [root/'src'/(module+suffix) for module in mods for suffix in ['.mli','.ml','.ox.mli.in']]}},indent=2)+'\n')
