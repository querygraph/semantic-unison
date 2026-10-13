#!/usr/bin/env python3
"""Persistent socket source-admission cleanup using private production modules.

Usage: python3 tests/test_socket_reconnect.py /private/tmp/isolated-unison-build
Optional --negative-control removes only commandLoop's output stop in the
private source copy, and expects retained credits after reconnect.
"""
import argparse
from pathlib import Path
import os
import re
import signal
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("--negative-control", action="store_true")
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
    with tempfile.TemporaryDirectory(prefix="unison-socket-scope-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        source = (repository / "src/remote.ml").read_text()
        if args.negative_control:
            stop = "       stopConnectionOutput conn;\n       match e with"
            assert source.count(stop) == 1
            source = source.replace(stop, "       match e with", 1)
        (work / "remoteForTest.ml").write_text(source)
        (work / "socketTest.ml").write_text((repository / "tests/socket_reconnect.ml").read_text())
        compiler = os.environ.get("OCAMLOPT", "ocamlopt")
        subprocess.run([compiler] + flags + ["-c", "remoteForTest.ml"], cwd=work, check=True)
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules]
        command += ["remoteForTest.cmx", str(build / "helperSupervisor.cmx"),
                    str(build / "semanticAdmission.cmx"), "socketTest.ml"]
        command += [str(build / obj) for obj in objects("COBJS")]
        command += ["-o", "socket-test"]
        subprocess.run(command, cwd=work, check=True)
        state = work / "state"; state.mkdir()
        socket = work / "server.sock"
        env = dict(os.environ, UNISON=str(state), UNISON_SCOPE_SOCKET=str(socket),
                   UNISON_SCOPE_STATUS=str(work / "status"))
        with (work / "server.log").open("w") as log:
            server = subprocess.Popen([str(work / "socket-test")], cwd=work,
                                      env=dict(env, UNISON_SCOPE_MODE="server"),
                                      stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 10
                while not socket.exists():
                    if server.poll() is not None or time.monotonic() >= deadline:
                        raise AssertionError((work / "server.log").read_text())
                    time.sleep(0.01)
                dropped = subprocess.run([str(work / "socket-test")], cwd=work,
                                         env=dict(env, UNISON_SCOPE_MODE="drop"),
                                         capture_output=True, text=True, timeout=10)
                assert dropped.returncode == 0, dropped.stdout + dropped.stderr + (work / "server.log").read_text()
                print(dropped.stdout.strip())
                assert server.poll() is None, (work / "server.log").read_text()
                checked = subprocess.run([str(work / "socket-test")], cwd=work,
                                         env=dict(env, UNISON_SCOPE_MODE="check",
                                                  UNISON_SCOPE_EXPECTED_PID=str(server.pid)),
                                         capture_output=True, text=True, timeout=10)
                if args.negative_control:
                    assert checked.returncode != 0 and "retained source admission credits" in checked.stderr, checked.stdout + checked.stderr
                    print("Negative control reproduces persistent-server source-credit leak.")
                else:
                    assert checked.returncode == 0, checked.stdout + checked.stderr + (work / "server.log").read_text()
                    print(checked.stdout.strip())
                    assert server.poll() is None, "persistent server exited after reconnect"
            finally:
                if server.poll() is None:
                    server.send_signal(signal.SIGINT)
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill(); server.wait(timeout=3)


if __name__ == "__main__":
    main()
