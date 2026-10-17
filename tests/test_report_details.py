#!/usr/bin/env python3
"""Exercise private owner UI cache code linked to an isolated compiler build."""
from pathlib import Path
import os
import re
import subprocess
import struct
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
    modules = modules[:modules.index("uicommon.cmx")]
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]] + ["-I", "+unix", "-I", "+str"]
    with tempfile.TemporaryDirectory(prefix="unison-detail-report-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        (work / "uicommonForTest.ml").write_text((repository / "src/uicommon.ml").read_text())
        (work / "uicommonForTest.mli").write_text((repository / "src/uicommon.mli").read_text() + "\n"
            "type semantic_detail = { item:Common.reconItem; roots:Common.root * Common.root;\n"
            "  snapshots:(Fspath.t * Unix.LargeFile.stats) list; text:string }\n"
            "val semantic_detail : semantic_detail option ref\n"
            "val take_semantic_detail : Common.reconItem -> string option\n")
        (work / "detailsTest.ml").write_text((repository / "tests/report_details.ml").read_text())
        compiler = os.environ.get("OCAMLOPT", "ocamlopt")
        subprocess.run([compiler] + flags + ["-c", "uicommonForTest.mli"], cwd=work, check=True)
        subprocess.run([compiler] + flags + ["-c", "uicommonForTest.ml"], cwd=work, check=True)
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules]
        command += ["uicommonForTest.cmx", "detailsTest.ml"]
        command += [str(build / obj) for obj in objects("COBJS")]
        subprocess.run(command + ["-o", "detail-test"], cwd=work, check=True)
        for name in ("left", "right", "state"):
            (work / name).mkdir()
        data=bytearray(8192)
        struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
        for i,entry in enumerate([(273,4,1,4096),(279,4,1,1024),(700,1,16,1024),(50706,1,4,1025)]):
            struct.pack_into('<HHII',data,10+12*i,*entry)
        data[1024:1040]=b'<x>one</x>      '
        data[4096:5120]=b'P'*1024
        (work/'left/components.dng').write_bytes(data)
        data[-1]=1
        (work/'right/components.dng').write_bytes(data)
        subprocess.run([str(work / "detail-test")], cwd=work,
                       env=dict(os.environ, UNISON=str(work / "state"), UNISON_DETAIL_TEST_ROOT=str(work)),
                       check=True, timeout=20)


if __name__ == "__main__":
    main()
