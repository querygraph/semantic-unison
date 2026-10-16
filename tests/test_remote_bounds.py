#!/usr/bin/env python3
"""Test RPC preallocation limits against header-only pipes in a private build.
Usage: python3 tests/test_remote_bounds.py /private/tmp/isolated-unison-build
"""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile


def main():
    repository = Path(__file__).resolve().parent.parent
    build = Path(sys.argv[1]).resolve() / "src"
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
        subprocess.run([compiler] + flags + ["-c", "remoteForTest.ml"], cwd=work, check=True)
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules]
        command += ["remoteForTest.cmx", "remoteTest.ml"]
        command += [str(build / obj) for obj in objects("COBJS")]
        command += ["-o", "remote-test"]
        subprocess.run(command, cwd=work, check=True)
        subprocess.run([str(work / "remote-test")], cwd=work, timeout=15,
                       env=dict(os.environ, UNISON=str(work / "state")), check=True)


if __name__ == "__main__":
    main()
