#!/usr/bin/env python3
"""Qualify owner file opens against disposable FIFOs, without a live-path race.

Links compiler-matched snapshot dependencies with private copies of current
SemanticSync, CandidateValidation and the source-planning portion of
SemanticRemote. The planner's protocol-version accessor is fixed to v1; its
open/proof/worker/resource code is unchanged. No production test API is added.
"""
from pathlib import Path
import argparse
import os
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--negative-control", action="store_true",
                        help="also remove O_NONBLOCK in private ML copies and require FIFO timeouts")
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
    modules = modules[:modules.index("semanticSync.cmx")]
    modules.append("dngValidation.cmx")
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]]
    flags += ["-I", "+unix", "-I", "+str"]
    compiler = os.environ.get("OCAMLOPT", "ocamlopt")
    with tempfile.TemporaryDirectory(prefix="unison-nonblocking-open-", dir="/private/tmp") as tmp:
        workspace = Path(tmp)
        for negative in ([False, True] if args.negative_control else [False]):
            work = workspace / ("baseline" if negative else "current")
            work.mkdir()
            sources = {
                "semanticSyncForTest": (repository / "src/semanticSync.ml").read_text(),
                "candidateValidationForTest": (repository / "src/candidateValidation.ml").read_text(),
                "semanticPlanForTest": (repository / "src/semanticRemote.ml").read_text().split("let source_scope", 1)[0],
            }
            # A planner unit call has no socket. Only this already-qualified
            # protocol gate is adapted; real profile negotiation remains enabled.
            sources["semanticPlanForTest"] = (
                "module Remote = struct include Remote let connectionVersion _ = 1 end\n"
                + sources["semanticPlanForTest"])
            for name, source in sources.items():
                if negative:
                    source, count = re.subn(r";\s*Unix\.O_NONBLOCK", "", source)
                    assert count >= 1, "baseline did not remove the audited open flags"
                (work / (name + ".ml")).write_text(source)
            (work / "semanticSyncForTest.mli").write_text((repository / "src/semanticSync.mli").read_text())
            (work / "candidateValidationForTest.mli").write_text(
                (repository / "src/candidateValidation.mli").read_text() + "\n"
                "val snapshot : SemanticWorkers.t -> HelperSupervisor.cancellation -> string -> DngValidation.snapshot Lwt.t\n"
                "val validate_file : reservation:SemanticAdmission.reservation option -> selected:DngValidation.policy -> Fspath.t -> unit Lwt.t\n")
            for name in sources:
                interface = work / (name + ".mli")
                if interface.exists():
                    subprocess.run([compiler] + flags + ["-c", interface.name], cwd=work, check=True)
                subprocess.run([compiler] + flags + ["-c", name + ".ml"], cwd=work, check=True)
            fixture = (repository / "tests/semantic/test.ml").read_text().split("let () =", 1)[0]
            (work / "openTest.ml").write_text(fixture + (repository / "tests/nonblocking_open.ml").read_text())
            command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
            command += [str(build / obj) for obj in modules]
            command += [name + ".cmx" for name in sources] + ["openTest.ml"]
            command += [str(build / obj) for obj in objects("COBJS")]
            subprocess.run(command + ["-o", "open-test"], cwd=work, check=True)
            for case in ("sync", "async", "plan", "candidate", "tool"):
                fixtures = work / case
                fixtures.mkdir()
                state = fixtures / "state"
                state.mkdir()
                try:
                    subprocess.run([str(work / "open-test"), case], cwd=fixtures,
                                   env=dict(os.environ, UNISON=str(state)), check=True,
                                   timeout=2 if negative else 20)
                except subprocess.TimeoutExpired:
                    if not negative:
                        raise
                    print("PASS private old-open negative control timed out: " + case, flush=True)
                else:
                    if negative:
                        raise AssertionError("private old-open control did not block: " + case)


if __name__ == "__main__":
    main()
