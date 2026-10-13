#!/usr/bin/env python3
"""Explicit CLI diff/details observations with disposable current file pairs.

Usage: python3 tests/test_semantic_reports.py MODIFIED_UNISON [OLD_PEER]
Scripted d/x/q requests exercise the real owner/UI/RPC path; quit preserves
both conflicting current files. A marker distinguishes ordinary external diff.
"""
from pathlib import Path
import hashlib
import os
import shlex
import struct
import subprocess
import sys
import tempfile


def fixture(value=b"one", opaque=65):
    data = bytearray(2 * 1024 * 1024)
    struct.pack_into("<2sHIH", data, 0, b"II", 42, 8, 4)
    packet = b"<x>" + value + b"</x>" + b" " * 32
    for i, entry in enumerate(((273, 4, 1, 4096), (279, 4, 1, 1024),
                               (700, 1, len(packet), 1024), (50706, 1, 4, 1025))):
        struct.pack_into("<HHII", data, 10 + i * 12, *entry)
    data[1024:1024 + len(packet)] = packet
    data[4096:5120] = b"R" * 1024
    data[-1] = opaque
    return bytes(data)


def exercise(binary, peer, name, original, changed_left, changed_right,
             classification=None, external=False, remote=False, unavailable=False, profile=None,
             expected_meaning=()):
    with tempfile.TemporaryDirectory(prefix="unison-semantic-ui-", dir="/private/tmp") as tmp:
        root = Path(tmp)
        left, right, state = (root / p for p in ("left", "right", "state"))
        for directory in (left, right, state):
            directory.mkdir()
        marker = root / "external-diff-called"
        diff = root / "ordinary_diff.py"
        diff.write_text("from pathlib import Path\n"
                        "Path(" + repr(str(marker)) + ").write_text('called')\n"
                        "print('ORDINARY_EXTERNAL_DIFF')\n")
        launcher = root / "loopback.py"
        launcher.write_text("#!/usr/bin/env python3\nimport os,sys\n"
                            "a=sys.argv[1:]\ni=a.index(" + repr(peer) + ")\n"
                            "os.execv(a[i],a[i:])\n")
        launcher.chmod(0o700)
        destination = "ssh://localhost/" + str(right) if remote else str(right)
        command = [binary, str(left), destination, "-ui", "text", "-fastcheck", "false",
                   "-times", "-semanticworkers", "2",
                   "-diff", shlex.quote(sys.executable) + " " + shlex.quote(str(diff)) + " CURRENT1 CURRENT2"]
        command += ["-semanticprofile", profile] if profile else ["-semanticdng"]
        if remote:
            command += ["-sshcmd", str(launcher), "-servercmd", peer]
        env = dict(os.environ, UNISON=str(state)); env.pop("PAGER", None)
        a, b = left / name, right / name
        a.write_bytes(original)
        first = subprocess.run(command + ["-batch", "-auto"], env=env,
                               capture_output=True, text=True, timeout=90)
        assert first.returncode == 0, first.stdout + first.stderr
        assert b.read_bytes() == original
        a.write_bytes(changed_left); b.write_bytes(changed_right)
        before = {p: (p.stat().st_ino, hashlib.sha256(p.read_bytes()).digest()) for p in (a, b)}
        action = subprocess.run(command, input="d\nx\nq\n", env=env,
                                capture_output=True, text=True, timeout=90)
        log = action.stdout + action.stderr
        for expected in expected_meaning:
            assert expected in log, log
        assert action.returncode == 3, log  # normal explicit quit
        assert log.count("<-?->") >= 3, log  # inspection does not resolve the conflict
        assert marker.exists() == external, log
        if external:
            assert "ORDINARY_EXTERNAL_DIFF" in log, log
        else:
            assert log.count("Semantic observation of the current replicas' data forks") >= 2, log
            assert "Profile: " + (profile or "org.firstpair.dng-xmp/1") in log, log
            assert "without an archived base" in log, log
        if classification:
            assert classification in log, log
        if unavailable:
            assert "Peer does not support negotiated semantic inspection" in log, log
        for path, (inode, digest) in before.items():
            assert path.stat().st_ino == inode
            assert hashlib.sha256(path.read_bytes()).digest() == digest
        assert set(p.name for p in left.iterdir()) == {name}
        assert set(p.name for p in right.iterdir()) == {name}
        print(f"CLI diff/details: {'remote' if remote else 'local'} {name}; "
              f"{'ordinary diff' if external else 'semantic observation'}; unchanged conflict and files")


def main():
    binary = str(Path(sys.argv[1]).resolve())
    metadata = "Classification: editable metadata differs; all bytes outside those regions match."
    other = "Classification: other bytes or the editable-region layout differ."
    cases = [
        ("photo.dng", fixture(), fixture(b"two"), fixture(b"six"), metadata, False),
        ("opaque.dng", fixture(), fixture(b"two", opaque=90), fixture(b"six"), other, False),
        ("growth.dng", fixture(), fixture(b"longer packet"), fixture(b"six"), other, False),
        ("unsupported.dng", b"not a DNG baseline", b"not a DNG left", b"not a DNG right", "unsupported:", False),
        ("renamed.bin", fixture(), fixture(b"two"), fixture(b"six"), metadata, False),
        ("ordinary.txt", b"baseline\n", b"left text\n", b"right text\n", None, True),
    ]
    for remote in (False, True):
        for name, original, left, right, expected, external in cases:
            exercise(binary, binary, name, original, left, right, expected, external, remote)
    if len(sys.argv) > 2:
        old = str(Path(sys.argv[2]).resolve())
        exercise(binary, old, "old-peer.dng", fixture(), fixture(b"two"), fixture(b"six"),
                 remote=True, unavailable=True)
        exercise(binary, old, "ordinary.txt", b"baseline\n", b"left text\n", b"right text\n",
                 external=True, remote=True)


if __name__ == "__main__":
    main()
