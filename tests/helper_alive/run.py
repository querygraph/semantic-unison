"""Actual supervised /bin/sleep observations; no SDK, camera, Photo or payload."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,shutil
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-helper-alive-'))
sources=['src/lwt/lwt.mli','src/lwt/lwt.ml','src/lwt/pqueue.mli','src/lwt/pqueue.ml','src/lwt/generic/lwt_unix_impl.ml','src/lwt/lwt_unix.mli','src/lwt/lwt_unix.ml','src/borrowedWork.mli','src/borrowedWork.ml','src/helperSupervisor_stubs.c','src/helperSupervisor.mli','src/helperSupervisor.ml','tests/helper_alive/test.ml']
print('Build',w,flush=True)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in sources:shutil.copyfile(root/name,w/pathlib.Path(name).name)
with (w/'build.log').open('w') as f:
 for name in sources[:-1]:subprocess.run([a.compiler,'-I','+unix','-c',pathlib.Path(name).name],cwd=w,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=20)
 objs=[pathlib.Path(n).stem+('.o' if n.endswith('.c') else '.cmx') for n in sources[:-1] if n.endswith(('.c','.ml'))]
 subprocess.run([a.compiler,'-I','+unix','unix.cmxa',*objs,'test.ml','-o','control'],cwd=w,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=20)
r=subprocess.run([str(w/'control')],cwd=w,capture_output=True,text=True,timeout=10);(w/'test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,end='')
a.report.write_text(json.dumps({'passed':r.returncode==0,'exit_code':r.returncode,'workspace':str(w),'sources':{n:h(root/n) for n in sources},'compiler':a.compiler,'helper':{'path':'/bin/sleep','sha256':h(pathlib.Path('/bin/sleep'))},'test_log_sha256':h(w/'test.log'),'scope':'actual3sleep helpers/native supervisor, observed live overlap/group0/directreap; no SDK/Photo/camera/EXglobal'},indent=2)+'\n');raise SystemExit(r.returncode)
