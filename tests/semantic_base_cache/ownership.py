#!/usr/bin/env python3
"""Link actual compiler-matched private acquisition exception guards; no production fault hooks."""
import argparse,hashlib,json,os,pathlib,shutil,struct,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];work=pathlib.Path(tempfile.mkdtemp(prefix='unison-cache-ownership-',dir='/private/tmp'));print('Workspace:',work,flush=True)
for name in ['src/semanticMergeCache.ml','src/semanticMergeCache.mli']:assert (root/name).read_bytes()==(a.build/name).read_bytes()
shutil.copyfile(root/'tests/semantic_base_cache/ownership.ml',work/'probe.ml')
# Native objects are immutable inputs. The full library is linked to preserve
# exactly its actual platform/compatibility dependencies and initialization.
objects=(a.build/'src/Makefile.OCaml').read_text().split('OCAMLOBJS =',1)[1].split('\n\n',1)[0].replace('\\','').split()
# Resolve Make platform variables for current macOS generic builds.
objects=[name.replace('$(SYSTEM)','generic') for name in objects if name!='$(WINOBJS)']
# Retain the source object's ordered dependency prefix through SemanticMergeCache.
objects=objects[:objects.index('semanticMergeCache.cmo')+1]
paths=[str(a.build/'src'/name.replace('.cmo','.cmx')) for name in objects[:-1]]
includes=['src','src/ubase','src/system','src/system/generic','src/lwt','src/lwt/generic']
flags=[value for path in includes for value in ['-I',str(a.build/path)]]
stubs=['pty.o','bytearray_stubs.o','hash_compat.o','props_xattr.o','props_acl.o','osxsupport.o','copy_stubs.o','nativeCopyRange_stubs.o','wholeFileClone_stubs.o','fileObservation_stubs.o','stagePublication_stubs.o','finalPublication_stubs.o','semanticHash_stubs.o','semanticFile_stubs.o','helperSupervisor_stubs.o']
# Compile one private copy against its actual production interface. Faults
# are injected into the protected body, never exposed in production source.
source=(root/'src/semanticMergeCache.ml').read_text()
for point,anchor in [('read','  match\n    if not (same before'),
                     ('directory','      (match\n        let rec count total ='),
                     ('quota','  match\n    (match before with None -> Unix.fchmod'),
                     ('quota-root','      (match\n        let rec loop count ='),
                     ('quota-shard','  match\n    let rec loop () ='),
                     ('temporary','      match\n        Unix.fchmod fd')]:
 assert source.count(anchor)==1,point
 first,rest=anchor.split('\n',1)
 source=source.replace(anchor,first+'\n'+(' '*4 if point=='read' else ' '*8)+
     'if Sys.getenv_opt "UNISON_PRIVATE_CACHE_FAULT" = Some "'+point+'" then raise Out_of_memory;\n'+rest)
(work/'semanticMergeCache.ml').write_text(source)
shutil.copyfile(a.build/'src/semanticMergeCache.cmi',work/'semanticMergeCache.cmi')
compiled=subprocess.run([a.compiler,*flags,'-c','semanticMergeCache.ml'],cwd=work,capture_output=True,text=True)
(work/'fault-module-compile.log').write_text(compiled.stdout+compiled.stderr);assert compiled.returncode==0,compiled.stderr
paths.append(str(work/'semanticMergeCache.cmx'))
command=[a.compiler,*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa',*[str(a.build/'src'/name) for name in stubs],*paths,'probe.ml','-o','probe']
result=subprocess.run(command,cwd=work,capture_output=True,text=True);(work/'compile.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
# Original minimal TIFF/DNG-shaped fixture: finite parser/storage tests, no SDK.
data=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
packet=b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="1" xmp:Label="Blue"/></rdf:RDF>'
packet+=b' '*(8192-len(packet))
for i,e in enumerate([(273,4,1,12288),(279,4,1,len(data)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',data,10+12*i,*e)
struct.pack_into('<I',data,58,0);data[1024:9216]=packet;(work/'base.dng').write_bytes(data)
state=work/'state';state.mkdir(mode=0o700)
env=dict(os.environ,UNISON=str(state))
result=subprocess.run([str(work/'probe')],cwd=work,env=env,capture_output=True,text=True);(work/'test.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
print(result.stdout,end='')
# Deliberately place the read fault BEFORE its guard in another private
# executable. The same conservation probe must observe its one leaked FD.
negative=work/'negative';negative.mkdir()
source=(root/'src/semanticMergeCache.ml').read_text()
anchor='  let fd = Unix.openfile filename [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in'
assert source.count(anchor)==1
source=source.replace(anchor,anchor+'\n  if Sys.getenv_opt "UNISON_PRIVATE_CACHE_FAULT" = Some "read" then raise Out_of_memory;')
(negative/'semanticMergeCache.ml').write_text(source)
for name in ['semanticMergeCache.cmi']:
 shutil.copyfile(a.build/'src'/name,negative/name)
shutil.copyfile(work/'probe.ml',negative/'probe.ml');shutil.copyfile(work/'base.dng',negative/'base.dng')
x=subprocess.run([a.compiler,*flags,'-c','semanticMergeCache.ml'],cwd=negative,capture_output=True,text=True)
(negative/'module-compile.log').write_text(x.stdout+x.stderr);assert x.returncode==0,x.stderr
negative_command=[str(negative/'semanticMergeCache.cmx') if arg==str(work/'semanticMergeCache.cmx') else arg for arg in command]
x=subprocess.run(negative_command,cwd=negative,capture_output=True,text=True)
(negative/'compile.log').write_text(x.stdout+x.stderr);assert x.returncode==0,x.stderr
(negative/'state').mkdir(mode=0o700)
x=subprocess.run([str(negative/'probe')],cwd=negative,env=dict(os.environ,UNISON=str(negative/'state')),capture_output=True,text=True)
(negative/'test.log').write_text(x.stdout+x.stderr)
assert x.returncode!=0 and 'read acquisition fault leaked descriptor' in x.stderr,x.stdout+x.stderr
print('PASS unguarded private negative detected one acquired-descriptor leak',flush=True)
a.report.write_text(json.dumps({'workspace':str(work),'build':str(a.build),'cases':6,'negative_control':{'exit':x.returncode,'expected':'read acquisition fault leaked descriptor','source_sha256':hashlib.sha256((negative/'semanticMergeCache.ml').read_bytes()).hexdigest(),'test_log_sha256':hashlib.sha256((negative/'test.log').read_bytes()).hexdigest()},'compiler_version':subprocess.check_output([a.compiler,'-version'],text=True).strip(),'private_fault_source_sha256':hashlib.sha256((work/'semanticMergeCache.ml').read_bytes()).hexdigest(),'probe_source_sha256':hashlib.sha256((root/'tests/semantic_base_cache/ownership.ml').read_bytes()).hexdigest(),'scope':'actual production interface/dependency objects plus privately injected cache body; six deterministic acquired-resource exceptions; no actual memory exhaustion/SDK', 'source_sha256':hashlib.sha256((root/'src/semanticMergeCache.ml').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((work/'probe').read_bytes()).hexdigest()},indent=2)+'\n')
