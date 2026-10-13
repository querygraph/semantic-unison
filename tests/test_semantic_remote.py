#!/usr/bin/env python3
"""Negotiated remote SDE and optional unmodified-peer fallback fixtures.

Usage: python3 tests/test_semantic_remote.py MODIFIED_UNISON [STOCK_UNISON]
All files and archive state are synthetic and disposable; no SSH server used.
"""
from pathlib import Path
import os
import struct
import subprocess
import sys
import tempfile


def fixture(value=b"one", opaque=65):
    b = bytearray(2 * 1024 * 1024)
    struct.pack_into("<2sHIH", b, 0, b"II", 42, 8, 4)
    xmp = b"<x>" + value + b"</x>" + b" " * 32
    for i, entry in enumerate([(273, 4, 1, 4096), (279, 4, 1, 1024),
                               (700, 1, len(xmp), 1024), (50706, 1, 4, 1025)]):
        struct.pack_into("<HHII", b, 10 + i * 12, *entry)
    b[1024:1024 + len(xmp)] = xmp
    b[4096:5120] = b"R" * 1024
    b[-1] = opaque
    return bytes(b)


def exercise(client, server, semantic):
    with tempfile.TemporaryDirectory(prefix="unison-sde-remote-", dir="/private/tmp") as tmp:
        root = Path(tmp)
        left, right = root / "left", root / "right"
        left.mkdir(); right.mkdir()
        state = root / "state"; state.mkdir()
        launcher = root / "loopback.py"
        launcher.write_text("#!/usr/bin/env python3\nimport os,sys\n"
                            "a=sys.argv[1:]\ni=a.index(" + repr(server) + ")\n"
                            "os.execv(a[i],a[i:])\n")
        launcher.chmod(0o700)
        env = dict(os.environ, UNISON=str(state))
        command = [client, str(left), "ssh://localhost/" + str(right),
                   "-sshcmd", str(launcher), "-servercmd", server,
                   "-batch", "-auto", "-fastcheck", "false", "-times",
                   "-debug", "semantic", "-semanticdng"]
        def sync(expect=False):
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
            log = result.stdout + result.stderr
            assert result.returncode == 0, log
            used = "Remote semantic clone wrote" in log
            assert used == expect, log
            assert not list(right.glob("*sde*.unison.tmp"))
            assert not list(left.glob("*sde*.unison.tmp"))
            return log
        a = left / "image.dng"; b = right / "image.dng"
        a.write_bytes(fixture()); sync()
        a.write_bytes(fixture(b"two")); sync(semantic)
        assert b.read_bytes() == a.read_bytes()
        print("remote receiver: XMP exact transfer" if semantic else "stock receiver: exact fallback")
        b.write_bytes(fixture(b"six")); sync(semantic)
        assert a.read_bytes() == b.read_bytes()
        print("local receiver: XMP exact transfer" if semantic else "stock source: exact fallback")
        a.write_bytes(fixture(b"new", opaque=90)); sync()
        assert b.read_bytes() == a.read_bytes()
        print("opaque edit: ordinary exact fallback")
        a.write_bytes(fixture(b"longer packet", opaque=90)); sync()
        assert b.read_bytes() == a.read_bytes()
        print("XMP layout change: ordinary exact fallback")
        previous = b.stat().st_ino
        sync()
        assert b.stat().st_ino == previous
        print("second sync: no replacement")


def exercise_local_source_clone(binary):
    with tempfile.TemporaryDirectory(prefix="unison-sde-local-", dir="/private/tmp") as tmp:
        root = Path(tmp)
        left, right = root / "left", root / "right"
        left.mkdir(); right.mkdir()
        state = root / "state"; state.mkdir()
        env = dict(os.environ, UNISON=str(state))
        command = [binary, str(left), str(right), "-batch", "-auto",
                   "-fastcheck", "false", "-times", "-debug", "copy",
                   "-debug", "semantic", "-semanticdng"]
        source, target = left / "image.dng", right / "image.dng"
        def sync():
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
            assert result.returncode == 0, result.stdout + result.stderr
            return result.stdout + result.stderr
        source.write_bytes(fixture()); sync()
        source.write_bytes(fixture(b"two")); source.chmod(0o400)
        log = sync()
        assert "Local source clone completed before semantic planning" in log, log
        assert "Local semantic workers wrote" not in log, log
        assert target.read_bytes() == source.read_bytes()
        assert target.stat().st_mode & 0o777 == 0o400
        inode = target.stat().st_ino
        sync()
        assert target.stat().st_ino == inode
        print("local source clone: priority, exact bytes/properties, stable second sync")


def exercise_bidirectional_admission(binary):
    """Saturate both peer consumer queues while each must serve source plans."""
    with tempfile.TemporaryDirectory(prefix="unison-sde-bidirectional-", dir="/private/tmp") as tmp:
        root = Path(tmp)
        left, right, state = (root / name for name in ("left", "right", "state"))
        for directory in (left, right, state):
            directory.mkdir()
        launcher = root / "loopback.py"
        launcher.write_text("#!/usr/bin/env python3\nimport os,sys\n"
                            "a=sys.argv[1:]\ni=a.index(" + repr(binary) + ")\n"
                            "os.execv(a[i],a[i:])\n")
        launcher.chmod(0o700)
        command = [binary, str(left), "ssh://localhost/" + str(right),
                   "-sshcmd", str(launcher), "-servercmd", binary, "-batch", "-auto",
                   "-fastcheck", "false", "-times", "-semanticdng", "-debug", "semantic",
                   "-semanticworkers", "2", "-semanticmaxinflight", "3", "-maxthreads", "24"]
        env = dict(os.environ, UNISON=str(state))
        def sync(payload_mib, descriptors, expect_runtime=False):
            result = subprocess.run(command + ["-semanticpayloadbudget", str(payload_mib),
                                               "-semanticdescriptorbudget", str(descriptors)],
                                    env=env, capture_output=True, text=True, timeout=90)
            log = result.stdout + result.stderr
            assert result.returncode == 0, log
            if expect_runtime:
                assert "2 CPU permits, 2 domains, 3 transaction slots" in log, log
            for directory in (left, right):
                leftovers = [path.name for path in directory.iterdir()
                             if path.name not in names]
                assert not leftovers, leftovers
            return log
        names = [f"image-{i:02d}.dng" for i in range(24)]
        for i, name in enumerate(names):
            # Distinct preserved bytes prevent ordinary fingerprint reuse from
            # satisfying every transfer with just one semantic result per side.
            (left / name).write_bytes(fixture(opaque=65 + i))
        sync(26, 24)
        # Sorted paths alternate transfer direction, placing both directions in
        # the same 24-transfer dispatch window. Every stage has the same layout.
        for payload_mib, descriptors, even, odd in ((26, 24, b"two", b"six"),
                                                    (17, 16, b"new", b"ten")):
            expected = {}
            for i, name in enumerate(names):
                contents = fixture(even if i % 2 == 0 else odd, opaque=65 + i)
                ((left if i % 2 == 0 else right) / name).write_bytes(contents)
                expected[name] = contents
            log = sync(payload_mib, descriptors, expect_runtime=True)
            assert log.count("Remote semantic clone wrote") == len(names), log
            for name, contents in expected.items():
                assert (left / name).read_bytes() == contents
                assert (right / name).read_bytes() == contents
            inodes = {(directory, name): (directory / name).stat().st_ino
                      for directory in (left, right) for name in names}
            assert "Remote semantic clone wrote" not in sync(payload_mib, descriptors)
            assert all((directory / name).stat().st_ino == inode
                       for (directory, name), inode in inodes.items())
        print("bidirectional SDE: 24 exact files, saturated transaction/payload/FD budgets, stable retry and no stages")


if __name__ == "__main__":
    current = str(Path(sys.argv[1]).resolve())
    exercise_local_source_clone(current)
    exercise(current, current, True)
    exercise_bidirectional_admission(current)
    if len(sys.argv) > 2:
        exercise(current, str(Path(sys.argv[2]).resolve()), False)
