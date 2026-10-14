#!/usr/bin/env python3
"""Actual core resource declarations via a compiled non-Adobe backend."""
import argparse,pathlib,subprocess,tempfile,importlib.util,hashlib,json,os,re
p=argparse.ArgumentParser();p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);p.add_argument('--activation-negative',action='store_true');a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];src=a.build.resolve()/'src';w=pathlib.Path(tempfile.mkdtemp(prefix='unison-backend-resources-')).resolve();commands=[];cases=[]
spec=importlib.util.spec_from_file_location('receive',r/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def objects(name):
 text=(src/'Makefile.OCaml').read_text();m=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S);assert m
 return m.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
def run(args,label):
 x=subprocess.run(list(map(str,args)),cwd=w,capture_output=True,text=True,timeout=120);log=w/(label+'.log');log.write_text(x.stdout+x.stderr);commands.append(dict(args=list(map(str,args)),exit=x.returncode,log=str(log),sha256=H(log)));assert x.returncode==0,x.stdout+x.stderr
j=dict(schema='unison-backend-resource-admission/1',work=str(w),commands=commands,cases=cases)
try:
 (w/'genericValidator.ml').write_bytes((r/'tests/backend_resources/plugin.ml').read_bytes())
 inc=[w,src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic'];flags=[str(v) for x in inc for v in ['-I',x]]+['-I','+unix','-I','+str']
 run([a.compiler,*flags,'-c','genericValidator.ml'],'plugin-compile')
 mods=objects('OCAMLOBJS');objs=[]
 for m in mods:
  if m=='main.cmx':objs.append(w/'genericValidator.cmx')
  objs.append(src/m)
 binary=w/'unison';run([a.compiler,*flags,'unix.cmxa','str.cmxa',*objs,src/'linktext.cmx',*[src/n for n in objects('COBJS')],'-o',binary],'plugin-link')
 (w/'controls.ml').write_bytes((r/'tests/backend_resources/controls.ml').read_bytes())
 run([a.compiler,*flags,'-c','controls.ml'],'controls-compile')
 control=w/'controls';run([a.compiler,*flags,'unix.cmxa','str.cmxa',*[src/m for m in mods if m!='main.cmx'],w/'controls.cmx',*[src/n for n in objects('COBJS')],'-o',control],'controls-link')
 run([control],'resource-controls')
 if a.activation_negative:
  negative=w/'negative';negative.mkdir()
  (negative/'candidateValidator.mli').write_bytes((src/'candidateValidator.mli').read_bytes())
  old=subprocess.check_output(['git','show','4717a6c:src/candidateValidator.ml'],cwd=r)
  (negative/'candidateValidator.ml').write_bytes(old)
  (negative/'activation_negative.ml').write_bytes((r/'tests/backend_resources/activation_negative.ml').read_bytes())
  nf=['-I',str(negative),*flags]
  for suffix in ['mli','ml']:run([a.compiler,*nf,'-c',negative/('candidateValidator.'+suffix)],'negative-validator-'+suffix)
  run([a.compiler,*nf,'-c',negative/'activation_negative.ml'],'negative-oracle-compile')
  before=mods[:mods.index('candidateValidator.cmx')]
  (w/'activation_positive.ml').write_bytes((r/'tests/backend_resources/activation_negative.ml').read_bytes())
  run([a.compiler,*flags,'-c',w/'activation_positive.ml'],'positive-oracle-compile')
  pb=w/'activation-positive';run([a.compiler,*flags,'unix.cmxa','str.cmxa',*[src/m for m in before],src/'candidateValidator.cmx',w/'activation_positive.cmx',*[src/n for n in objects('COBJS')],'-o',pb],'positive-oracle-link')
  run([pb],'positive-activation-oracle')
  nb=negative/'activation';run([a.compiler,*nf,'unix.cmxa','str.cmxa',*[src/m for m in before],negative/'candidateValidator.cmx',negative/'activation_negative.cmx',*[src/n for n in objects('COBJS')],'-o',nb],'negative-link')
  x=subprocess.run([nb],cwd=negative,capture_output=True,text=True,timeout=30);log=negative/'result.log';log.write_text(x.stdout+x.stderr)
  assert x.returncode==2 and 'DESIGNATED late resource backend accepted without reserved workspace' in log.read_text()
  j['activationNegative']=dict(parent='4717a6c',participantSha256=hashlib.sha256(old).hexdigest(),binarySha256=H(nb),exit=x.returncode,log=str(log),logSha256=H(log),scope='Exact previous CandidateValidator implementation only, other prefix objects current; independently rejected by late-activation oracle.')
 for name,memory,lanes,succeeds in [('fits',4,1,True),('memory-too-large',32,1,False),('cpu-too-large',4,3,False)]:
  s=v.Session(w/name,str(binary));serverlog=s.root/'server.tsv';clientlog=s.root/'client.tsv'
  cfg=dict(s.config('server'),testvalidatorlog=str(serverlog),testbackendmemory=str(memory),testbackendlanes=str(lanes));(s.server_state/'endpoint.prf').write_text(''.join(f'{k} = {x}\n' for k,x in cfg.items()))
  data=b'TOY0 independent backend memory declaration fixture';(s.left/'image.toy').write_bytes(data)
  options=('-testvalidatorlog',str(clientlog),'-testbackendmemory',str(memory),'-testbackendlanes',str(lanes),'-semanticpayloadbudget','32','-semanticdescriptorbudget','64','-semanticvolumejobs','1')
  log=s.sync(policy='off',options=options,success=succeeds)
  if succeeds:
   assert (s.right/'image.toy').read_bytes()==data
   rows=[line.split('\t') for line in serverlog.read_text().splitlines()];assert len(rows)==1
   record=rows[0];assert list(map(int,record[4:7]))==[4*1048576,1,2]
   # No semantic format is enabled here: publication uses its 1 MiB floor
   # plus the backend's 4 MiB declaration, retained through validation.
   assert int(record[7])==5*1048576 and int(record[8])==26,record
   cases.append(dict(name=name,status='passed',backendBytes=4*1048576,envelopeBytes=int(record[7]),envelopeDescriptors=int(record[8]),doubleDebit=False))
  else:
   assert not (s.right/'image.toy').exists() and not serverlog.exists()
   assert not list(s.right.glob('.unison*')),'rejected plan created staging'
   assert 'resource budget' in log if memory==32 else 'CPU declaration' in log
   cases.append(dict(name=name,status='passed',rejectedBeforeStage=True))
  assert not s.calls('client') and not s.calls('server');print('PASS',name,flush=True)
 s=v.Session(w/'manifest-partition',str(binary));logpath=s.root/'server.tsv'
 cfg=dict(s.config('server'),testvalidatorlog=str(logpath),testbackendmemory='4',testbackendlanes='1',validationtreememory='1')
 (s.server_state/'endpoint.prf').write_text(''.join(f'{k} = {value}\n' for k,value in cfg.items()))
 album=s.left/'album';album.mkdir();expected={}
 for n in range(6):
  data=b'TOY0 directory parent/child admission fixture '+bytes([n]);name=f'item-{n}.toy';(album/name).write_bytes(data);expected[name]=data
 s.sync(policy='off',options=('-validationtreememory','1','-semanticmaxinflight','1','-semanticdng=false','-semanticpayloadbudget','32','-semanticdescriptorbudget','64'))
 rows=[line.split('\t') for line in logpath.read_text().splitlines()];assert len(rows)==6
 for row in rows:assert list(map(int,row[7:10]))==[12*1048576,37,1],row
 assert {p.name:p.read_bytes() for p in (s.right/'album').iterdir()}==expected
 assert {p.name:p.read_bytes() for p in album.iterdir()}==expected
 assert not s.calls('client') and not s.calls('server')
 cases.append(dict(name='manifest-partition',status='passed',files=6,globalTransactions=1,envelopeBytes=12*1048576,envelopeDescriptors=37,maximumGlobalTransactions=1,childDoubleDebit=False));print('PASS manifest-partition',flush=True)
 s=v.Session(w/'nested-backend-partition',str(binary));logpath=s.root/'server.tsv'
 cfg=dict(s.config('server'),testvalidatorlog=str(logpath),testvalidatormode='hold-cpu',testbackendmemory='4',testbackendlanes='2',validationtreememory='1')
 (s.server_state/'endpoint.prf').write_text(''.join(f'{k} = {value}\n' for k,value in cfg.items()))
 album=s.left/'album';album.mkdir();expected={}
 for n in range(6):
  data=b'TOY0 nested backend caller-inclusive CPU fixture '+bytes([n]);name=f'item-{n}.toy';(album/name).write_bytes(data);expected[name]=data
 s.sync(policy='off',options=('-validationtreememory','1','-semanticmaxinflight','1','-semanticdng=false','-semanticpayloadbudget','8','-semanticdescriptorbudget','64'))
 rows=[line.split('\t') for line in logpath.read_text().splitlines()];assert len(rows)==6
 for row in rows:assert list(map(int,row[4:10]))==[4*1048576,2,2,7*1048576,26,1],row
 assert {p.name:p.read_bytes() for p in (s.right/'album').iterdir()}==expected
 assert {p.name:p.read_bytes() for p in album.iterdir()}==expected
 cases.append(dict(name='nested-backend-partition',status='passed',files=6,cpuBudget=2,backendLanes=2,workspaces=1,envelopeBytes=7*1048576,envelopeDescriptors=26,configuredBytes=8*1048576,allDeclaredCpuPermitsHeld=True,scope='Synthetic permit ownership, not SDK threading/CPU utilization.'))
 print('PASS nested-backend-partition',flush=True)
 for f in ['backendResources.ml','backendResources.mli','candidateValidator.ml','candidateValidator.mli','candidateValidators.ml','candidateValidators.mli','candidateValidation.ml','semanticRuntime.ml','semanticRuntime.mli','validationTreeBudget.ml','validationTreeBudget.mli','validationTreePolicy.ml','validationTreePolicy.mli']:
  assert H(src/f)==H(r/'src'/f),('source drift',f)
 j.update(status='passed',binarySha256=H(binary),sourcePins={f:H(r/f) for f in ['tests/backend_resources/plugin.ml','tests/backend_resources/controls.ml','tests/backend_resources/activation_negative.ml','tests/backend_resources/run.py','tests/validation_paths/run.py']},compiledSourcePins={str(x):H(src/x) for x in mods if (src/x).is_file()},scope='Actual CLI compiled-object registration/core memory admission, synthetic TOY0 backend. Accounting declarations, not SDK enforcement/RSS; no Adobe/Photo/native preview work.')
finally:
 j.setdefault('status','failed');a.receipt.write_text(json.dumps(j,indent=2)+'\n');(w/'RESULT.json').write_text(json.dumps(j,indent=2)+'\n')
