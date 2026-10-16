#!/usr/bin/env python3
"""Current merge -> unmodified old peer -> current merge, private archives only."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt',type=Path,required=True)
p.add_argument('--baseline',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
build=json.loads(a.build_receipt.read_text());binary=Path(build['binary']).resolve();baseline=a.baseline.resolve()
assert build['complete'] and build['build_exit']==build['selftest_exit']==0
assert sha(binary)==build['binary_sha256']
for name,digest in build['source_sha256'].items():
 if name.startswith('src/'):assert sha(ROOT/name)==digest,name
baseline_sha=sha(baseline)
spec=importlib.util.spec_from_file_location('paths',ROOT/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.ADMISSION_OPTIONS[:]=['-semanticvolumejobs','1']
work=Path(tempfile.mkdtemp(prefix='unison-archive-downgrade-')).resolve()
s=v.Session(work/'roundtrip',str(binary))
# Both generations use exactly the same logical roots, hostname, state and
# transport. Only the executable changes. No archive is deleted or regenerated.
s.launcher.write_text('#!/usr/bin/python3\nimport os,sys\na=sys.argv[1:]\ni=a.index("-server")-1\nassert a[i] in '+repr([str(binary),str(baseline)])+'\nos.environ["UNISON"]='+repr(str(s.server_state))+'\nos.execv(a[i],a[i:])\n')

def fixture(rating='1',label='Blue'):
 data=bytearray(bytes((i*71+19)%256 for i in range(65536)))
 struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
 for i,entry in enumerate([(273,4,1,12288),(279,4,1,len(data)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',data,10+12*i,*entry)
 struct.pack_into('<I',data,58,0)
 packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"/></rdf:RDF>').encode()
 data[1024:9216]=packet+b' '*(8192-len(packet));return bytes(data)

options=('-semanticdng','-semanticmergebasecache','-merge','Name *.dng -> unison:dng-xmp-scalars/0')
stages=[]
def inventory():
 return {endpoint:{f.name:sha(f) for f in state.iterdir() if f.is_file() and f.name.startswith('ar')}
         for endpoint,state in [('client',s.client_state),('server',s.server_state)]}
def verify(expected):
 assert (s.left/'image.dng').read_bytes()==(s.right/'image.dng').read_bytes()==expected

def current(name,expected,merge=False):
 log=s.sync(policy='off',options=options);verify(expected)
 assert ('Built-in DNG scalar merge verified' in log)==merge,log
 assert not s.calls('client') and not s.calls('server')
 stages.append({'name':name,'archive_inventory':inventory(),'output_sha256':hashlib.sha256(expected).hexdigest(),'log':str(s.root/f'run-{s.sequence:02d}.log')})

def old(name,expected,noop=False):
 before=inventory();assert all(before.values()),before
 inode=(s.right/'image.dng').stat().st_ino
 argv=[str(baseline),str(s.left),'ssh://localhost/'+str(s.right),'-sshcmd',str(s.launcher),
       '-servercmd',str(baseline),'-batch','-auto','-fastcheck','false','-debug','archive']
 result=subprocess.run(argv,env=dict(os.environ,UNISON=str(s.client_state)),capture_output=True,text=True,timeout=60)
 log=s.root/(name+'.log');log.write_text(result.stdout+result.stderr)
 assert result.returncode==0,log.read_text()
 verify(expected);after=inventory();assert all(after.values())
 # A rescan/rebuild would hide archive incompatibility; require normal loading
 # and the no-op to leave receiver content/inode and archive names intact.
 # Archive bytes may change for normal format/property bookkeeping.
 text=log.read_text().lower()
 assert 'no archive files were found' not in text and 'archive format mismatch' not in text,text
 assert {k:set(v) for k,v in before.items()}=={k:set(v) for k,v in after.items()}
 if noop:assert (s.right/'image.dng').stat().st_ino==inode
 stages.append({'name':name,'command':argv,'exit':result.returncode,'log':str(log),
                'archive_before':before,'archive_after':after,'output_sha256':hashlib.sha256(expected).hexdigest()})

receipt={'schema':'unison-archive-downgrade/1','workspace':str(work),'build_receipt':str(a.build_receipt),
 'build_receipt_sha256':sha(a.build_receipt),'binary':str(binary),'binary_sha256':sha(binary),
 'baseline':str(baseline),'baseline_sha256':baseline_sha,'stages':stages,'complete':False,
 'scope':'Private synthetic current scalar merge/compact bases -> baseline archive load/update -> current merge. No SDK, photos, catalog or production archives.'}
print('Workspace:',work,flush=True)
try:
 (s.left/'image.dng').write_bytes(fixture());current('seed',fixture())
 (s.left/'image.dng').write_bytes(fixture('2'));(s.right/'image.dng').write_bytes(fixture(label='Gold'))
 current('current-merge-before-downgrade',fixture('2','Gold'),merge=True)
 old('baseline-noop',fixture('2','Gold'),noop=True)
 (s.left/'image.dng').write_bytes(fixture('3','Gold'))
 old('baseline-update',fixture('3','Gold'))
 current('current-reopen',fixture('3','Gold'))
 (s.left/'image.dng').write_bytes(fixture('4','Gold'));(s.right/'image.dng').write_bytes(fixture('3','Rose'))
 log=s.sync(policy='off',options=options,success=False)
 assert 'no saved common base is available' in log and 'Uncaught unix error' not in log
 assert (s.left/'image.dng').read_bytes()==fixture('4','Gold')
 assert (s.right/'image.dng').read_bytes()==fixture('3','Rose')
 stages.append({'name':'missing-baseline-era-base-refused','log':str(s.root/f'run-{s.sequence:02d}.log'),'both_edits_preserved':True})
 # Explicitly restore the known common synthetic version, then propagate a new
 # one-sided current-version edit. Never infer a base from conflicting edits.
 (s.left/'image.dng').write_bytes(fixture('3','Gold'));(s.right/'image.dng').write_bytes(fixture('3','Gold'))
 current('restore-known-common-fixture',fixture('3','Gold'))
 (s.left/'image.dng').write_bytes(fixture('4','Gold'))
 current('current-captured-common-update',fixture('4','Gold'))
 (s.left/'image.dng').write_bytes(fixture('5','Gold'));(s.right/'image.dng').write_bytes(fixture('4','Rose'))
 current('current-merge-after-baseline',fixture('5','Rose'),merge=True)
 current('current-final-noop',fixture('5','Rose'))
 assert sha(binary)==build['binary_sha256'] and sha(baseline)==baseline_sha
 receipt['complete']=True
finally:
 receipt['runner_sha256']=sha(__file__)
 a.report.write_text(json.dumps(receipt,indent=2)+'\n');(work/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('PASS',len(stages),'archive round-trip stages',flush=True)
