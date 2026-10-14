#!/usr/bin/env python3
"""Actual negotiated JPEG receiver updates, mixed compilers and old peers."""
import argparse, hashlib, json, os, pathlib, struct, subprocess, tempfile
p=argparse.ArgumentParser();p.add_argument('--client',required=True);p.add_argument('--server',required=True);p.add_argument('--legacy',action='store_true');p.add_argument('--disabled',action='store_true');p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-jpeg-sync-',dir='/private/tmp'));left=w/'left';right=w/'right';state=w/'state'
for d in [left,right,state]:d.mkdir()
launcher=w/'loopback.py';launcher.write_text('#!/usr/bin/env python3\nimport os,sys\na=sys.argv[1:];i=a.index('+repr(a.server)+');os.execv(a[i],a[i:])\n');launcher.chmod(0o700)
def seg(m,data):return bytes([255,m])+struct.pack('>H',len(data)+2)+data
def fixture(value=b'one',opaque=b'A'):
 return (b'\xff\xd8'+seg(0xe1,b'Exif\0\0preserved')+seg(0xe1,b'http://ns.adobe.com/xap/1.0/\0<x>'+value+b'</x>      ')+seg(0xc0,b'\x08\x00\x02\x00\x03\x01\x01\x11\x00')+seg(0xda,b'\x01\x01\x00\x00\x3f\x00')+b'\x11\xff\x00\x33\xff\xd9'+opaque*(2*1024*1024))
cmd=[a.client,str(left),'ssh://localhost/'+str(right),'-sshcmd',str(launcher),'-servercmd',a.server,'-batch','-auto','-fastcheck','false','-times','-debug','semantic','-semanticprofile','org.firstpair.jpeg-xmp/0']
if a.disabled: cmd=cmd[:-2]+['-semanticdng']
checks=[]
def sync(name,expected):
 r=subprocess.run(cmd,env=dict(os.environ,UNISON=str(state)),capture_output=True,text=True,timeout=90);log=r.stdout+r.stderr;(w/(name+'.log')).write_text(log)
 assert r.returncode==0,log
 assert ('Remote semantic clone wrote' in log)==expected,(name,log)
 assert (left/'image.jpg').read_bytes()==(right/'image.jpg').read_bytes()
 for d in [left,right]:assert [f.name for f in d.iterdir()]==['image.jpg']
 checks.append(dict(name=name,semanticUsed=expected,logSha256=hashlib.sha256(log.encode()).hexdigest(),targetSha256=hashlib.sha256((right/'image.jpg').read_bytes()).hexdigest()))
x=left/'image.jpg';y=right/'image.jpg';x.write_bytes(fixture());sync('initial',False)
x.write_bytes(fixture(b'two'));sync('remote-metadata',not (a.legacy or a.disabled))
y.write_bytes(fixture(b'six'));sync('local-metadata',not (a.legacy or a.disabled))
x.write_bytes(fixture(b'new',b'Z'));sync('opaque-fallback',False)
x.write_bytes(fixture(b'longer',b'Z'));sync('growth-fallback',False)
sync('noop',False)
r=dict(schema='unison-jpeg-sync/1',status='passed',workspace=str(w),client=dict(path=a.client,sha256=hashlib.sha256(pathlib.Path(a.client).read_bytes()).hexdigest()),server=dict(path=a.server,sha256=hashlib.sha256(pathlib.Path(a.server).read_bytes()).hexdigest()),legacy=a.legacy,disabled=a.disabled,checks=checks)
a.receipt.write_text(json.dumps(r,indent=2)+'\n');print('PASS actual JPEG receiving paths',len(checks),'retained',w)
