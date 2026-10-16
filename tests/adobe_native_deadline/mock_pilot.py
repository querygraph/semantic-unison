#!/usr/bin/env python3
"""Exercise the full pilot runner with original fake protocol tools, never SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--ocamlopt',required=True)
p.add_argument('--production-build',required=True,type=Path)
p.add_argument('--report',required=True,type=Path)
a=p.parse_args()
work=Path(tempfile.mkdtemp(prefix='unison-mock-pilot-',dir='/private/tmp'))
print('Workspace:',work,flush=True)
sdk=work/'original-tools';sdk.mkdir()
validator=sdk/'unison-adobe-validator'
validator.write_text('''#!/usr/bin/python3
import hashlib,json,os,pathlib,struct,sys
here=pathlib.Path(__file__).parent
with (here/'calls.jsonl').open('a') as log:log.write(json.dumps({'tool':'validator','pid':os.getpid(),'group':os.getpgrp()})+'\\n')
a=sys.argv[1:];data=pathlib.Path(a[-1]).read_bytes();count=struct.unpack_from('<H',data,8)[0]
tags={struct.unpack_from('<H',data,10+i*12)[0]:struct.unpack_from('<I',data,18+i*12)[0] for i in range(count)}
valid=hashlib.md5(data[tags[273]:]).digest()==data[tags[50972]:tags[50972]+16]
print('UNISON-DNG-VALIDATION 1');print('candidate-sha256 '+hashlib.sha256(data).hexdigest());print('candidate-size '+str(len(data)))
print('driver-build original-mock-only');print('structure valid');print('decode success')
print('raw-digest '+('valid' if valid else 'mismatch'));print('errors '+('0' if valid else '1'));print('warnings 0');print('END')
''')
writer=sdk/'fixture-writer'
writer.write_text('''#!/usr/bin/python3
import json,os,pathlib,struct,sys
here=pathlib.Path(__file__).parent
with (here/'calls.jsonl').open('a') as log:log.write(json.dumps({'tool':'writer','pid':os.getpid(),'group':os.getpgrp()})+'\\n')
data=bytearray(pathlib.Path(sys.argv[2]).read_bytes());count=struct.unpack_from('<H',data,8)[0]
for i in range(count):
 if struct.unpack_from('<H',data,10+i*12)[0]==259:struct.pack_into('<H',data,18+i*12,{'uncompressed':1,'jpeg':7,'jxl':52546}[sys.argv[1]])
pathlib.Path(sys.argv[3]).write_bytes(data)
''')
for path in (validator,writer):path.chmod(0o700)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
(sdk/'build-manifest.json').write_text(json.dumps({'sdk':'ORIGINAL-MOCK-NO-SDK','executable_sha256':sha(validator),'build_id':'original-mock-only','source_sha256':sha(validator),'threads':1,'qualification':'passed original protocol mock only; NOT SDK qualification'}))
output=work/'pilot.json'
command=['python3',str(root/'bench/adobe/run.py'),'--sdk-build',str(sdk),'--ocamlopt',a.ocamlopt,'--production-build',str(a.production_build),'--pilot','--workers','1','--cpu-credit-budget','1','--output',str(output)]
with (work/'log').open('w') as log:
 result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=320)
assert result.returncode==0,(work/'log').read_text()
receipt=json.loads(output.read_text());assert receipt['complete']
calls=[json.loads(row) for row in (sdk/'calls.jsonl').read_text().splitlines()]
assert len(calls)==13 and sum(row['tool']=='writer' for row in calls)==3
closure=receipt['aggregate_lifecycle']
assert closure['closed'] and closure['reaped'] and closure['other_members_absent'] and closure['wall_seconds']<300
assert all(row['group']==closure['pid'] for row in calls)
assert len(receipt['samples'])==3 and all(row['correct_receipts']==1 for row in receipt['samples'])
a.report.write_text(json.dumps({'scope':'original fake protocol tools; no SDK or real JPEG/JXL decoding','workspace':str(work),'calls':calls,'aggregate':closure,'runner_receipt':receipt},indent=2)+'\n')
print('PASS full synthetic runner:13 calls, one owned group, true closure',flush=True)
