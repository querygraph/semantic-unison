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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--report', type=Path)
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
    with tempfile.TemporaryDirectory(prefix="unison-rpc-bounds-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        (work / "remoteForTest.ml").write_text((repository / "src/remote.ml").read_text())
        (work / "remoteTest.ml").write_text((repository / "tests/remote_bounds.ml").read_text())
        compiler = os.environ.get("OCAMLOPT", "ocamlopt")
        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        record = dict(schema='unison-rpc-input-bounds/1', status='failed',
                      compiler=compiler, build_snapshot=str(build.parent),
                      tested_sources={'src/remote.ml': sha(work/'remoteForTest.ml'),
                                      'tests/remote_bounds.ml': sha(work/'remoteTest.ml'),
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
            record['status']='passed'
        finally:
            if args.report:
                args.report.write_text(json.dumps(record, indent=2)+'\n')


if __name__ == "__main__":
    main()
