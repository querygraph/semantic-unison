#!/usr/bin/env python3
"""Link the endpoint preference boundary tests against an isolated native build."""
import os
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main():
    repository = Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path)
    parser.add_argument('--compiler',default=os.environ.get('OCAMLOPT','ocamlopt'))
    args=parser.parse_args()
    build = args.build.resolve() / "src"
    makefile = (build / "Makefile.OCaml").read_text()

    def objects(name):
        body = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S).group(1)
        body = body.replace("\\\n", " ").replace("$(SYSTEM)", "generic")
        body = body.replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
        return body.replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split()

    modules = objects("OCAMLOBJS")
    modules = modules[:modules.index("ubase/prefs.cmx") + 1]
    includes = [build, build / "ubase", build / "system", build / "system/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]] + ["-I", "+unix", "-I", "+str"]
    with tempfile.TemporaryDirectory(prefix="unison-endpoint-prefs-") as temp:
        work = Path(temp)
        source = work / "endpoint_prefs.ml"
        source.write_text((repository / "tests/endpoint_prefs.ml").read_text())
        command = [args.compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules] + [str(source)]
        command += [str(build / obj) for obj in objects("COBJS")]
        binary = str(work / "endpoint-prefs-test")
        subprocess.run(command + ["-o", binary], cwd=work, check=True)
        subprocess.run([binary, "-endpoint-alias-after", "cli-host", "-globalpolicy", "cli-policy"],
                       cwd=work, env=dict(os.environ, UNISON=str(work / "state")),
                       check=True, timeout=20)


if __name__ == "__main__":
    main()
