#!/usr/bin/env python3
"""Actual external-copy status/limit publication fences with private roots."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('validation_path_fixtures',ROOT/'tests/validation_paths/run.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
COPY=r'''#!/usr/bin/python3
import hashlib,json,os,pathlib,signal,sys,time
here=pathlib.Path(__file__)
mode=here.with_suffix('.mode').read_text()
def local(value):
 if value.startswith('localhost:'):value=value[len('localhost:'):]
 p=pathlib.Path(value);assert p.is_absolute() and p.is_relative_to(here.parent);return p
source,target=map(local,sys.argv[1:]);data=source.read_bytes();target.write_bytes(data)
here.with_suffix('.copy-proof.json').write_text(json.dumps({'pid':os.getpid(),'candidate':str(target),'source_sha256':hashlib.sha256(data).hexdigest(),'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':len(data),'mode':mode}))
if mode=='hang':
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 while True:time.sleep(.01)
if mode=='flood':
 for i in range(129):sys.stdout.write('x'*16384);sys.stdout.flush()
sys.exit(7 if mode=='exit7' else 0)
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--unison',type=Path,required=True);ap.add_argument('--parent',type=Path)
 ap.add_argument('--receipt',type=Path,required=True);args=ap.parse_args()
 work=Path(tempfile.mkdtemp(prefix='unison-supervised-copy-status-',dir='/private/tmp'))
 receipt={'schema':1,'success':False,'work':str(work),'binary':str(args.unison.resolve()),
  'binary_sha256':sha(args.unison.resolve()),'runner_sha256':sha(Path(__file__)),
  'fixture_dependency_sha256':sha(ROOT/'tests/validation_paths/run.py'),'cases':[],
  'scope':'Actual local-exec remote Unison external copy; synthetic fully written candidate; no Adobe/Photo/UI',
  'Adobe_or_Photo_or_UI_access':False}
 try:
  participants=[('fixed',str(args.unison.resolve()))]+([('parent',str(args.parent.resolve()))] if args.parent else [])
  for label,binary in participants:
   for mode in ('pass','exit7','hang','flood') if label=='fixed' else ('exit7',):
    root=work/(label+'-'+mode);session=base.Session(root,binary)
    session.copy.write_text(COPY);session.copy.chmod(0o700);session.copy.with_suffix('.mode').write_text(mode)
    name='image.bin';old=b'independent existing sibling bytes';new=b'independent new source bytes'*128
    session.control('sentinel.bin');(session.left/'sentinel.bin').write_bytes(old);session.sync(policy='off')
    session.control(name)
    (session.left/name).write_bytes(new)
    options=['-copythreshold','0','-copyprog',str(session.copy),'-copyprogrest',str(session.copy),'-xferbycopying=false']
    if label=='fixed':options+=['-externalhelpertimeout','1','-externalhelperoutput','1']
    argv=session.command(policy='off',options=options)
    result=subprocess.run(argv,env=dict(os.environ,UNISON=str(session.client_state)),text=True,
      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20)
    log=root/'receive.log';log.write_text(result.stdout)
    proof=json.loads(session.copy.with_suffix('.copy-proof.json').read_text())
    assert proof['source_sha256']==proof['candidate_sha256']==hashlib.sha256(new).hexdigest()
    assert proof['size']==len(new) and (session.left/name).read_bytes()==new
    accepted=label=='parent' or mode=='pass'
    assert (result.returncode==0)==accepted,result.stdout
    assert (session.right/'sentinel.bin').read_bytes()==old, 'external copy changed existing sibling'
    if accepted:assert (session.right/name).read_bytes()==new
    else:assert not (session.right/name).exists(), 'failed external copy was published'
    try:os.kill(proof['pid'],0)
    except ProcessLookupError:pass
    else:raise AssertionError('external copy child still alive after CLI return')
    receipt['cases'].append({'participant':label,'mode':mode,'argv':argv,'exit':result.returncode,
      'log':str(log),'log_sha256':sha(log),'proof':proof,'published':accepted,
      'source_preserved':True,'existing_sibling_preserved':True,'absent_destination_preserved':not accepted,'designated_negative':label=='parent'})
    print('PASS',label,mode,flush=True)
  if args.parent:receipt['parent_binary_sha256']=sha(args.parent.resolve())
  receipt['success']=True
 finally:
  args.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print('receipt',args.receipt,'work',work,flush=True)
if __name__=='__main__':main()
