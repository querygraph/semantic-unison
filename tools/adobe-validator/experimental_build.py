#!/usr/bin/env python3
"""Build/static-inspect only. Never execute a validator or fixture writer."""
import argparse,fcntl,hashlib,json,os,pathlib,subprocess,sys,tempfile
HERE=pathlib.Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inspect(build):
 manifest=build/'build-manifest-area-memory-unqualified.json'
 m=json.loads(manifest.read_text());binary=pathlib.Path(m['executable'])
 if m['build_id']!='unison-sdk171-2724-v3-area-memory-unqualified' or binary.parent!=build or sha(binary)!=m['executable_sha256']:
  raise RuntimeError('experimental artifact binding mismatch')
 for name,digest in m['adapter_headers_sha256'].items():
  if sha(HERE/name)!=digest:raise RuntimeError('adapter source changed: '+name)
 if sha(HERE/'driver.cpp')!=m['source_sha256']:raise RuntimeError('driver source changed')
 observation=pathlib.Path(tempfile.mkdtemp(prefix='link-only-inspection-',dir=build))
 reports={}
 for name,command in [('image',['/usr/bin/file',str(binary)]),('libraries',['/usr/bin/otool','-L',str(binary)]),('symbols',['/usr/bin/nm',str(binary)])]:
  result=subprocess.run(command,capture_output=True,text=True,check=True)
  report=observation/(name+'.txt');report.write_text(result.stdout+result.stderr)
  reports[name]={'path':str(report),'sha256':sha(report)}
 symbols=(observation/'symbols.txt').read_text()
 if 'UnisonAreaTaskHost' not in symbols or 'UnisonMemoryAllocator' not in symbols:
  raise RuntimeError('expected adapter symbols absent')
 receipt={'scope':'build/static-inspection only; target never executed','manifest':str(manifest),'manifest_sha256':sha(manifest),'binary':str(binary),'binary_sha256':sha(binary),'reports':reports,'runtime_qualified':False,'production_endpoint_changed':False}
 (observation/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('Static observation:',observation/'RESULT.json',flush=True)
 return receipt

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--sdk-root',default=os.environ.get('SDK_ROOT'),type=pathlib.Path)
 p.add_argument('--build-dir',default=os.environ.get('BUILD_DIR'),type=pathlib.Path)
 p.add_argument('--jobs',default=os.environ.get('JOBS','4'),type=int)
 p.add_argument('--inspect-only',action='store_true')
 a=p.parse_args()
 if a.build_dir is None or (not a.inspect_only and a.sdk_root is None) or not 1<=a.jobs<=128:
  p.error('BUILD_DIR and (for builds) SDK_ROOT required; JOBS must be 1..128')
 build=a.build_dir.resolve()
 if (build/'build-manifest.json').exists():p.error('qualified v1 build directory refused')
 if a.inspect_only:inspect(build);return
 sdk=a.sdk_root.resolve();owner=build/'.unison-experimental-area-memory-owner.json'
 expected={'schema':1,'sdk_root':str(sdk),'mode':'area-memory-unqualified'}
 if build.exists():
  if not owner.is_file() or json.loads(owner.read_text())!=expected:
   p.error('use a fresh directory or matching owned experimental directory')
 else:
  build.mkdir(parents=True,mode=0o700);owner.write_text(json.dumps(expected)+'\n')
 with (build/'.build.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  subprocess.run([sys.executable,str(HERE/'build.py'),'--sdk-root',str(sdk),'--build-dir',str(build),'--jobs',str(a.jobs),'--experimental-area-task-host','--experimental-memory-budget'],check=True)
  inspect(build)

if __name__=='__main__':main()
