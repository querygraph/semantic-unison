#!/usr/bin/env python3
"""Finite synthetic CLI read-telemetry check; Adobe disabled, no photographs."""
import argparse,hashlib,importlib.util,json,os,re,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
build=json.loads(a.build_receipt.read_text());assert build['complete'] and build['build_exit']==build['selftest_exit']==0
assert sha(build['binary'])==build['binary_sha256']
for name,digest in build['source_sha256'].items():
 if name.startswith('src/'):assert sha(root/name)==digest,name
v=module('paths',root/'tests/validation_paths/run.py');f=module('fixtures',root/'bench/sync/fixtures.py')
v.ADMISSION_OPTIONS[:]=['-semanticvolumejobs','1']
work=Path(tempfile.mkdtemp(prefix='unison-read-stats-cli-')).resolve();print('Workspace:',work,flush=True)
s=v.Session(work/'sync',build['binary']);source=s.left/'image.dng';target=s.right/'image.dng'
meta=f.create(source,2097152,8192,7)
options=('-semanticdng','-clone','auto','-debug','semantic-reads')
s.sync(policy='off',options=options);original=sha(target);basis=work/'basis.dng';os.link(target,basis)
f.edit(source,meta);log=s.sync(policy='off',options=options)
assert source.read_bytes()==target.read_bytes() and sha(basis)==original
assert 'Remote semantic clone wrote' in log,log
pattern=r'Completed semantic worker job (\d+) primary reader delivered (\d+) logical bytes in (\d+) chunks \(saturated=(true|false)\)\.'
records=[{'job':int(i),'logical_bytes':int(n),'chunks':int(c),'saturated':sat=='true'}
         for i,n,c,sat in re.findall(pattern,log)]
assert records and not any(row['saturated'] for row in records),log
assert sum(row['logical_bytes'] for row in records)>=source.stat().st_size
assert all((row['logical_bytes']==0)==(row['chunks']==0) for row in records)
inode=target.stat().st_ino;s.sync(policy='off',options=options)
assert target.stat().st_ino==inode and source.read_bytes()==target.read_bytes() and sha(basis)==original
assert not s.calls('client') and not s.calls('server')
result={'schema':'unison-logical-read-cli/1','workspace':str(work),'build_receipt':str(a.build_receipt),'build_receipt_sha256':sha(a.build_receipt),'binary_sha256':sha(build['binary']),'records':records,'logical_worker_read_bytes':sum(row['logical_bytes'] for row in records),'successful_nonempty_chunks':sum(row['chunks'] for row in records),'output_sha256':sha(target),'old_basis_sha256':original,'exact_result_basis_and_noop':True,'sdk_calls':0,'sources':{str(path.relative_to(root)):sha(path) for path in [Path(__file__).resolve(),root/'bench/sync/fixtures.py',root/'tests/validation_paths/run.py']},'logs':[{ 'path':str(path),'sha256':sha(path)} for path in s.root.glob('run-*.log')],'scope':'Completed worker primary-reader reports across client/server; excludes nested readers (including output verification), legacy/validator reads, partial/cancelled jobs, channel prefetch, syscalls and physical I/O. Not a throughput measurement.'}
a.report.write_text(json.dumps(result,indent=2)+'\n');print('PASS exact SDE update, read telemetry, old basis and no-op; worker logical bytes:',result['logical_worker_read_bytes'])
