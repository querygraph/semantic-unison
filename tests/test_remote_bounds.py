#!/usr/bin/env python3
"""Test RPC preallocation limits against header-only pipes in a private build.
Usage: python3 tests/test_remote_bounds.py /private/tmp/isolated-unison-build
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import nullcontext


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--compiler', default=os.environ.get('OCAMLOPT', 'ocamlopt'))
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    build = args.build.resolve() / "src"
    makefile = (build / "Makefile.OCaml").read_text()
    def objects(name):
        body = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S).group(1)
        body = body.replace("\\\n", " ").replace("$(SYSTEM)", "generic")
        body = body.replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
        return body.replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split()
    modules = objects("OCAMLOBJS")
    modules = modules[:modules.index("remote.cmx")]
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]] + ["-I", "+unix", "-I", "+str"]
    workspace = nullcontext(tempfile.mkdtemp(prefix="unison-rpc-bounds-", dir="/private/tmp")) if args.report else tempfile.TemporaryDirectory(prefix="unison-rpc-bounds-", dir="/private/tmp")
    with workspace as tmp:
        work = Path(tmp)
        def controlled(source):
            anchor='let receivePacket ?maxBytes'
            assert source.count(anchor)==1
            source=source.replace(anchor,'let header_test_guard : int option ref=ref None\n'+anchor,1)
            anchor='  let buf = Bytearray.create length in'
            assert source.count(anchor)==1
            return source.replace(anchor,'  (match !header_test_guard with Some cap when length>cap->failwith "DESIGNATED header payload allocation reached" | _->());\n'+anchor,1)
        (work / "remoteForTest.ml").write_text(controlled((repository / "src/remote.ml").read_text()))
        (work / "remoteTest.ml").write_text((repository / "tests/remote_bounds.ml").read_text()+'\n'+(repository/'tests/remote_header_bounds.ml').read_text())
        compiler = args.compiler
        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        record = dict(schema='unison-rpc-input-bounds/1', status='failed',
                      compiler=compiler, build_snapshot=str(build.parent),
                      tested_sources={'src/remote.ml': sha(repository/'src/remote.ml'),
                                      'tests/remote_bounds.ml': sha(repository/'tests/remote_bounds.ml'),
                                      'tests/remote_header_bounds.ml': sha(repository/'tests/remote_header_bounds.ml'),
                                      'tests/test_remote_bounds.py': sha(Path(__file__))},
                      linked_objects={name: sha(build/name) for name in modules+objects('COBJS')},
                      commands=[])
        def execute(command, **kwargs):
            result = subprocess.run(command, cwd=work, **kwargs)
            record['commands'].append(dict(argv=command, exit_code=result.returncode))
            result.check_returncode()
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules]
        command += ["remoteForTest.cmx", "remoteTest.ml"]
        command += [str(build / obj) for obj in objects("COBJS")]
        command += ["-o", "remote-test"]
        try:
            execute([compiler] + flags + ["-c", "remoteForTest.ml"])
            execute(command)
            execute([str(work / "remote-test")], timeout=15,
                    env=dict(os.environ, UNISON=str(work / "state")))
            record['workspace']=str(work)
            record['binary_sha256']=sha(work/'remote-test')
            # Remove only the selected decoded limits; unit-list payload is
            # 2000 elements, so this counterexample never asks for huge memory.
            negative=work/'negative';negative.mkdir(mode=0o700)
            source=(repository/'src/remote.ml').read_text()
            old='(boundedMarshalingFunctions maxArgs mArg) (boundedMarshalingFunctions maxResult mRet) f in'
            assert source.count(old)==1
            bad=source.replace(old,'(defaultMarshalingFunctions mArg) (defaultMarshalingFunctions mRet) f in')
            (negative/'remoteForTest.ml').write_text(controlled(bad))
            (negative/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
            private_flags=['-I',str(negative),*flags]
            for argv in [[compiler,*private_flags,'-c','remoteForTest.ml'],
                         [compiler,*private_flags,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','remote-negative']]:
                c=subprocess.run(argv,cwd=negative,capture_output=True,text=True,timeout=30)
                record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
            c=subprocess.run([str(negative/'remote-negative')],cwd=negative,env=dict(os.environ,UNISON=str(negative/'state')),capture_output=True,text=True,timeout=15)
            (negative/'test.log').write_text(c.stdout+c.stderr)
            assert c.returncode==2 and 'DESIGNATED decoded collection reached server' in c.stderr,c.stdout+c.stderr
            record['negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(negative/'remoteForTest.ml'),binary_sha256=sha(negative/'remote-negative'),scope='Only bounded registrations use legacy decoder;2000zero-payload elements, no huge allocation')
            # Restore only unbounded header routing. The test-only allocation
            # guard fails before a body allocation/read; no large allocation.
            header=work/'header-negative';header.mkdir(mode=0o700)
            old='receiveHeader conn >>= (fun req ->'
            assert source.count(old)==1
            bad_header=source.replace(old,'receivePacket conn >>= (fun buffer -> let req=unmarshalHeader conn buffer in')
            (header/'remoteForTest.ml').write_text(controlled(bad_header))
            (header/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
            hf=['-I',str(header),*flags]
            for argv in [[compiler,*hf,'-c','remoteForTest.ml'],[compiler,*hf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','header-negative']]:
                c=subprocess.run(argv,cwd=header,capture_output=True,text=True,timeout=30)
                record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
            c=subprocess.run([str(header/'header-negative')],cwd=header,env=dict(os.environ,UNISON=str(header/'state')),capture_output=True,text=True,timeout=15)
            (header/'test.log').write_text(c.stdout+c.stderr)
            assert c.returncode==2 and 'DESIGNATED header payload allocation reached' in c.stderr,c.stdout+c.stderr
            record['header_negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(header/'remoteForTest.ml'),binary_sha256=sha(header/'header-negative'))
            record['controlled_remote_sha256']=sha(work/'remoteForTest.ml')
            record['controlled_probe_sha256']=sha(work/'remoteTest.ml')
            record['status']='passed'
        finally:
            if args.report:
                args.report.write_text(json.dumps(record, indent=2)+'\n')


if __name__ == "__main__":
    main()
