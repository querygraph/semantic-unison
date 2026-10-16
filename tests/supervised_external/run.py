#!/usr/bin/env python3
"""Actual compiler-matched generic helper bridge on SDK-free private data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
CASES=('argv','shell','empty-argv','nul-argv0','nul-argument','missing','weight',
       'timeout','stdout-limit','stderr-limit','signal','active-cancel','queued-cancel','mixed')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def objects(text,name):
    value=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
    return (value.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','')
            .replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split())

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,required=True);ap.add_argument('--ocamlopt',required=True)
    ap.add_argument('--receipt',type=Path,required=True);args=ap.parse_args()
    src=args.build.resolve()/'src';compiler=Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
    allmods=objects((src/'Makefile.OCaml').read_text(),'OCAMLOBJS')
    modules=allmods[:allmods.index('supervisedExternal.cmx')+1];native=objects((src/'Makefile.OCaml').read_text(),'COBJS')
    work=Path(tempfile.mkdtemp(prefix='unison-supervised-external-',dir='/private/tmp'))
    env=os.environ.copy()
    for k in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):env.pop(k,None)
    env['SUPERVISED_FIXTURE_ENV']='inherited value'
    tests=['tests/supervised_external/'+p for p in ('helper.ml','test.ml','run.py')]
    receipt={'schema':1,'success':False,'work':str(work),'snapshot':str(src),'compiler':str(compiler),
        'compiler_sha256':sha(compiler),'commands':[],'cases':[],'test_pins':{p:sha(ROOT/p) for p in tests},
        'linked_object_pins':{p:sha(src/p) for p in modules+native},'source_pins':{},
        'scope':'Actual unmodified SupervisedExternal/shared legacy-Lwt/domain/helper runtime; compiled synthetic CLI helper only',
        'Adobe_or_Photo_or_UI_access':False,'performance_claim':False}
    for module in modules:
        for suffix in ('.ml','.mli'):
            p=Path(module).with_suffix(suffix)
            if (src/p).is_file():
                receipt['source_pins'][str(p)]=sha(src/p)
                if str(p)!='ubase/projectInfo.ml':assert sha(src/p)==sha(ROOT/'src'/p)
    def command(argv,cwd,label,extra=None):
        r=subprocess.run([str(p) for p in argv],cwd=cwd,env=dict(env,**(extra or {})),
            text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        log=cwd/(label+'.log');log.write_text(r.stdout)
        receipt['commands'].append({'argv':[str(p) for p in argv],'cwd':str(cwd),'exit':r.returncode,
            'log':str(log),'log_sha256':sha(log),'task_env':extra or {}})
        if r.returncode:print(r.stdout,flush=True)
        r.check_returncode();return r
    try:
        receipt['compiler_version']=command([compiler,'-version'],work,'compiler').stdout.strip()
        for p in tests:shutil.copy2(ROOT/p,work/Path(p).name)
        includes=[src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic']
        flags=[x for p in includes for x in ('-I',str(p))]+['-I','+unix','-I','+str']
        command([compiler,'-I','+unix','unix.cmxa','helper.ml','-o','helper'],work,'helper-build')
        command([compiler,*flags,'unix.cmxa','str.cmxa',*[src/m for m in modules],*[src/n for n in native],
            'test.ml','-o','test'],work,'test-build')
        for case in CASES:
            directory=work/case;directory.mkdir()
            result=command([work/'test',case,work/'helper'],directory,'run',{'UNISON':str(directory/'state')})
            assert 'PASS '+case+' checks=' in result.stdout
            receipt['cases'].append(case);print(result.stdout.strip(),flush=True)
        receipt['artifacts']={str(p.relative_to(work)):{'bytes':p.stat().st_size,'sha256':sha(p)}
            for p in sorted(work.rglob('*')) if p.is_file()}
        receipt['success']=True
    finally:
        args.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print('receipt',args.receipt,'work',work,flush=True)

if __name__=='__main__':main()
