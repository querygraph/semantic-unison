"""Bounded self-task physical-footprint observation, not RSS qualification."""
import argparse,hashlib,json,resource,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
source=Path(__file__).with_name('footprint_probe.c');work=Path(tempfile.mkdtemp(prefix='unison-self-footprint-'))
before=resource.getrlimit(resource.RLIMIT_NOFILE)
command=['clang','-std=c11','-D_DARWIN_C_SOURCE','-Wall','-Wextra','-Werror','-O2',str(source),'-o',str(work/'probe')]
c=subprocess.run(command,capture_output=True,text=True,timeout=30);assert c.returncode==0,c.stderr
runs=[]
for mode in ['baseline','self-limit']:
 c=subprocess.run([str(work/'probe'),mode],capture_output=True,text=True,timeout=15)
 rows=[json.loads(line) for line in c.stdout.splitlines()]
 if mode=='baseline':assert c.returncode==0 and any(x.get('stage')=='completed' for x in rows),(c.returncode,rows)
 runs.append({'argv':[str(work/'probe'),mode],'returncode':c.returncode,'observations':rows,'stderr':c.stderr,'direct_child_returned':True})
assert resource.getrlimit(resource.RLIMIT_NOFILE)==before
headers={}
for name in ['mach/task.h','mach/task.defs']:
 header=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include')/name
 if header.exists():headers[str(header)]={'bytes':header.stat().st_size,'sha256':hashlib.sha256(header.read_bytes()).hexdigest()}
with a.report.open('x') as f:json.dump({'scope':'Self-task API observation only; physical footprint differs from RSS and no inheritance/group enforcement is established. 32MiB maximum touched per original child. Production RSS refusal unchanged.','sources':{str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [source,Path(__file__).resolve()]},'headers':headers,'work':str(work),'build_command':command,'runs':runs,'parent_limits_unchanged':True,'binary_sha256':hashlib.sha256((work/'probe').read_bytes()).hexdigest()},f,indent=2)
print(json.dumps({'scope':'OBSERVATION_ONLY','runs':[{k:r[k] for k in ['returncode','direct_child_returned']} for r in runs]}))
