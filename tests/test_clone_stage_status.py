#!/usr/bin/env python3
"""Build/qualify strict native clone results in a disposable APFS directory."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="unison-clone-status-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        shutil.copy2(root / "src/copy_stubs.c", work / "copy_stubs.c")
        shutil.copy2(root / "tests/clone_stage_status.ml", work / "clone_stage_status.ml")
        subprocess.run([args.ocamlopt, "-I", "+unix", "-c", "copy_stubs.c"], cwd=work, check=True)
        subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", "copy_stubs.o",
                        "clone_stage_status.ml", "-o", "clone-stage-status"], cwd=work, check=True)
        harness = work / "clone-stage-status"

        def run(mode, source, output, *, skip=False):
            result = subprocess.run([str(harness), mode, str(source), str(output)], timeout=10)
            if skip and result.returncode == 77:
                return False
            result.check_returncode()
            assert not list(work.glob("*.basis.*")), "owned basis path remained"
            return True

        source = work / "source"
        source.write_bytes(bytes(range(256)) * 32)
        source.chmod(0o400)
        if not run("shared", source, work / "stage", skip=True):
            print("SKIP: fixture filesystem/platform lacks native clone staging")
            return
        assert source.stat().st_mode & 0o777 == 0o400
        fifo = work / "fifo"
        os.mkfifo(fifo)
        run("kind", fifo, work / "fifo-stage")
        directory = work / "directory"
        directory.mkdir()
        run("kind", directory, work / "directory-stage")
        subprocess.run(["/usr/bin/chflags", "nodump", str(source)], check=True)
        try:
            run("flags", source, work / "flags-stage")
        finally:
            subprocess.run(["/usr/bin/chflags", "0", str(source)], check=True)
        run("missing-parent", source, work / "missing" / "stage")
        link = work / "source-link"
        link.symlink_to(source)
        run("symlink", link, work / "symlink-stage")
        assert source.read_bytes() == bytes(range(256)) * 32
        print("Strict native clone outcomes retain scope/phase; legacy option ABI remains usable")


if __name__ == "__main__":
    main()
