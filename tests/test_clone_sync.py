#!/usr/bin/env python3
"""Disposable APFS clone/rsync integration tests; no SSH server or photo inputs.

Usage: python3 tests/test_clone_sync.py /absolute/path/to/built/unison
Build the supplied native test separately against the same copy_stubs.o to
exercise descriptor and property behavior. All sync state lives under /tmp.
"""
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import re
import signal
import time


def main():
    binary = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory(prefix="unison-clone-test-", dir="/private/tmp") as tmp:
        root = Path(tmp)
        left, right = root / "left", root / "right"
        left.mkdir(); right.mkdir()
        state = root / "state"; state.mkdir()
        loopback = root / "loopback.py"
        loopback.write_text("#!/usr/bin/env python3\nimport os,sys,subprocess,time\n"
                            "a=sys.argv[1:]\n"
                            "i=a.index(" + repr(binary) + ")\n"
                            "if os.getenv('UNISON_TEST_THROTTLE'):\n"
                            " p=subprocess.Popen(a[i:],stdout=subprocess.PIPE)\n"
                            " while True:\n"
                            "  b=p.stdout.read1(4096)\n"
                            "  if not b: break\n"
                            "  sys.stdout.buffer.write(b); sys.stdout.buffer.flush(); time.sleep(0.1)\n"
                            " sys.exit(p.wait())\n"
                            "os.execv(a[i],a[i:])\n")
        loopback.chmod(0o700)
        env = dict(os.environ, UNISON=str(state))
        command = [binary, str(left), "ssh://localhost/" + str(right),
                   "-sshcmd", str(loopback), "-servercmd", binary,
                   "-batch", "-auto", "-fastcheck", "false",
                   "-times", "-debug", "copy", "-clone", "auto"]
        def check_inventory():
            for directory in (left, right):
                actual = {path.name for path in directory.iterdir()}
                assert actual == {"ordinary.bin"}, (str(directory), actual)
        def sync(expect_clone=False):
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            if expect_clone and "Using immutable receiver clone basis" not in result.stderr + result.stdout:
                raise AssertionError("clone path not exercised\n" + result.stdout + result.stderr)
            check_inventory()
            return result.stdout + result.stderr
        rng = random.Random(98231)
        original = rng.randbytes(2 * 1024 * 1024)
        (left / "ordinary.bin").write_bytes(original)
        sync()
        cases = [
            ("same offset edit", original[:15000] + b"CHANGED!" + original[15008:]),
            ("insert prefix", b"inserted prefix" + original),
            ("delete prefix", original[193:]),
            ("duplicate shifted blocks", original[65536:] + original[:65536]),
            ("all literals", rng.randbytes(len(original))),
            ("shorten EOF", original[:800000]),
            ("extend EOF", original + b"new end" * 10000),
        ]
        for label, data in cases:
            (left / "ordinary.bin").write_bytes(data)
            log = sync(expect_clone=True)
            if label == "same offset edit":
                counts = re.findall(r"Receiver clone preserved (\d+) logical bytes", log)
                assert counts and int(counts[-1]) > len(data) // 2, log
            assert (right / "ordinary.bin").read_bytes() == data, label
            print(label + ": exact bytes and cleaned staging")
        previous = (right / "ordinary.bin").stat().st_ino
        sync()
        assert (right / "ordinary.bin").stat().st_ino == previous, "second sync changed inode"
        print("second sync: no replacement")

        alias = root / "old-hardlink"
        os.link(right / "ordinary.bin", alias)
        saved = alias.read_bytes()
        data = saved[:9000] + b"new hardlink update" + saved[9019:]
        (left / "ordinary.bin").write_bytes(data)
        sync(expect_clone=True)
        assert alias.read_bytes() == saved
        assert (right / "ordinary.bin").read_bytes() == data
        assert alias.stat().st_ino != (right / "ordinary.bin").stat().st_ino
        print("hardlinks: old inode unchanged, destination replaced")

        command[-1] = "off"
        (left / "ordinary.bin").write_bytes(original)
        log = sync()
        assert "Using immutable receiver clone basis" not in log
        assert (right / "ordinary.bin").read_bytes() == original
        print("clone=off: ordinary transfer remains exact")

        command[-1] = "require"
        subprocess.run(["/usr/bin/chflags", "nodump", str(right / "ordinary.bin")], check=True)
        (left / "ordinary.bin").write_bytes(data)
        failed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
        assert failed.returncode != 0
        assert "cannot clone this basis" in failed.stdout + failed.stderr
        assert (right / "ordinary.bin").read_bytes() == original
        check_inventory()
        command[-1] = "auto"
        log = sync()
        assert "Using immutable receiver clone basis" not in log
        assert (right / "ordinary.bin").read_bytes() == data
        subprocess.run(["/usr/bin/chflags", "0", str(right / "ordinary.bin")], check=True)
        print("unsupported flagged basis: require fails safely, auto falls back")

        # Kill both sides after staging exists. A partial clone must never be
        # published or subsequently trusted as an ordinary resumable prefix.
        target = rng.randbytes(8 * 1024 * 1024)
        (left / "ordinary.bin").write_bytes(target)
        interrupted = subprocess.Popen(command, env=dict(env, UNISON_TEST_THROTTLE="1"),
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       start_new_session=True)
        try:
            deadline = time.monotonic() + 15
            while not list(right.glob("*clone*.unison.tmp")):
                assert interrupted.poll() is None, "transfer ended before interruption"
                assert time.monotonic() < deadline, "clone stage not observed"
                time.sleep(0.02)
            os.killpg(interrupted.pid, signal.SIGKILL)
            interrupted.wait(timeout=10)
        finally:
            if interrupted.poll() is None:
                os.killpg(interrupted.pid, signal.SIGKILL)
                interrupted.wait(timeout=10)
        assert (right / "ordinary.bin").read_bytes() == data
        # SIGKILL intentionally leaves archive locks, so explicitly recover
        # locks only in this disposable fixture.
        command += ["-ignorelocks"]
        sync(expect_clone=True)
        assert (right / "ordinary.bin").read_bytes() == target
        print("interruption: destination untouched, retry rebuilt clone exactly")


if __name__ == "__main__":
    main()
