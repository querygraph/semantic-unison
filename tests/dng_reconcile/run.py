#!/usr/bin/env python3
import argparse,pathlib,tempfile,subprocess,hashlib,json,shutil,struct,ctypes,sys
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-dng-reconcile-',dir='/private/tmp'));version=subprocess.check_output([a.compiler,'-version'],text=True).strip();ox='+ox' in version
mods=['semanticHash','semanticFile','formatExtension','xmpObservation','xmpMerge','dngSemantic','semanticDelta'];sources=['src/'+n+e for n in mods for e in ['.mli','.ml','.ox.mli.in']]+['src/semanticHash_stubs.c','src/semanticHash_evp.h','src/semanticFile_stubs.c','src/semantic_mode_filter.ml','tests/dng_reconcile/test.ml','tests/dng_reconcile/run.py']
for s in sources:shutil.copyfile(r/s,w/pathlib.Path(s).name)
subprocess.run([a.compiler,'-o','filter','semantic_mode_filter.ml'],cwd=w,check=True)
for n in mods:
 for ext in ['mli','ml']:
  q=w/(n+'.'+ext);q.write_bytes(subprocess.check_output([str(w/'filter'),version,str(q)]))
if ox:
 q=w/'test.ml';s=q.read_text();assert s.count('let () =')==1;q.write_text(s.replace('let () =','let controls () =')+'\nlet () = let d=Domain.Safe.spawn(fun () -> controls()) in Domain.join d\n')
def fixture(rating,label,opaque=False,maker=None,private=None,scalars=(),flip_at=None,subxmp=False,props=0,xmptype=1):
 b=bytearray(bytes((i*71+19)%256 for i in range(2097152)));struct.pack_into('<2sHIH',b,0,b'II',42,8,4)
 packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"'+''.join(f' xmp:P{i}="0"' for i in range(props))+'/></rdf:RDF>').encode();packet+=b' '*(8192-len(packet))
 entries=[(273,4,1,12288),(279,4,1,len(b)-12288),(700,xmptype,8192,1024),(50706,1,4,1025)]
 if maker:entries.append((34665,4,1,9216))
 if subxmp:entries.append((330,4,1,9700))
 # Opaque DNGPrivateData: (type, offset, flipped byte or None, in IFD1 instead of the primary IFD).
 if private and not private[3]:entries.append((50740,private[0],64,private[1]))
 entries+=list(scalars)
 struct.pack_into('<H',b,8,len(entries))
 for i,e in enumerate(entries):struct.pack_into('<HHII',b,10+12*i,*e)
 struct.pack_into('<I',b,10+12*len(entries),0);b[1024:9216]=packet
 if maker:
  # One-entry Exif IFD holding an opaque MakerNote: (type, offset, flipped byte or None).
  typ,offset,flip=maker;struct.pack_into('<HHHII',b,9216,1,37500,typ,64,offset);struct.pack_into('<I',b,9230,0)
  if flip is not None:b[offset+flip]^=1
 if private:
  typ,offset,flip,ifd1=private
  if ifd1:struct.pack_into('<I',b,10+12*len(entries),9500);struct.pack_into('<HHHII',b,9500,1,50740,typ,64,offset);struct.pack_into('<I',b,9514,0)
  if flip is not None:b[offset+flip]^=1
 if subxmp:
  # One SubIFD carrying its own 64-byte XMP packet, as iPhone mattes do.
  struct.pack_into('<HHHII',b,9700,1,700,7,64,9750);struct.pack_into('<I',b,9714,0)
 if opaque:b[-1]^=1
 if flip_at is not None:b[flip_at]^=1
 return bytes(b)
inputs={'base.dng':fixture('1','Blue'),'left.dng':fixture('2','Blue'),'right.dng':fixture('1','Gold'),'target.dng':fixture('2','Gold'),'opaque.dng':fixture('1','Gold',True),'conflict.dng':fixture('3','Blue'),
 'maker-base.dng':fixture('1','Blue',maker=(7,9300,None)),'maker-left.dng':fixture('2','Blue',maker=(7,9300,None)),
 'maker-right.dng':fixture('1','Gold',maker=(7,9300,None)),'maker-target.dng':fixture('2','Gold',maker=(7,9300,None)),
 'maker-changed.dng':fixture('1','Gold',maker=(7,9300,5)),'maker-alias.dng':fixture('1','Blue',maker=(7,2048,None)),
 'maker-type.dng':fixture('1','Blue',maker=(4,9300,None))}
P=(1,9400,None,False);M=(7,9300,None)
# Scan-found fields: SelfTimerMode and the five depth fields (simple SHORT and
# RATIONAL types, RATIONALs out of line at 9900/9908), an unknown FLOAT, and a
# 64-byte ProfileGainTableMap at 9800, a 32-byte tag 52545 at 9920, an inline
# 4-byte TIFF/EP StandardID and an SSHORT 34858.
X=[(34858,8,1,0),(34859,3,1,0),(37398,1,4,1),(51177,3,1,1),(51178,5,1,9900),(51179,5,1,9908),(51180,3,1,1),(51181,3,1,0),(52525,7,64,9800),(52545,7,32,9920),(60001,11,1,0)]
for prefix,kw in (('priv',dict(private=P)),('both',dict(maker=M,private=P)),('extra',dict(scalars=X)),('sub',dict(subxmp=True)),('many',dict(props=300)),('undef',dict(xmptype=7))):
 for name,(rating,label) in dict(base=('1','Blue'),left=('2','Blue'),right=('1','Gold'),target=('2','Gold')).items():
  inputs[f'{prefix}-{name}.dng']=fixture(rating,label,**kw)
inputs.update({'priv-changed.dng':fixture('1','Gold',private=(1,9400,7,False)),'priv-alias.dng':fixture('1','Blue',private=(1,2048,None,False)),
 'priv-type.dng':fixture('1','Blue',private=(7,9400,None,False)),
 # Merge-only LONG scalars: ImageNumber and CacheVersion, count 1; count 2 must decline.
 'scalar-base.dng':fixture('1','Blue',scalars=[(37393,4,1,7160),(51114,4,1,0x01000000)]),
 'scalar-count.dng':fixture('1','Blue',scalars=[(37393,4,2,9700)]),
 'extra-changed.dng':fixture('1','Gold',scalars=X,flip_at=9803),'sub-changed.dng':fixture('1','Gold',subxmp=True,flip_at=9760),'long-unknown.dng':fixture('1','Blue',scalars=[(60000,4,1,7)]),'gain-type.dng':fixture('1','Blue',scalars=[(52525,1,64,9800)]),
 'gain-alias.dng':fixture('1','Blue',scalars=[(52525,7,64,2048)]),'priv-ifd1.dng':fixture('1','Blue',private=(1,9600,None,True))})
STAGED=('maker','priv','both','extra','sub','many','undef')
for n,b in inputs.items():(w/n).write_bytes(b)
if sys.platform=='darwin':
 libc=ctypes.CDLL(None,use_errno=True);clone=libc.clonefile;clone.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];clone.restype=ctypes.c_int
 assert clone(str(w/'left.dng').encode(),str(w/'stage.dng').encode(),0)==0,ctypes.get_errno()
 for prefix in STAGED:assert clone(str(w/f'{prefix}-left.dng').encode(),str(w/f'{prefix}-stage.dng').encode(),0)==0,ctypes.get_errno()
 substrate='Darwin clonefile success on private same-volume fixture'
else:
 (w/'stage.dng').write_bytes(inputs['left.dng']);[(w/f'{prefix}-stage.dng').write_bytes(inputs[f'{prefix}-left.dng']) for prefix in STAGED];substrate='ordinary private exact copy; native cloning unqualified'
assert (w/'stage.dng').stat().st_ino!=(w/'left.dng').stat().st_ino
cmd=[a.compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c',*[n+e for n in mods for e in ['.mli','.ml']],'test.ml','-o','test'];x=subprocess.run(cmd,cwd=w,capture_output=True,text=True);(w/'compile.log').write_text(x.stdout+x.stderr);assert x.returncode==0,x.stderr
x=subprocess.run([str(w/'test')],cwd=w,capture_output=True,text=True);(w/'test.log').write_text(x.stdout+x.stderr);print(x.stdout+x.stderr,end='');assert x.returncode==0
for n,b in inputs.items():assert (w/n).read_bytes()==b
assert (w/'stage.dng').read_bytes()==inputs['target.dng'] and all((w/f'{p}-stage.dng').read_bytes()==inputs[f'{p}-target.dng'] for p in STAGED)
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=dict(schema='unison-dng-three-way-plan/1',status='passed',workspace=str(w),compiler=dict(path=a.compiler,version=version),sourcePins={s:H(r/s) for s in sources},binarySha256=H(w/'test'),compileLogSha256=H(w/'compile.log'),testLogSha256=H(w/'test.log'),targetSha256=H(w/'stage.dng'),inputHashes={n:H(w/n) for n in inputs},modeChecked=ox,stageSubstrate=substrate,automaticMergeEnabled=False,archiveBaseAuthorityQualified=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n')
