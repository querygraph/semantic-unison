#!/usr/bin/env python3
"""Private generated JPEG + OS ImageIO decode; no Photo/Adobe inputs."""
import argparse,hashlib,json,pathlib,struct,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--kernel',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-jpeg-decoded-',dir='/private/tmp'));width,height=72,48
rowbytes=(width*3+3)&~3;pixels=b''.join(bytes(v for x in range(width) for v in [(x*3+y)%256,(y*5)%256,(x+y*2)%256])+b'\0'*(rowbytes-width*3) for y in range(height))
bmp=struct.pack('<2sIHHI',b'BM',54+len(pixels),0,0,54)+struct.pack('<IiiHHIIiiII',40,width,height,1,24,0,len(pixels),2835,2835,0,0)+pixels
(w/'source.bmp').write_bytes(bmp)
def sips(source,fmt,target):
 r=subprocess.run(['/usr/bin/sips','-s','format',fmt,str(source),'--out',str(target)],capture_output=True,text=True,timeout=30);assert r.returncode==0,r.stdout+r.stderr;return r.stdout+r.stderr
logs=[sips(w/'source.bmp','jpeg',w/'encoded.jpg')];jpeg=(w/'encoded.jpg').read_bytes();assert jpeg[:2]==b'\xff\xd8'
packet=b'<x>one</x>      ';sig=b'http://ns.adobe.com/xap/1.0/\0';app=b'\xff\xe1'+struct.pack('>H',len(sig)+len(packet)+2)+sig+packet
basis=jpeg[:2]+app+jpeg[2:];target=basis.replace(packet,b'<x>two</x>      ',1)
for n,data in [('basis.jpg',basis),('target.jpg',target),('stage.jpg',basis)]:(w/n).write_bytes(data)
r=subprocess.run([a.kernel,'apply',str(w/'basis.jpg'),str(w/'target.jpg'),str(w/'stage.jpg')],capture_output=True,text=True,timeout=30);assert r.returncode==0 and r.stdout.strip()=='APPLIED 16 1',r.stdout+r.stderr
assert (w/'stage.jpg').read_bytes()==target and (w/'basis.jpg').read_bytes()==basis
logs += [sips(w/'basis.jpg','bmp',w/'decoded-basis.bmp'),sips(w/'stage.jpg','bmp',w/'decoded-target.bmp')]
def raster(path):
 b=path.read_bytes();off=struct.unpack_from('<I',b,10)[0];geometry=struct.unpack_from('<ii',b,18);bits=struct.unpack_from('<H',b,28)[0];compression=struct.unpack_from('<I',b,30)[0];assert geometry[0]==width and abs(geometry[1])==height and compression==0;return geometry,bits,b[off:]
left=raster(w/'decoded-basis.bmp');right=raster(w/'decoded-target.bmp');assert left==right
receipt=dict(schema='unison-jpeg-generated-decode/1',status='passed',workspace=str(w),decoder='/usr/bin/sips (macOS ImageIO)',kernel=a.kernel,kernelSha256=hashlib.sha256(pathlib.Path(a.kernel).read_bytes()).hexdigest(),geometry=list(left[0]),decodedBits=left[1],decodedRasterSha256=hashlib.sha256(left[2]).hexdigest(),exactSourceReconstruction=True,unchangedBasis=True,decodedRasterEqual=True,scope='One privately generated JPEG; not Adobe/Lightroom/profile/color/representative JPEG corpus qualification',logs=logs)
a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print('PASS generated JPEG exact output and decoded raster parity',w)
