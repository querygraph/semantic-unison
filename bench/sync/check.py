#!/usr/bin/env python3
"""Small Adobe-free independent fixture, capture and transport controls."""
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time

from fixtures import create, edit, packet, sha256
import measure
from measure import run
from run import InvocationFailure, internal_counters, measure_invocation

HERE = Path(__file__).resolve().parent


def rejected(function):
    try:
        function()
    except AssertionError:
        return
    raise AssertionError("wrong materializer outcome admitted")


def main():
    with tempfile.TemporaryDirectory(prefix="unison-sync-controls-", dir="/private/tmp") as temporary:
        work = Path(temporary)
        fixture = work / "synthetic.dng"
        description = create(fixture, 1048576, 8192, 0)
        before = fixture.read_bytes()
        target_digest = edit(fixture, description)
        after = fixture.read_bytes()
        start, size = description["packet_offset"], description["packet_bytes"]
        assert before[:start] == after[:start] and before[start + size:] == after[start + size:]
        assert before[start:start + size] == packet(size, 1)
        assert after[start:start + size] == packet(size, 2)
        assert target_digest == sha256(fixture) != description["before_sha256"]
        result = run([sys.executable, "-c", "import os;os.write(1,b'A'*131072);os.write(2,b'B'*131072)"],
                     os.environ.copy(), 5, max_output=1024)
        assert result["returncode"] == 0 and result["capture_truncated"]
        assert result["capture_bytes"] == {"stdout": 131072, "stderr": 131072}
        assert result["stdout"] == "A" * 1024 and result["stderr"] == "B" * 1024
        timeout = run([sys.executable, "-c", "import time;time.sleep(10)"], os.environ.copy(), 0.05)
        assert timeout["timed_out"] and timeout["returncode"] < 0
        capture_creation_controls()
        missing = internal_counters("", "ordinary", 2, 2097152)
        assert missing["semantic_logical_write_bytes"] is None
        assert missing["materialization_non_inherited_logical_bytes_model"] == 4194304
        rejected(lambda: internal_counters("", "semantic", 2, 2097152))
        rejected(lambda: internal_counters("Using immutable receiver clone basis\n"
                     "Receiver clone preserved 1048576 logical bytes\n", "receiver-clone", 2, 2097152))
        rejected(lambda: internal_counters("Local source clone completed before semantic planning\n",
                                           "ordinary", 1, 2097152))
        semantic_trace = "Remote semantic clone wrote 3072 logical metadata bytes in 1 write calls (8192 payload bytes; 4096-byte comparison windows; org.firstpair.dng-xmp/0)\n"
        receiver_trace = "Using immutable receiver clone basis\nReceiver clone preserved 2088960 logical bytes\n"
        source_trace = "Local source clone completed before semantic planning\n"
        for mode in ("ordinary", "reference"):
            rejected(lambda mode=mode: internal_counters("Receiver clone preserved 2088960 logical bytes\n",
                                                         mode, 1, 2097152))
        for mode, trace in (("semantic", semantic_trace + receiver_trace),
                            ("semantic", semantic_trace + source_trace),
                            ("receiver-clone", receiver_trace + semantic_trace),
                            ("receiver-clone", receiver_trace + source_trace),
                            ("source-clone", source_trace + semantic_trace),
                            ("source-clone", source_trace + receiver_trace)):
            rejected(lambda mode=mode, trace=trace: internal_counters(trace, mode, 1, 2097152))
        # An independent echo process establishes the counted protocol bytes
        # and the deliberately excluded launcher control header.
        fake = work / "echo.py"
        fake.write_text("#!/usr/bin/env python3\nimport os,sys\n"
                        "while True:\n"
                        " data=os.read(0,65536)\n"
                        " if not data:break\n"
                        " os.write(1,data)\n")
        fake.chmod(0o700)
        for code in (0, 19):
            if code:
                fake.write_text("#!/usr/bin/env python3\nraise SystemExit(19)\n")
            path = work / (str(code) + ".sock")
            receipt_path = work / (str(code) + ".json")
            env = dict(os.environ, UNISON_SYNC_BENCH_BINARY=str(fake),
                       UNISON_SYNC_BENCH_SOCKET=str(path),
                       UNISON_SYNC_BENCH_PROXY_RECEIPT=str(receipt_path),
                       UNISON_SYNC_BENCH_SERVER_FLAGS="[]")
            client = (
                "import hashlib,json,os,socket,struct\n"
                "s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)\n"
                "s.connect(os.environ['UNISON_SYNC_BENCH_SOCKET'])\n"
                "h=json.dumps([os.environ['UNISON_SYNC_BENCH_BINARY'],'-server']).encode()\n"
                "s.sendall(struct.pack('>I',len(h))+h)\n"
                "p=bytes(range(256))*257 if os.environ['ECHO_BYTES']=='yes' else b''\n"
                "s.sendall(p);s.shutdown(socket.SHUT_WR);r=bytearray()\n"
                "while True:\n"
                " b=s.recv(65536)\n"
                " if not b:break\n"
                " r.extend(b)\n"
                "assert bytes(r)==p\n")
            try:
                outcome = measure_invocation([sys.executable, "-c", client],
                    dict(env, ECHO_BYTES="yes" if not code else "no"), 3, HERE / "proxy.py")
            except InvocationFailure as error:
                assert code == 19
                outcome = error.outcome
            else:
                assert code == 0
            proof = outcome["proxy"]
            payload = bytes(range(256)) * 257 if not code else b""
            control = json.dumps([str(fake), "-server"]).encode()
            assert proof["forwarded_protocol_bytes"] == {
                "client_to_server_bytes": len(payload), "server_to_client_bytes": len(payload)}
            assert proof["server_returncode"] == code and proof["input_pump_joined"]
            assert proof["server_cleanup"]["reaped"] and proof["fault"] is None
            absent(proof["server_pid"])
            assert proof["launcher_control_header_bytes_excluded"] == 4 + len(control)
            assert not proof["pump_errors"]
        failure_controls(work)
    print("Fixture/capture, mixed-mode rejection, exact traffic, native exit and four failure ownership controls pass.")


def capture_creation_controls():
    original_group, original_capture = measure.OwnedGroup, measure.CapturedStream
    for failure_index in (0, 1):
        owned = []
        calls = 0

        class RecordingGroup(original_group):
            def __init__(self, *arguments, **keywords):
                super().__init__(*arguments, **keywords)
                owned.append(self)

        def capture(*arguments, **keywords):
            nonlocal calls
            current = calls
            calls += 1
            if current == failure_index:
                raise RuntimeError("injected captured reader creation failure")
            return original_capture(*arguments, **keywords)

        measure.OwnedGroup, measure.CapturedStream = RecordingGroup, capture
        try:
            try:
                run([sys.executable, "-c", "import time;time.sleep(10)"], os.environ.copy(), 3)
            except RuntimeError as error:
                assert "reader creation failure" in str(error)
            else:
                raise AssertionError("reader creation failure did not escape")
            assert len(owned) == 1 and owned[0].reaped
            absent(owned[0].pid)
        finally:
            measure.OwnedGroup, measure.CapturedStream = original_group, original_capture


def absent(pid):
    deadline = time.monotonic() + 3
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        assert time.monotonic() < deadline, "exact native PID survived owned cleanup"
        time.sleep(0.005)


def failure_controls(work):
    native = work / "hang.py"
    native.write_text("#!/usr/bin/env python3\nimport os,signal,time\n"
                      "signal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
                      "os.write(1,b'READY')\n"
                      "while True:time.sleep(1)\n")
    native.chmod(0o700)
    client = (
        "import json,os,socket,struct,time\n"
        "s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)\n"
        "s.connect(os.environ['UNISON_SYNC_BENCH_SOCKET'])\n"
        "h=json.dumps([os.environ['UNISON_SYNC_BENCH_BINARY'],'-server']).encode()\n"
        "s.sendall(struct.pack('>I',len(h))+h)\n"
        "while s.recv(65536):pass\n")
    observed = []
    for kind in ("output-pump", "deadline", "client-timeout", "supervisor-exit"):
        socket_path, pid_path, receipt_path = [work / (kind + suffix) for suffix in (".sock", ".pid", ".json")]
        env = dict(os.environ, UNISON_SYNC_BENCH_BINARY=str(native),
                   UNISON_SYNC_BENCH_SOCKET=str(socket_path),
                   UNISON_SYNC_BENCH_PROXY_RECEIPT=str(receipt_path),
                   UNISON_SYNC_BENCH_SERVER_FLAGS="[]",
                   UNISON_SYNC_BENCH_CHILD_PID_FILE=str(pid_path),
                   UNISON_SYNC_BENCH_DEADLINE_SECONDS="0.5" if kind == "deadline" else "10")
        if kind in ("output-pump", "supervisor-exit"):
            env["UNISON_SYNC_BENCH_FAULT"] = kind
        try:
            measure_invocation([sys.executable, "-c", client], env,
                               0.15 if kind == "client-timeout" else 3, HERE / "proxy.py")
        except InvocationFailure as error:
            outcome = error.outcome
        else:
            raise AssertionError("injected ownership failure admitted a measurement")
        identity = json.loads(pid_path.read_text())
        absent(identity["pid"])
        settled = outcome["supervisor_cleanup"]
        assert settled["pid"] == identity["supervisor_pid"] and settled["reaped"]
        assert settled["group_cleanup_before_leader_reap"]
        try:
            os.waitpid(settled["pid"], os.WNOHANG)
        except ChildProcessError:
            pass
        else:
            raise AssertionError("supervisor was not already reaped")
        proof = outcome["proxy"]
        if kind == "supervisor-exit":
            assert proof is None and settled["returncode"] == 73
            # Group cleanup kills the orphan; parent has no native wait4 proof
            # on Darwin and must never present this as native-owner reap.
            owned_native_reap = False
        else:
            assert proof["server_pid"] == identity["pid"] and proof["fault"]
            assert proof["server_cleanup"]["reaped"] and proof["input_pump_joined"]
            assert proof["server_cleanup"]["returncode"] < 0
            if kind == "output-pump":
                assert "injected output pump failure" in proof["fault"]
            if kind == "deadline":
                assert "native server deadline" in proof["fault"]
            if kind == "client-timeout":
                assert outcome["timed_out"] and proof["cancellation_signals"]
            owned_native_reap = True
        observed.append({"control": kind, "native_pid": identity["pid"],
                         "exact_native_pid_absent": True, "native_owner_reap_attested": owned_native_reap,
                         "supervisor_reaped": True, "outcome": outcome})
    if os.environ.get("UNISON_SYNC_CONTROLS_OUTPUT"):
        Path(os.environ["UNISON_SYNC_CONTROLS_OUTPUT"]).write_text(json.dumps(observed, indent=2) + "\n")


if __name__ == "__main__":
    main()
