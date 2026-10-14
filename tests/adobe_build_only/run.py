#!/usr/bin/env python3
"""Original filesystem/build-denial controls; no SDK compilation or execution."""
import fcntl,hashlib,json,pathlib,subprocess,sys,tempfile
root=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-experimental-build-guard-',dir='/private/tmp'));script=root/'tools/adobe-validator/experimental_build.py';records=[]
for case in ['qualified','unowned','busy']:
 build=w/case;build.mkdir();(build/'preserved').write_bytes(b'original retained bytes')
 if case=='qualified':(build/'build-manifest.json').write_text('original qualified manifest')
 if case=='busy':
  (build/'.unison-experimental-area-memory-owner.json').write_text(json.dumps({'schema':1,'sdk_root':str(w/'unused-sdk'),'mode':'area-memory-unqualified'}))
  lock=(build/'.build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before={str(p):p.read_bytes() for p in build.iterdir()}
 r=subprocess.run([sys.executable,str(script),'--sdk-root',str(w/'unused-sdk'),'--build-dir',str(build)],capture_output=True,text=True,timeout=5)
 if case=='busy':lock.close()
 assert r.returncode!=0 and 'Building bundled' not in r.stdout
 expected={'qualified':'qualified v1 build directory refused','unowned':'fresh directory','busy':'BlockingIOError'}[case]
 assert expected in r.stderr,r.stderr
 assert {str(p):p.read_bytes() for p in build.iterdir()}==before
 (w/(case+'.log')).write_text(r.stdout+r.stderr);records.append({'case':case,'exit':r.returncode,'status':'passed'})
receipt={'scope':'three local denial controls; no builder/SDK invoked','workspace':str(w),'cases':records,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest()}
(w/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
