"""Compile current runtime against actual compiler-matched dependency objects.

Fixed no-file/no-helper controls and one exact previous-guard negative. No SDK,
CLI sync, Photo data, payload or canonical IO lane is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-result',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2]
build=json.loads(a.build_result.read_text());src=Path(build['workspace'])/'src'
compiler=build['compiler'];sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(compiler)==build['compiler_sha256']
w=Path(tempfile.mkdtemp(prefix='unison-publication-admission-'));print(w,flush=True)
def objects(name):
 match=re.search(r'^'+name+r' = (.*?)(?=\n\n)',(src/'Makefile.OCaml').read_text(),re.M|re.S)
 assert match
 return match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
allmods=objects('OCAMLOBJS');mods=allmods[:allmods.index('semanticRuntime.cmx')]
# Bind the dependency snapshot to the recorded production source inventory.
for name,digest in build['source_sha256'].items():
 if name.startswith('src/') and Path(name).suffix in ('.ml','.mli','.c'):
  assert sha(src.parent/name)==digest,name
linked={str(src/name):sha(src/name) for name in mods+objects('COBJS')}
source=(root/'src/semanticRuntime.ml').read_text()
fixed='''  try SemanticAdmission.make_reservation (resource_gate ()) ~role:SemanticAdmission.Consumer
    ~cost:(publication_cost max_payload)
  with SemanticAdmission.Failed reason ->
    raise (Util.Transient ("Receiving resource admission: " ^ reason))
'''
old='''  SemanticAdmission.make_reservation (resource_gate ()) ~role:SemanticAdmission.Consumer
    ~cost:(publication_cost max_payload)
'''
assert source.count(fixed)==1
commands=[]
def run(argv,cwd,label,expected=0,marker=None):
 result=subprocess.run(list(map(str,argv)),cwd=cwd,text=True,capture_output=True,timeout=45)
 log=w/(label+'.log');log.write_text(result.stdout+result.stderr)
 commands.append({'argv':list(map(str,argv)),'returncode':result.returncode,'log':str(log),'sha256':sha(log)})
 assert result.returncode==expected,log.read_text()
 if marker:assert marker in log.read_text(),log.read_text()
for variant in ('current','previous-guard'):
 d=w/variant;d.mkdir()
 shutil.copyfile(src/'semanticRuntime.cmi',d/'semanticRuntime.cmi')
 (d/'semanticRuntime.ml').write_text(source if variant=='current' else source.replace(fixed,old))
 shutil.copyfile(root/'tests/publication_admission/test.ml',d/'test.ml')
 flags=[str(v) for x in (d,src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic') for v in ('-I',x)]+['-I','+unix','-I','+str']
 run([compiler,*flags,'-c','semanticRuntime.ml'],d,variant+'-compile')
 run([compiler,*flags,'unix.cmxa','str.cmxa',*[src/m for m in mods],d/'semanticRuntime.cmx',d/'test.ml',*[src/n for n in objects('COBJS')],'-o',d/'control'],d,variant+'-link')
 modes=('require','warn','fits','off','negative') if variant=='current' else ('require',)
 for mode in modes:
  run([d/'control',mode],d,variant+'-'+mode,expected=0 if variant=='current' else 2,
      marker='PASS publication admission '+mode if variant=='current' else 'DESIGNATED oversized publication reservation escaped as SemanticAdmission.Failed')
a.report.write_text(json.dumps({'schema':'unison-publication-admission/1','workspace':str(w),'compiler':compiler,'compiler_sha256':sha(compiler),'commands':commands,'linked_objects':linked,'runtime_source_sha256':sha(root/'src/semanticRuntime.ml'),'test_sources':{str(q):sha(q) for q in (Path(__file__),root/'tests/publication_admission/test.ml')},'scope':'actual production dependency objects/current runtime plus exact prior-guard negative; no SDK/helper/file payload/CLI sync or IO lane','passed':True},indent=2)+'\n')
