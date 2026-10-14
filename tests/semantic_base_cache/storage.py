#!/usr/bin/env python3
"""Link actual compiler-matched private cache objects; deterministic original files only."""
import argparse,hashlib,json,os,pathlib,shutil,struct,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];work=pathlib.Path(tempfile.mkdtemp(prefix='unison-cache-storage-',dir='/private/tmp'));print('Workspace:',work,flush=True)
for name in ['src/semanticMergeCache.ml','src/semanticMergeCache.mli']:assert (root/name).read_bytes()==(a.build/name).read_bytes()
shutil.copyfile(root/'tests/semantic_base_cache/storage.ml',work/'probe.ml')
# Native objects are immutable inputs. The full library is linked to preserve
# exactly its actual platform/compatibility dependencies and initialization.
objects=(a.build/'src/Makefile.OCaml').read_text().split('OCAMLOBJS =',1)[1].split('\n\n',1)[0].replace('\\','').split()
# Resolve Make platform variables for current macOS generic builds.
objects=[name.replace('$(SYSTEM)','generic') for name in objects if name!='$(WINOBJS)']
# Retain the source object's ordered dependency prefix through SemanticMergeCache.
objects=objects[:objects.index('semanticMergeCache.cmo')+1]
paths=[str(a.build/'src'/name.replace('.cmo','.cmx')) for name in objects]
includes=['src','src/ubase','src/system','src/system/generic','src/lwt','src/lwt/generic']
flags=[value for path in includes for value in ['-I',str(a.build/path)]]
stubs=['pty.o','bytearray_stubs.o','hash_compat.o','props_xattr.o','props_acl.o','osxsupport.o','copy_stubs.o','nativeCopyRange_stubs.o','wholeFileClone_stubs.o','fileObservation_stubs.o','stagePublication_stubs.o','finalPublication_stubs.o','semanticHash_stubs.o','semanticFile_stubs.o','helperSupervisor_stubs.o']
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
a.report.write_text(json.dumps({'workspace':str(work),'build':str(a.build),'cases':16,'compiler_version':subprocess.check_output([a.compiler,'-version'],text=True).strip(),'probe_source_sha256':hashlib.sha256((root/'tests/semantic_base_cache/storage.ml').read_bytes()).hexdigest(),'scope':'actual native cache objects; finite private storage trust/capacity/FD controls; no SDK', 'source_sha256':hashlib.sha256((root/'src/semanticMergeCache.ml').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((work/'probe').read_bytes()).hexdigest()},indent=2)+'\n')
