#!/usr/bin/env python3
"""Run native APFS clone fixtures entirely in a disposable directory.

Build tests/clone_stage.ml in an isolated build tree first, for example:
  cd /private/tmp/unison-build/tests
  ocamlopt -I +unix unix.cmxa ../src/copy_stubs.o clone_stage.ml -o clone_stage
Then run this driver with that executable as its sole argument.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile


def main():
    harness = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory(prefix="unison-clone-stage-", dir="/private/tmp") as tmp:
        root = Path(tmp)
        fifo, fifo_stage = root / "fifo", root / "fifo-stage"
        os.mkfifo(fifo)
        # This open precedes the native regular-file check. A blocking open
        # would hang forever without a writer, preventing owner cancellation.
        result = subprocess.run([harness, str(fifo), str(fifo_stage)], timeout=5)
        assert result.returncode == 77, result.returncode
        assert not fifo_stage.exists()
        assert not list(root.glob("*.basis.*"))
        print("FIFO basis: prompt decline without a writer or owned leftovers")
        source, stage = root / "source", root / "stage"
        source.write_bytes(bytes(range(256)) * 32)
        subprocess.run(["/usr/bin/xattr", "-w", "org.unison.fixture", "old attribute", str(source)], check=True)
        subprocess.run(["/usr/bin/xattr", "-w", "com.apple.ResourceFork", "old fork", str(source)], check=True)
        subprocess.run(["/bin/chmod", "+a", "everyone allow read", str(source)], check=True)
        source.chmod(0o400)
        result = subprocess.run([harness, str(source), str(stage)])
        if result.returncode == 77:
            print("SKIP: fixture filesystem does not support APFS clone staging")
            return
        result.check_returncode()
        assert not subprocess.check_output(["/usr/bin/xattr", str(stage)]).strip()
        acl = subprocess.check_output(["/bin/ls", "-le", str(stage)], text=True)
        assert "everyone allow" not in acl, acl
        assert not list(root.glob("*.basis.*"))
        print("staging: no inherited xattrs, resource fork, ACL or snapshot paths")
        # The old destination ACL may deny writing even after mode 0600 is
        # applied. Clear it on the private readonly clone descriptor before
        # reopening that same inode for writes; leave the live source alone.
        source.chmod(0o600)
        subprocess.run(["/bin/chmod", "+a", "everyone deny write,append", str(source)], check=True)
        source.chmod(0o400)
        protected_stage = root / "acl-stage"
        try:
            subprocess.run([harness, str(source), str(protected_stage), "--readonly-source"], check=True)
            acl = subprocess.check_output(["/bin/ls", "-le", str(protected_stage)], text=True)
            assert "deny write" not in acl, acl
        finally:
            subprocess.run(["/bin/chmod", "-N", str(source)], check=True)
        print("write-denying ACL: only private clone permissions relaxed")
        subprocess.run(["/usr/bin/chflags", "nodump", str(source)], check=True)
        unsupported = root / "unsupported"
        try:
            result = subprocess.run([harness, str(source), str(unsupported)])
            assert result.returncode == 77
            assert not unsupported.exists()
            assert not list(root.glob("*.basis.*"))
        finally:
            subprocess.run(["/usr/bin/chflags", "0", str(source)], check=True)
        print("flagged basis: declined without output or snapshot leftovers")


if __name__ == "__main__":
    main()
