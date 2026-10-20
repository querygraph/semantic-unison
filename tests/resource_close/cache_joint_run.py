"""Actual joint cache scopes, opaque directories, descriptors and temporary names."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--report',required=True);a=p.parse_args()
r=json.loads(Path(a.receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
for name,digest in r['source_sha256'].items():
 if name.startswith('src/'):assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
text=(build/'Makefile.OCaml').read_text()
def objects(name):
 body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
 return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticMergeCache.cmx')];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
work=Path(tempfile.mkdtemp(prefix='unison-local-owner-'));work.chmod(0o700);calls=[]
(work/'state').mkdir(mode=0o700);env=dict(os.environ,UNISON=str(work/'state'))
flags=[v for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for v in ['-I',str(d)]]+['-I','+unix','-I','+str']
def call(argv,cwd=work,expected=0):
 c=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
 if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
 return c
shutil.copyfile(HERE/'cache_joint_fault.ml',work/'cacheJointFault.ml');call([compiler,*flags,'-c','cacheJointFault.ml'])
directory=(build/'directoryOwner.ml').read_text();old='Unix.closedir (Obj.obj owner.handle : Unix.dir_handle)';assert directory.count(old)==1
(work/'directoryOwnerForCache.ml').write_text(directory.replace(old,'CacheJointFault.closedir owner.path (Obj.obj owner.handle : Unix.dir_handle)'))
call([compiler,*flags,'-c','directoryOwnerForCache.ml'])
for obj in modules[start:]:
 name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
 if name=='notificationPipe':
  old='Unix.close t.read.fd';assert source.count(old)==1
  source=source.replace(old,'CacheJointFault.close t.read.fd')
 (work/(name+'.ml')).write_text(source)
 for ext in ['.mli','.cmi']:
  if (build/(name+ext)).exists():shutil.copyfile(build/(name+ext),work/(name+ext))
 argv=[compiler,*flags]
 if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
 call(argv+['-c',name+'.ml'])
source=(build/'semanticMergeCache.ml').read_text().replace('DirectoryOwner.','DirectoryOwnerForCache.')
for old,new in [('NotificationPipe.adopt_read file fd;','NotificationPipe.adopt_read file fd;CacheJointFault.acquired filename fd;'),('Unix.unlink owner.temporary','CacheJointFault.unlink owner.temporary'),('let rec loop count =','CacheJointFault.quota_body ();\n        let rec loop count ='),('let remove_temporary owner =','let remove_temporary owner =\n  CacheJointFault.before_remove owner.temporary;')]:
 assert source.count(old)==1;source=source.replace(old,new)
(work/'semanticMergeCacheForOwner.ml').write_text(source)
shutil.copyfile(HERE/'cache_joint_test.ml',work/'cache_joint_test.ml')
sync=(build/'semanticSync.ml').read_text().replace('SemanticMergeCache.','SemanticMergeCacheForOwner.')
(work/'semanticSyncForCache.ml').write_text(sync)
def link(binary):
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['cacheJointFault.cmx','directoryOwnerForCache.cmx']+[str(work/x) for x in modules[start:]]+['semanticMergeCacheForOwner.ml','semanticSyncForCache.ml','cache_joint_test.ml']+[str(build/x) for x in native]+['-o',str(work/binary)])
link('fixed')
fixed_binary_sha256=hashlib.sha256((work/'fixed').read_bytes()).hexdigest()
import struct
data=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
packet=b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="1" xmp:Label="Blue"/></rdf:RDF>'
packet+=b' '*(8192-len(packet))
for i,e in enumerate([(273,4,1,12288),(279,4,1,len(data)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',data,10+12*i,*e)
struct.pack_into('<I',data,58,0);data[1024:9216]=packet
modes=['known','read-before','read-after','quota-before','quota-after','temporary-before','temporary-after','directory-before','directory-after','root-after','inner-shard-after','error-quota-dir','unlink-before','unlink-after','capture-temporary-after','capture-root-after','merge-read-after','temporary-interrupt','temporary-interrupt-close','unlink-rebound']
def case(mode,binary='fixed',expected=0):
 folder=work/(binary+'-'+mode);folder.mkdir(mode=0o700);(folder/'base.dng').write_bytes(data);(folder/'state').mkdir(mode=0o700)
 c=call([str(work/binary),mode],cwd=folder,expected=expected)
 assert (folder/'base.dng').read_bytes()==data
 return c
# Each process uses its own state; invoke with exact private UNISON directory.
original_call=call
def call(argv,cwd=work,expected=0):
 global env
 old=env;env=dict(old,UNISON=str(cwd/'state')) if cwd!=work else old
 try:return original_call(argv,cwd,expected)
 finally:env=old
for mode in modes:case(mode)
# Swallowing a read close must be rejected as a false ordinary cache result.
old='with NotificationPipe.Uncertain _ as error->note_unknown owner error;raise_unknown owner'
assert source.count(old)==1
bad=source.replace(old,'with NotificationPipe.Uncertain _ -> ()')
cleanup='with NotificationPipe.Uncertain _ as error->note_unknown owner error)'
assert bad.count(cleanup)==1
bad=bad.replace(cleanup,'with NotificationPipe.Uncertain _ -> ())')
(work/'semanticMergeCacheForOwner.ml').write_text(bad)
link('bad')
c=case('read-after','bad',2);assert 'DESIGNATED cache uncertainty escaped' in c.stderr
with Path(a.report).open('x') as f:json.dump(dict(scope='20actual store/load/capture/merge joint-owner scenarios inside Runtime transaction plus designated swallowing rejection. Private aliases preserve full DirectoryOwner implementation with close-call injection; no numeric opaque-directory guessing. Generated64KiBDNG only/noSDK/Photo/transport/EXIO/aggregatehardlimits.',compiler=compiler,work=str(work),calls=calls,controlled_cache_sha256=hashlib.sha256(source.encode()).hexdigest(),original_directory_sha256=hashlib.sha256(directory.encode()).hexdigest(),controlled_directory_sha256=hashlib.sha256((work/'directoryOwnerForCache.ml').read_bytes()).hexdigest(),fixed_binary_sha256=fixed_binary_sha256,bad_binary_sha256=hashlib.sha256((work/'bad').read_bytes()).hexdigest(),bad_controlled_cache_sha256=hashlib.sha256(bad.encode()).hexdigest(),fixture_sha256=hashlib.sha256(data).hexdigest()),f,indent=2)
print('PASS joint cache',compiler,len(modes),'and designated rejection')
