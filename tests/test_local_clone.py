#!/usr/bin/env python3
"""Exercise the local producer and semantic transaction without volume mounts.

Usage: python3 tests/test_local_clone.py /private/tmp/isolated-unison-build
Requires an already-built native tree. Compilation and fixtures are temporary;
the source workspace and supplied build tree are read-only to this driver.
OCAMLOPT may name the compiler that produced the supplied build objects.
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
    modules = modules[:modules.index("copy.cmx")]
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]] + ["-I", "+unix", "-I", "+str"]
    with tempfile.TemporaryDirectory(prefix="unison-local-clone-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        (work / "copyForTest.ml").write_text((repository / "src/copy.ml").read_text())
        fixtures = (repository / "tests/semantic/test.ml").read_text().split("let () =", 1)[0]
        registration = (repository / "tests/generic_format.ml").read_text()
        (work / "localTest.ml").write_text(fixtures + registration + (repository / "tests/local_clone.ml").read_text())
        compiler = os.environ.get("OCAMLOPT", "ocamlopt")
        subprocess.run([compiler] + flags + ["-c", "copyForTest.ml"], cwd=work, check=True)
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules]
        command += ["copyForTest.cmx", "localTest.ml"]
        command += [str(build / obj) for obj in objects("COBJS")]
        command += ["-o", "local-test"]
        subprocess.run(command, cwd=work, check=True)
        fixtures = work / "fixtures"; fixtures.mkdir()
        subprocess.run([str(work / "local-test")], cwd=fixtures,
                       env=dict(os.environ, UNISON=str(work / "state")), check=True)


if __name__ == "__main__":
    main()
