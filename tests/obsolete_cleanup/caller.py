#!/usr/bin/env python3
"""Actual private Copy cleanup and wrong-parent negative, ordinary CLI only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PREFIX = r'''
module ObsoleteCallerFault = struct
  let env name = match Sys.getenv_opt name with Some value -> value | None -> ""
  let fired = ref false
  let write path bytes =
    let fd = Unix.openfile path [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL] 0o600 in
    let ch = Unix.out_channel_of_descr fd in
    Fun.protect ~finally:(fun () -> close_out ch) (fun () -> output_string ch bytes)
  let before directory path =
    let root = Fspath.toString directory in
    if not !fired && root = env "OBSOLETE_RIGHT" && env "OBSOLETE_MODE" <> "" then begin
      fired := true;
      let name = Path.toString path in
      let leaf = Filename.concat root name in
      write leaf "independent admitted obsolete stage";
      let log = open_out_bin (env "OBSOLETE_LOG") in
      output_string log name; close_out log;
      if env "OBSOLETE_MODE" = "rebind" then begin
        Unix.rename root (root ^ "-held"); Unix.mkdir root 0o700;
        write leaf "independent replacement stage";
        write (Filename.concat root "image.bin") "independent replacement LIVE"
      end
    end
end
'''

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def objects(makefile, name):
    text = re.search(r'^' + name + r' = (.*?)(?=\n\n)', makefile, re.M | re.S).group(1)
    return (text.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','')
            .replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--ocamlopt', required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    args = ap.parse_args()
    src = args.build.resolve() / 'src'
    compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
    work = Path(tempfile.mkdtemp(prefix='unison-obsolete-caller-',dir='/private/tmp'))
    env = os.environ.copy()
    for key in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'): env.pop(key,None)
    modules = objects((src / 'Makefile.OCaml').read_text(),'OCAMLOBJS')
    native = objects((src / 'Makefile.OCaml').read_text(),'COBJS')
    at = modules.index('copy.cmx')
    receipt = {'schema':1,'success':False,'work':str(work),'compiler':str(compiler),
        'compiler_sha256':sha(compiler),'snapshot':str(src),'copy_source_sha256':sha(src/'copy.ml'),
        'native_source_sha256':sha(src/'finalPublication_stubs.c'),'runner_sha256':sha(Path(__file__)),
        'commands':[],'runs':[],'Adobe_or_Photo_or_UI_access':False,
        'scope':'Actual local Copy/Files CLI and normal native publication; private obsolete-name/parent mutation only; clone/semantic transfer disabled'}
    assert sha(src/'copy.ml') == sha(ROOT/'src/copy.ml')
    assert sha(src/'finalPublication_stubs.c') == sha(ROOT/'src/finalPublication_stubs.c')
    def command(argv, cwd, label, extras=None):
        result = subprocess.run([str(x) for x in argv],cwd=cwd,env=dict(env,**(extras or {})),
            text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
        log = cwd/(label+'.log');log.write_text(result.stdout)
        receipt['commands'].append({'argv':[str(x) for x in argv],'cwd':str(cwd),'exit':result.returncode,
            'log':str(log),'log_sha256':sha(log),'task_env':extras or {}})
        return result
    try:
        for mode in ('fixed','pathname-negative'):
            directory = work/mode;directory.mkdir()
            for name in modules[at:] + ['linktext.cmx']:
                for suffix in ('.ml','.mli'):
                    path = src/Path(name).with_suffix(suffix)
                    if path.is_file(): shutil.copy2(path,directory/path.name)
            path = directory/'copy.ml';text = path.read_text()
            anchor = 'let removeOldTempFile ?producer fspathTo pathTo =\n'
            assert text.count(anchor)==1
            if mode == 'pathname-negative':
                begin = text.index(anchor);end = text.index('(* There is an issue',begin)
                text = text[:begin] + anchor + '  ignore producer;\n  if Os.exists fspathTo pathTo then Os.delete fspathTo pathTo\n\n' + text[end:]
            text = text.replace(anchor,anchor+'  ObsoleteCallerFault.before fspathTo pathTo;\n')
            path.write_text(PREFIX+text)
            includes = [directory,src,src/'ubase',src/'lwt',src/'system',src/'system/generic',src/'lwt/generic']
            flags = [x for p in includes for x in ('-I',str(p))]+['-I','+unix','-I','+str']
            for name in modules[at:] + ['linktext.cmx']:
                stem = Path(name).stem
                for suffix in ('.mli','.ml'):
                    p=directory/(stem+suffix)
                    if p.is_file():
                        r=command([compiler,*flags,'-c',p.name],directory,'compile-'+stem+suffix)
                        if r.returncode: print(r.stdout)
                        r.check_returncode()
            binary=directory/'unison'
            r=command([compiler,*flags,'unix.cmxa','str.cmxa',*[src/n for n in modules[:at]],
                *[Path(n).name for n in modules[at:]],'linktext.cmx',*[src/n for n in native],'-o',binary],directory,'link')
            if r.returncode: print(r.stdout)
            r.check_returncode()
            for action in ('ordinary','rebind') if mode == 'fixed' else ('rebind',):
                case=directory/action;case.mkdir()
                left,right,state=(case/n for n in ('left','right','state'))
                for p in (left,right,state):p.mkdir()
                source=left/'image.bin';target=right/'image.bin';old=b'OLD-source';new=b'NEW-source-independent'
                source.write_bytes(old)
                argv=[binary,left,right,'-batch','-auto','-fastcheck','false','-clone','off','-semanticdng=false','-semanticworkers','1']
                r=command(argv,case,'baseline',{'UNISON':str(state)});r.check_returncode()
                assert target.read_bytes()==old
                source.write_bytes(new);log=case/'stage-name'
                r=command(argv,case,'transfer',{'UNISON':str(state),'OBSOLETE_RIGHT':str(right),
                    'OBSOLETE_MODE':action,'OBSOLETE_LOG':str(log)})
                assert log.exists(),'actual Copy cleanup hook did not execute'
                name=log.read_text();leaf=right/name
                assert source.read_bytes()==new
                if action=='ordinary':
                    assert r.returncode==0 and target.read_bytes()==new and not leaf.exists()
                elif mode=='fixed':
                    assert r.returncode!=0 and leaf.read_bytes()==b'independent replacement stage'
                    assert target.read_bytes()==b'independent replacement LIVE'
                    assert (Path(str(right)+'-held')/name).read_bytes()==b'independent admitted obsolete stage'
                    assert (Path(str(right)+'-held')/'image.bin').read_bytes()==old
                else:
                    assert r.returncode!=0 and not leaf.exists(),'pathname negative failed to reproduce actual wrong-parent removal'
                    assert target.read_bytes()==b'independent replacement LIVE'
                receipt['runs'].append({'mode':mode,'action':action,'actual_cli_exit':r.returncode,'stage_name':name,
                    'source_preserved':True,'designated_negative_detected':mode!='fixed'})
                print('PASS',mode,action,flush=True)
        receipt['artifacts']={str(p.relative_to(work)):{'bytes':p.stat().st_size,'sha256':sha(p)}
            for p in sorted(work.rglob('*')) if p.is_file()}
        receipt['success']=True
    finally:
        args.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print('receipt',args.receipt,'work',work,flush=True)

if __name__=='__main__':main()
