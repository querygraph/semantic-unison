#!/usr/bin/env python3
"""Actual asynchronous capture, saved-file and cached scalar merge on synthetic DNGs."""
import argparse,json,hashlib,os,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads(a.build_receipt.read_text());build=Path(b['workspace'])
assert b['complete'] and b['build_exit']==b['selftest_exit']==0
assert sha(b['compiler'])==b['compiler_sha256'] and sha(b['binary'])==b['binary_sha256']
for name,digest in b['source_sha256'].items():
 if name.startswith('src/'):assert sha(root/name)==digest,name
work=Path(tempfile.mkdtemp(prefix='unison-merge-io-errors-')).resolve()
shutil.copyfile(root/'tests/resource_close/input_pipeline_test.ml',work/'probe.ml')
objects=(build/'src/Makefile.OCaml').read_text().split('OCAMLOBJS =',1)[1].split('\n\n',1)[0].replace('\\','').split()
objects=[name.replace('$(SYSTEM)','generic') for name in objects if name!='$(WINOBJS)']
objects=objects[:objects.index('semanticSync.cmo')+1]
paths=[str(build/'src'/name.replace('.cmo','.cmx')) for name in objects]
flags=[v for name in ['src','src/ubase','src/system','src/system/generic','src/lwt','src/lwt/generic'] for v in ['-I',str(build/name)]]
stubs=['pty.o','bytearray_stubs.o','hash_compat.o','props_xattr.o','props_acl.o','osxsupport.o','copy_stubs.o','nativeCopyRange_stubs.o','wholeFileClone_stubs.o','fileObservation_stubs.o','stagePublication_stubs.o','finalPublication_stubs.o','semanticHash_stubs.o','semanticFile_stubs.o','helperSupervisor_stubs.o']
command=[b['compiler'],*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa',*[str(build/'src'/s) for s in stubs],*paths,'probe.ml','-o','probe']
c=subprocess.run(command,cwd=work,capture_output=True,text=True,timeout=60)
(work/'compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stderr
import struct
def fixture(rating='1',label='Blue'):
 b=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',b,0,b'II',42,8,4)
 packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"/></rdf:RDF>').encode();packet+=b' '*(8192-len(packet))
 for i,e in enumerate([(273,4,1,12288),(279,4,1,len(b)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',b,10+12*i,*e)
 struct.pack_into('<I',b,58,0);b[1024:9216]=packet
 return bytes(b)
for name,data in [('base',fixture()),('left',fixture('2')),('right',fixture(label='Gold')),('output',fixture('2')),('expected',fixture('2','Gold'))]:(work/name).write_bytes(data)
(work/'directory').mkdir();(work/'state').mkdir(mode=0o700)
before={name:sha(work/name) for name in ('base','left','right')}
x=subprocess.run([str(work/'probe')],cwd=work,env=dict(os.environ,UNISON=str(work/'state'),UNISON_PRIVATE_MERGE_EXCEPTION='',UNISON_PRIVATE_MERGE_FAULT_PROBE=''),capture_output=True,text=True,timeout=30)
(work/'test.log').write_text(x.stdout+x.stderr)
assert before=={name:sha(work/name) for name in before}
assert x.returncode==0,(x.returncode,x.stdout,x.stderr)
a.report.write_text(json.dumps(dict(work=str(work),compiler=b['compiler'],build_receipt=str(a.build_receipt),compile_command=command,stdout=x.stdout,stderr=x.stderr,returncode=x.returncode,scope='Actual full asynchronous capture, saved-file and cached scalar merge on generated64KiB DNG only; exact disjoint scalar reconciliation, source immutability and settled FD/admission/worker/CPU/IO ledgers. No real transport/SDK/camera/cache uncertainty injection.'),indent=2)+'\n')
print(x.stdout,end='')
