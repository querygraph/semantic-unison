#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile,shutil,json,hashlib,resource,os
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-helper-limits-')).resolve();before=resource.getrlimit(resource.RLIMIT_NOFILE)
sources=['src/lwt/lwt.mli','src/lwt/lwt.ml','src/lwt/pqueue.mli','src/lwt/pqueue.ml','src/lwt/generic/lwt_unix_impl.ml','src/lwt/lwt_unix.mli','src/lwt/lwt_unix.ml','src/borrowedWork.mli','src/borrowedWork.ml','src/helperSupervisor.mli','src/helperSupervisor.ml','src/helperSupervisor_stubs.c','tests/helper_limits/test.ml','tests/helper_limits/probe.c','tools/helper-limits/launcher.c','tests/helper_limits/close_fixture.c','tests/helper_limits/darwin_close_fixture.c']
for s in sources:shutil.copyfile(r/s,w/pathlib.Path(s).name)
commands=[]
def run(args,code=0,**kwargs):
 x=subprocess.run(args,cwd=w,capture_output=True,text=True,timeout=60,**kwargs);commands.append(dict(argv=args,exit=x.returncode,stdout=x.stdout,stderr=x.stderr));assert x.returncode==code,(args,x.stdout,x.stderr);return x
j=dict(schema='unison-helper-limits/1',work=str(w),commands=commands,parentNoFileBefore=before)
try:
 for n in ['launcher','probe','close_fixture','darwin_close_fixture']:run(['clang','-std=c11','-D_DEFAULT_SOURCE','-D_DARWIN_C_SOURCE','-Wall','-Wextra','-Werror','-O2',n+'.c','-o',n])
 run([str(w/'close_fixture')])
 run([str(w/'darwin_close_fixture'),str(w/'probe'),str(w/'close-error-target')])
 assert not (w/'close-error-target').exists()
 # Private old-behavior participant must fail each designated new oracle.
 old=(w/'launcher.c').read_text().replace(
  'if(close(fds[i].proc_fd)) {int saved=errno;free(fds);errno=saved;return -1;}',
  '(void)close(fds[i].proc_fd);').replace(
  'before.rlim_max>65536','before.rlim_max>INT_MAX').replace(
  'if(close(fd) && errno!=EBADF)return -1;','(void)close(fd);')
 assert old!=(w/'launcher.c').read_text()
 regression=w/'old-behavior';regression.mkdir();(regression/'launcher.c').write_text(old)
 j['oldBehaviorSourceSha256']=hashlib.sha256(old.encode()).hexdigest()
 for name in ['close_fixture','darwin_close_fixture']:
  shutil.copyfile(w/(name+'.c'),regression/(name+'.c'))
  run(['clang','-std=c11','-D_DEFAULT_SOURCE','-D_DARWIN_C_SOURCE','-Wall','-Wextra','-Werror','-O2',str(regression/(name+'.c')),'-o',str(regression/name)])
 run([str(regression/'close_fixture')],code=1)
 run([str(regression/'darwin_close_fixture'),str(w/'probe'),str(w/'old-close-error-target')],code=2 if os.uname().sysname=='Darwin' else 0)
 assert not (w/'old-close-error-target').exists()
 for s in sources:
  if s.startswith('src/'):run([a.compiler,'-I','+unix','-c',pathlib.Path(s).name])
 run([a.compiler,'-I','+unix','unix.cmxa','lwt.cmx','pqueue.cmx','lwt_unix_impl.cmx','lwt_unix.cmx','borrowedWork.cmx','helperSupervisor.cmx','helperSupervisor_stubs.o','test.ml','-o','test'])
 x=run([str(w/'test'),str(w/'launcher'),str(w/'probe')]);print(x.stdout,end='')
 # The direct launcher must close an explicitly inherited high descriptor.
 fd=os.open('/dev/null',os.O_RDONLY);os.dup2(fd,200);os.close(fd)
 try:
  x=run([str(w/'launcher'),'--unison-helper-limits-v1','12','0','--',str(w/'probe'),'probe','inherit','200'],pass_fds=(200,));assert 'INHERIT -1 ERR 9' in x.stdout
 finally:os.close(200)
 # Malformed version/numeric requests must never enter the target.
 for descriptors,address in [('0','0'),('2','0'),('-1','0'),('012','0'),('x','0'),('12','-1'),('12','18446744073709551616')]:
  run([str(w/'launcher'),'--unison-helper-limits-v1',descriptors,address,'--',str(w/'probe'),'probe','marker',str(w/'invalid-target')],code=125)
  assert not (w/'invalid-target').exists()
 # A rejected OS address-space request must never enter the target.
 marker=w/'not-invoked';x=subprocess.run([str(w/'launcher'),'--unison-helper-limits-v1','0','67108864','--',str(w/'probe'),'probe','marker',str(marker)],capture_output=True,text=True,timeout=10)
 j['addressSpaceProbe']=dict(exit=x.returncode,stdout=x.stdout,stderr=x.stderr,targetEntered=marker.exists())
 if x.returncode:assert x.returncode==125 and not marker.exists()
 assert resource.getrlimit(resource.RLIMIT_NOFILE)==before
 j.update(status='passed',sourcePins={s:hashlib.sha256((r/s).read_bytes()).hexdigest() for s in sources},compiler=a.compiler,compilerVersion=run([a.compiler,'-version']).stdout.strip(),parentNoFileAfter=resource.getrlimit(resource.RLIMIT_NOFILE))
finally:
 j.setdefault('status','failed');a.receipt.write_text(json.dumps(j,indent=2)+'\n');(w/'RESULT.json').write_text(json.dumps(j,indent=2)+'\n')
