#!/usr/bin/env python3
"""Compile a finite owned-group kernel observation probe; no SDK or Photo."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--ocamlopt',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2]
work=Path(tempfile.mkdtemp(prefix='unison-owned-group-probe-')).resolve()
print('Workspace:',work,flush=True)
names=('src/helperSupervisor_stubs.c','tests/helper_group_observation/probe.ml','tests/helpers/synthetic_helper.ml')
def pin(path):
 path=Path(path);return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
sources=[pin(root/n) for n in names]
for name in names:shutil.copyfile(root/name,work/Path(name).name)
commands=([str(a.ocamlopt),'-I','+unix','-c','helperSupervisor_stubs.c'],
          [str(a.ocamlopt),'-I','+unix','unix.cmxa','synthetic_helper.ml','-o','synthetic_helper'],
          [str(a.ocamlopt),'-I','+unix','unix.cmxa','helperSupervisor_stubs.o','probe.ml','-o','probe'],
          [str(work/'probe'),str(work/'synthetic_helper')])
results=[]
def execute(command):
 index=len(results)
 result=subprocess.run(command,cwd=work,capture_output=True,text=True,timeout=30)
 log=work/('step-%d.log'%index);log.write_text(result.stdout+result.stderr)
 results.append({'command':command,'exit_code':result.returncode,'log':pin(log)})
 print(result.stdout+result.stderr,end='',flush=True)
 return result.returncode==0
for command in commands:
 if not execute(command):break
success=len(results)==4 and all(r['exit_code']==0 for r in results)
if success:
 # Exercise the six-argument bytecode ABI separately from native calls.
 compiler=a.ocamlopt.with_name('ocamlc')
 success=execute([str(compiler),'-custom','-I','+unix','unix.cma',
                  'helperSupervisor_stubs.o','probe.ml','-o','probe.byte'])
 if success:success=execute([str(work/'probe.byte'),str(work/'synthetic_helper')])
if success:
 # Original private wrappers affect only the new query, never production files.
 # A failed/incomplete kernel observation must not become a zero-member receipt.
 faults={
  'ENOMEM':'errno=ENOMEM; return -1;',
  'size':'*length=1; return 0;',
  'identity':('struct kinfo_proc record={0}; record.kp_proc.p_pid=name[3]; '
              'record.kp_eproc.e_pgid=0; record.kp_proc.p_stat=SRUN; '
              'memcpy(buffer,&record,sizeof(record)); *length=sizeof(record); return 0;'),
  'duplicate':('struct kinfo_proc pair[2]={{0},{0}}; '
               'pair[0].kp_proc.p_pid=pair[1].kp_proc.p_pid=name[3]; '
               'pair[0].kp_proc.p_stat=pair[1].kp_proc.p_stat=SZOMB; '
               'memcpy(buffer,pair,sizeof(pair)); *length=sizeof(pair); return 0;')}
 for name,body in faults.items():
  source=work/(name+'.c')
  source.write_text('#include <sys/types.h>\n#include <sys/sysctl.h>\n#include <sys/proc.h>\n#include <errno.h>\n#include <string.h>\n'
      'static int group_query(int *name, unsigned int count, void *buffer, size_t *length, void *value, size_t size) {'
      '(void)count;(void)value;(void)size;'+body+'}\n#define sysctl group_query\n'
      '#include "helperSupervisor_stubs.c"\n')
  if not execute([str(a.ocamlopt),'-I','+unix','-c',source.name]):success=False;break
  if not execute([str(a.ocamlopt),'-I','+unix','unix.cmxa',name+'.o','probe.ml','-o',name+'-probe']):success=False;break
  if not execute([str(work/(name+'-probe')),str(work/'synthetic_helper'),'ENOMEM' if name=='ENOMEM' else 'EIO']):success=False;break
a.report.write_text(json.dumps({'complete':success,'workspace':str(work),'sources':sources,'compiler':pin(a.ocamlopt),'steps':results,'scope':'private finite POSIX helper groups and actual macOS kernel observation only; no SDK/Photo; no production observer integration'},indent=2)+'\n')
raise SystemExit(0 if success else 1)
