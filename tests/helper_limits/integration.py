#!/usr/bin/env python3
"""Fail-closed limiter pin checks through actual receiving lifecycle."""
import argparse,pathlib,tempfile,importlib.util,json,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('--unison',required=True);p.add_argument('--launcher',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('receive',r/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.ADMISSION_OPTIONS[:]=['-semanticvolumejobs','1'];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-helper-limit-pins-')).resolve();cases=[];template=v.DRIVER
j=dict(schema='unison-helper-limiter-pins/1',work=str(w),binary=a.unison,cases=cases)
try:
 for fault in ['pin','mutation','invalid-limit']:
  for policy in ['require','warn']:
   name=fault+'-'+policy;limiter=w/(name+'-limiter');shutil.copyfile(a.launcher,limiter);limiter.chmod(0o700)
   v.HELPER_CONFIG.clear();v.HELPER_CONFIG.update(helperlimiter=str(limiter),helperlimiterhash=v.sha(limiter.read_bytes()),helperdescriptors='64')
   if fault=='pin':v.HELPER_CONFIG['helperlimiterhash']='0'*64
   if fault=='invalid-limit':v.HELPER_CONFIG['helperdescriptors']='2'
   v.DRIVER=template
   if fault=='mutation':
    anchor="print('UNISON-DNG-VALIDATION 1')"
    assert template.count(anchor)==1
    v.DRIVER=template.replace(anchor,"with pathlib.Path("+repr(str(limiter))+").open('ab') as changed:changed.write(b'private limiter mutation')\n"+anchor)
   s=v.Session(w/name,a.unison);old=b'original synthetic .dng receiver bytes';new=b'new synthetic .dng sender bytes'
   (s.left/'image.dng').write_bytes(old);s.sync(policy='off')
   (s.left/'image.dng').write_bytes(new);log=s.sync(policy=policy,success=False)
   assert (s.left/'image.dng').read_bytes()==new and (s.right/'image.dng').read_bytes()==old
   assert len(s.calls())==(1 if fault=='mutation' else 0)
   if fault=='mutation':assert 'Helper limiter changed during execution' in log,log
   if fault=='pin':assert 'Helper limiter executable pin mismatch' in log,log
   cases.append(dict(name=name,status='passed',validatorCalls=len(s.calls()),liveInputPreserved=True,log=str(s.root/'run-02.log')));print('PASS',name,flush=True)
 j['status']='passed'
finally:
 j.setdefault('status','failed');j['sourcePins']={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__),r/'tests/validation_paths/run.py']};a.receipt.write_text(json.dumps(j,indent=2)+'\n');(w/'RESULT.json').write_text(json.dumps(j,indent=2)+'\n')
