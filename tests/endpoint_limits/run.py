"""Actual stock/Ox endpoint CLI under opt-in hard per-process FD limits."""
import argparse,hashlib,json,os,resource,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
paths=[ROOT/'tools/helper-limits/launcher.c',ROOT/'tests/endpoint_limits/exec_probe.c',Path(__file__).resolve()];pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
work=Path(tempfile.mkdtemp(prefix='unison-endpoint-fd-'));calls=[];before=resource.getrlimit(resource.RLIMIT_NOFILE)
def call(argv,env=None,expected=0):
 c=subprocess.run(argv,cwd=work,env=env,capture_output=True,text=True,timeout=180);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
 if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
 return c
for name,source in [('launcher',paths[0]),('probe',paths[1])]:call(['clang','-std=c11','-D_DEFAULT_SOURCE','-D_DARWIN_C_SOURCE','-Wall','-Wextra','-Werror','-O2',str(source),'-o',str(work/name)])
rows=[]
for index,receipt in enumerate(a.receipt):
 r=json.loads(Path(receipt).read_text());binary=Path(r['binary']) if 'binary' in r else Path(r['workspace'])/'src/unison'
 assert binary.is_file(),binary
 state=work/('state-'+str(index));state.mkdir(mode=0o700)
 argv=[str(work/'launcher'),'--unison-endpoint-limits-v1','96','0','--',str(work/'probe'),'endpoint-probe','96',str(binary),str(binary),'-ui','text','-selftest','-semanticworkers','3','-adobevalidate','off']
 c=call(argv,env=dict(os.environ,UNISON=str(state)))
 assert 'soft=96 hard=96 opens=93 EMFILE=true raiseDenied=true' in c.stdout
 rows.append(dict(compiler=r['compiler'],binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),oracle=True,selftests_exit=0))
# A requested RSS ceiling must never be quietly ignored or called RLIMIT_AS.
marker=work/'rss-must-not-enter'
c=call([str(work/'launcher'),'--unison-endpoint-limits-v1','96','67108864','--','/usr/bin/touch','touch',str(marker)],expected=125)
assert not marker.exists() and 'hard endpoint RSS containment unavailable' in c.stderr
assert resource.getrlimit(resource.RLIMIT_NOFILE)==before
assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with Path(a.report).open('x') as f:json.dump(dict(scope='Opt-in endpoint per-process hard FD96, actual CLI+selftests, no aggregate descendant/RSS cap; hard RSS requests refuse before exec. No Photo/SDK/camera payload.',sources=pins,work=str(work),calls=calls,endpoints=rows,parent_limits_unchanged=True,launcher_sha256=hashlib.sha256((work/'launcher').read_bytes()).hexdigest()),f,indent=2)
print('PASS stock/Ox full CLI+selftests under hard endpoint FD96, RSS refusal')
