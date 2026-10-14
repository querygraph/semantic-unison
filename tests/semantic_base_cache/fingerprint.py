#!/usr/bin/env python3
"""Link actual compiler-matched fingerprint objects; owned original files only."""
import argparse,hashlib,json,pathlib,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];work=pathlib.Path(tempfile.mkdtemp(prefix='unison-held-md5-',dir='/private/tmp'));print('Workspace:',work,flush=True)
for name in ['src/fingerprint.ml','src/fingerprint.mli']:assert (root/name).read_bytes()==(a.build/name).read_bytes()
shutil.copyfile(root/'tests/semantic_base_cache/fingerprint.ml',work/'probe.ml')
# Native objects are immutable inputs. The full library is linked to preserve
# exactly its actual platform/compatibility dependencies and initialization.
objects=(a.build/'src/Makefile.OCaml').read_text().split('OCAMLOBJS =',1)[1].split('\n\n',1)[0].replace('\\','').split()
# Resolve Make platform variables for current macOS generic builds.
objects=[name.replace('$(SYSTEM)','generic') for name in objects if name!='$(WINOBJS)']
# Retain the source object's ordered dependency prefix through Fingerprint.
objects=objects[:objects.index('fingerprint.cmo')+1]
paths=[str(a.build/'src'/name.replace('.cmo','.cmx')) for name in objects]
includes=['src','src/ubase','src/system','src/system/generic','src/lwt','src/lwt/generic']
flags=[value for path in includes for value in ['-I',str(a.build/path)]]
stubs=['pty.o','bytearray_stubs.o','hash_compat.o','props_xattr.o','props_acl.o','osxsupport.o','copy_stubs.o','nativeCopyRange_stubs.o','wholeFileClone_stubs.o','fileObservation_stubs.o','stagePublication_stubs.o','finalPublication_stubs.o']
command=[a.compiler,*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa',*[str(a.build/'src'/name) for name in stubs],*paths,'probe.ml','-o','probe']
result=subprocess.run(command,cwd=work,capture_output=True,text=True);(work/'compile.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
result=subprocess.run([str(work/'probe')],cwd=work,capture_output=True,text=True);(work/'test.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
print(result.stdout,end='')
a.report.write_text(json.dumps({'workspace':str(work),'build':str(a.build),'cases':8,'scope':'actual native fingerprint objects on original disposable files','binary_sha256':hashlib.sha256((work/'probe').read_bytes()).hexdigest()},indent=2)+'\n')
