"""Link actual compiled receiving companion; generated tiny input/fake helpers only."""
import argparse,hashlib,json,os,pathlib,re,subprocess,sys,tempfile
root=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tests/camera_sdk_concurrency'))
sys.path.insert(0,str(root/'tests/validation_process'))
import live_records,records
p=argparse.ArgumentParser();p.add_argument('--build-result',type=pathlib.Path,required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads(a.build_result.read_text());src=pathlib.Path(b['workspace'])/'src';assert h(pathlib.Path(b['compiler']))==b['compiler_sha256']
for name,digest in b['source_sha256'].items():assert h(root/name)==digest,name
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-live-companion-'));print(w,flush=True)
def objects(name):
 s=re.search(r'^'+name+r' = (.*?)(?=\n\n)',(src/'Makefile.OCaml').read_text(),re.M|re.S).group(1)
 return s.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
mods=objects('OCAMLOBJS');mods=mods[:mods.index('dngCandidateValidation.cmx')+1]
flags=[str(y) for x in (src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic') for y in ('-I',x)]+['-I','+unix','-I','+str']
(w/'companion.ml').write_bytes((root/'tests/validation_live/companion.ml').read_bytes())
exe=w/'control';cmd=[b['compiler'],*flags,'unix.cmxa','str.cmxa',*[str(src/m) for m in mods],str(w/'companion.ml'),*[str(src/n) for n in objects('COBJS')],'-o',str(exe)]
r=subprocess.run(cmd,cwd=w,capture_output=True,text=True,timeout=30);(w/'build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
helper=w/'helper.py'
helper.write_text('#!'+sys.executable+'\n'+'''import sys,time,pathlib,hashlib,os
args=sys.argv;candidate=pathlib.Path(args[-1]);data=candidate.read_bytes()
with pathlib.Path('helper.calls').open('x') as f:f.write(str(os.getpid())+'\\n')
time.sleep(.12)
errors=1 if pathlib.Path('mode').read_text()=='error' else 0
print('UNISON-DNG-VALIDATION 1\\ncandidate-sha256 '+hashlib.sha256(data).hexdigest()+'\\ncandidate-size '+str(len(data))+'\\ndriver-build synthetic-live-1\\nstructure valid\\ndecode success\\nraw-digest valid\\nerrors '+str(errors)+'\\nwarnings 0\\nEND')
''');helper.chmod(0o700)
runs=[]
for mode in ['pass','error','silent','off']:
 d=w/mode;d.mkdir(mode=0o700);(d/'candidate.dng').write_bytes(b'original tiny synthetic candidate\0'*32);(d/'mode').write_text(mode)
 env=dict(os.environ,UNISON=str(d/'state'))
 child=subprocess.Popen([str(exe),mode,str(helper)],cwd=d,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 output=child.communicate(timeout=15)[0].decode();(d/'output.log').write_text(output);assert child.returncode==0,output
 live=live_records.parse(output);groups=records.parse_groups(output)
 if mode in ['pass','error']:
  assert len(live)==1 and len(groups)==1 and groups[0].other_members==0,output
  pid=int((d/'helper.calls').read_text());candidate=d/'candidate.dng'
  span=live_records.bound(live[0],endpoint='client',owner_pid=child.pid,helper_pid=pid,candidate_sha256=h(candidate),candidate_bytes=candidate.stat().st_size)
  assert live[0].samples>=2
 else:assert not live,output
 assert len(groups)==(0 if mode=='off' else 1)
 if mode!='off':
  assert groups[0].pid==int((d/'helper.calls').read_text()) and groups[0].candidate_sha256==h(d/'candidate.dng') and groups[0].other_members==0
 runs.append({'mode':mode,'owner_pid':child.pid,'owner_exit':child.returncode,'live_records':len(live),'groups':len(groups),'output':str(d/'output.log'),'output_sha256':h(d/'output.log')})
a.report.write_text(json.dumps({'passed':True,'workspace':str(w),'runs':runs,'build_result_sha256':h(a.build_result),'linked_objects':{str(src/n):h(src/n) for n in mods+objects('COBJS')},'helper_sha256':h(helper),'sources':{str(p):h(p) for p in [root/'tests/validation_live/companion.ml',pathlib.Path(__file__),root/'tests/camera_sdk_concurrency/live_records.py']},'scope':'actual compiled receiving companion with4tiny synthetic/fake-validator cases; no SDK/Photo/camera/EXglobal/CLI sync'},indent=2)+'\n')
print('PASS4 receiving companion trace cases; actual records bound; direct helpers reaped',flush=True)
