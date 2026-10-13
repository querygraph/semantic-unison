#!/usr/bin/env python3
"""Link a synthetic second profile without changing any production dispatcher.
Usage: python3 tests/test_generic_format.py /private/tmp/isolated-unison-build
"""
from pathlib import Path
import os
import re
import runpy
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
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]] + ["-I", "+unix", "-I", "+str"]
    with tempfile.TemporaryDirectory(prefix="unison-generic-format-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        (work / "genericFormat.ml").write_text((repository / "tests/generic_format.ml").read_text())
        compiler = os.environ.get("OCAMLOPT", "ocamlopt")
        subprocess.run([compiler] + flags + ["-c", "genericFormat.ml"], cwd=work, check=True)
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        for obj in objects("OCAMLOBJS"):
            if obj == "main.cmx":
                command.append("genericFormat.cmx")
            command.append(str(build / obj))
        command.append(str(build / "linktext.cmx"))
        command += [str(build / obj) for obj in objects("COBJS")]
        binary = str(work / "unison-generic")
        subprocess.run(command + ["-o", binary], cwd=work, check=True)
        left,right,state = work / "left",work / "right",work / "state"
        left.mkdir(); right.mkdir(); state.mkdir()
        launcher = work / "loopback.py"
        launcher.write_text("#!/usr/bin/env python3\nimport os,sys\n"
                            "a=sys.argv[1:]\ni=a.index(" + repr(binary) + ")\n"
                            "os.execv(a[i],a[i:])\n")
        launcher.chmod(0o700)
        args = [binary,str(left),"ssh://localhost/"+str(right),"-sshcmd",str(launcher),
                "-servercmd",binary,"-batch","-auto","-fastcheck","false","-times",
                "-debug","semantic","-semanticprofile","org.unison.test-fixed/0"]
        def sync(expect):
            result = subprocess.run(args, env=dict(os.environ,UNISON=str(state)),
                                    capture_output=True,text=True,timeout=90)
            log = result.stdout + result.stderr
            assert result.returncode == 0, log
            assert ("Remote semantic clone wrote" in log) == expect, log
            if expect:
                assert "org.unison.test-fixed/0" in log, log
        source,target = left / "opaque.bin",right / "opaque.bin"
        source.write_bytes(b"TOY0aaaa" + b"X" * 2000000); sync(False)
        source.write_bytes(b"TOY0bbbb" + b"X" * 2000000); sync(True)
        assert target.read_bytes() == source.read_bytes()
        target.write_bytes(b"TOY0cccc" + b"X" * 2000000); sync(True)
        assert source.read_bytes() == target.read_bytes()
        source.write_bytes(b"TOY0dddd" + b"X" * 1999999 + b"Z"); sync(False)
        assert target.read_bytes() == source.read_bytes()
        print("registered second format: both remote directions exact; opaque change fallback; no dispatcher edits")
        report_test = runpy.run_path(str(repository / "tests/test_semantic_reports.py"))["exercise"]
        original = b"TOY0aaaa" + b"X" * 2000000
        for remote in (False, True):
            report_test(binary,binary,"opaque.bin",original,
                        b"TOY0bbbb" + b"X" * 2000000,b"TOY0cccc" + b"X" * 2000000,
                        classification="Classification: editable metadata differs; all bytes outside those regions match.",
                        remote=remote,profile="org.unison.test-fixed/0",
                        expected_meaning=("Extension interpretation: org.unison.toy-properties/0",
                                          "workflow metadata: toy:workflow-state encoding/context changed"))
        print("registered second format: generic local/remote CLI diff/details without dispatch branches")


if __name__ == "__main__":
    main()
