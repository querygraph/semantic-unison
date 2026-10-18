#!/usr/bin/env python3
"""Independent JPEG marker fixtures and exact-output preservation checks."""
import argparse, hashlib, json, pathlib, shutil, struct, subprocess, tempfile
p=argparse.ArgumentParser();p.add_argument('--ocamlopt',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);p.add_argument('--old-kernel');a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];work=pathlib.Path(tempfile.mkdtemp(prefix='unison-jpeg-'))
modules=['semanticHash','semanticFile','formatExtension','xmpObservation','xmpMerge','dngSemantic','dngExtended','jpegSemantic','semanticDelta']
sources=['src/'+m+s for m in modules for s in ('.mli','.ml')]+['src/semanticHash_stubs.c','src/semanticHash_evp.h','src/semanticFile_stubs.c','tests/jpeg/test.ml']
for s in sources: shutil.copyfile(root/s,work/pathlib.Path(s).name)
cmd=[a.ocamlopt,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c']
for m in modules:cmd += [m+'.mli',m+'.ml']
subprocess.run(cmd+['test.ml','-o','jpeg-test'],cwd=work,check=True)
sig=b'http://ns.adobe.com/xap/1.0/\0';ext=b'http://ns.adobe.com/xmp/extension/\0'
def segment(m,data):return bytes([255,m])+struct.pack('>H',len(data)+2)+data
frame=segment(0xc0,b'\x08\x00\x02\x00\x03\x01\x01\x11\x00')
scan=segment(0xda,b'\x01\x01\x00\x00\x3f\x00')
exif=segment(0xe1,b'Exif\0\0opaque');icc=segment(0xe2,b'ICC_PROFILE\0opaque')
packet=b'<x>one</x>      '
head=b'\xff\xd8'+exif+icc+segment(0xe1,sig+packet)+frame+scan
entropy=b'\x11\xff\x00\x33\xff\xd0\x44\xff\xd9opaque-trailer'
base=head+entropy
checks=[]
def run(*args):return subprocess.check_output([str(work/'jpeg-test'),*map(str,args)],text=True).strip()
def inspection(name,data,eligible,offset=None,length=None):
 path=work/(name+'.jpg');path.write_bytes(data);out=run('inspect',path)
 assert (out.startswith('REGION'))==eligible,(name,out)
 if eligible: assert out==f'REGION {offset} {length}',(name,out)
 assert path.read_bytes()==data
 checks.append(dict(name=name,result=out,sha256=hashlib.sha256(data).hexdigest()))
offset=2+len(exif)+len(icc)+4+len(sig)
inspection('standard',base,True,offset,len(packet))
inspection('fill',base[:2]+b'\xff'*3+base[2:],True,offset+3,len(packet))
inspection('progressive',base.replace(frame,frame[:1]+b'\xc2'+frame[2:]),True,offset,len(packet))
inspection('cumulative-fill-boundary',b'\xff\xd8'+b'\xff'*4096+b'\xe0\x00\x02'+b'\xff'*4091+b'\xe0\x00\x02'+base[2:],True,offset+8193,len(packet))
inspection('maximum-packet',b'\xff\xd8'+segment(0xe1,sig+b'p'*65504)+frame+scan+entropy,True,35,65504)
for n in range(len(head)):
 inspection('truncated-'+str(n),base[:n],False)
for name,data in [
 ('missing-xmp',b'\xff\xd8'+frame+scan+entropy),
 ('empty-xmp',b'\xff\xd8'+segment(0xe1,sig)+frame+scan+entropy),
 ('duplicate-xmp',base[:2]+segment(0xe1,sig+packet)+base[2:]),
 ('extended-xmp',base[:2]+segment(0xe1,ext+b'opaque')+base[2:]),
 ('no-frame',base.replace(frame,b'')),('duplicate-frame',base.replace(frame,frame+frame)),
 ('bad-frame-count',base.replace(frame,segment(0xc0,b'\x08\x00\x02\x00\x03\x02\x01\x11\x00'))),
 ('zero-height',base.replace(frame,segment(0xc0,b'\x08\x00\x00\x00\x03\x01\x01\x11\x00'))),
 ('scan-count',base.replace(scan,segment(0xda,b'\x02\x01\x00\x00\x3f\x00'))),
 ('short-length',b'\xff\xd8\xff\xe1\x00\x01'+base[2:]),
 ('out-of-bounds',b'\xff\xd8\xff\xe1\xff\xff'+base[2:]),
 ('standalone-restart',b'\xff\xd8\xff\xd0'+base[2:]),
 ('fill-limit',b'\xff\xd8'+b'\xff'*4097+base[3:]),
 ('cumulative-fill-one-over',b'\xff\xd8'+b'\xff'*4096+b'\xe0\x00\x02'+b'\xff'*4092+b'\xe0\x00\x02'+base[2:]),
 ('cumulative-fill-limit',b'\xff\xd8'+(b'\xff'*3000+b'\xe0\x00\x02')*3+base[2:]),
 ('marker-limit',b'\xff\xd8'+segment(0xfe,b'')*4097+base[2:]),
 ('header-limit',b'\xff\xd8'+segment(0xfe,b'c'*65533)*257+base[2:])]:inspection(name,data,False)
negative=None
if a.old_kernel:
 old=pathlib.Path(a.old_kernel);out=subprocess.check_output([str(old),'inspect',str(work/'cumulative-fill-limit.jpg')],text=True).strip();assert out.startswith('REGION'),out
 negative=dict(binary=str(old),binarySha256=hashlib.sha256(old.read_bytes()).hexdigest(),oldResult=out,newResult=[c['result'] for c in checks if c['name']=='cumulative-fill-limit'][0])
basepath=work/'basis.jpg';targetpath=work/'target.jpg';stage=work/'stage.jpg'
for name,target,applied in [
 ('metadata',base.replace(b'one',b'two'),True),('unchanged',base,True),
 ('entropy',base[:-len(entropy)]+entropy.replace(b'\x33',b'\x34'),False),
 ('exif',base.replace(b'Exif\0\0opaque',b'Exif\0\0OPAQUE'),False),
 ('icc',base.replace(b'ICC_PROFILE\0opaque',b'ICC_PROFILE\0OPAQUE'),False),
 ('trailer',base[:-1]+b'!',False),
 ('growth',base.replace(segment(0xe1,sig+packet),segment(0xe1,sig+packet+b' ')),False),
 ('relocation',b'\xff\xd8'+segment(0xe1,sig+packet)+exif+icc+frame+scan+entropy,False)]:
 basepath.write_bytes(base);targetpath.write_bytes(target);stage.write_bytes(base)
 out=run('apply',basepath,targetpath,stage);assert out.startswith('APPLIED')==applied,(name,out)
 assert basepath.read_bytes()==base and targetpath.read_bytes()==target
 assert stage.read_bytes()==(target if applied else base),(name,'exact bytes')
 if name=='metadata':assert out==f'APPLIED {len(packet)} 1',out
 if name=='unchanged':assert out=='APPLIED 0 0',out
 checks.append(dict(name=name,result=out,exactBytes=True))
r=dict(schema='unison-jpeg-profile/1',status='passed',compiler=a.ocamlopt,compilerVersion=subprocess.check_output([a.ocamlopt,'-version'],text=True).strip(),workspace=str(work),sourcePins={s:hashlib.sha256((root/s).read_bytes()).hexdigest() for s in sources+['tests/jpeg/run.py']},binarySha256=hashlib.sha256((work/'jpeg-test').read_bytes()).hexdigest(),checks=checks,previousKernelNegative=negative)
a.receipt.write_text(json.dumps(r,indent=2)+'\n');print('PASS JPEG',len(checks),'cases; retained',work)
