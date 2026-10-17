#!/usr/bin/env python3
"""Harness-owned server: retain faults, cancel, and reap its native child."""
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import subprocess
import threading
import time

from measure import receipt
from ownership import NativeChild


def exact(connection, length, check):
    result = bytearray()
    while len(result) < length:
        check()
        try:
            data = connection.recv(length - len(result))
        except socket.timeout:
            continue
        if not data:
            raise RuntimeError("short launcher control header")
        result.extend(data)
    return bytes(result)


def main():
    before = time.monotonic()
    deadline = before + float(os.environ.get("UNISON_SYNC_BENCH_DEADLINE_SECONDS", "180"))
    cancelled = threading.Event()
    signals = []
    errors = []
    fault = None
    endpoint = connection = native = thread = None
    command = None
    server_group_binding = None
    length = None
    counts = {"client_to_server_bytes": 0, "server_to_client_bytes": 0}
    cleanup = usage = None

    def request_cancel(number, _frame):
        signals.append(number)
        cancelled.set()

    signal.signal(signal.SIGTERM, request_cancel)
    signal.signal(signal.SIGINT, request_cancel)

    def check():
        if errors:
            raise RuntimeError(errors[0])
        if cancelled.is_set():
            raise RuntimeError("supervisor cancellation signal " + repr(signals))
        if time.monotonic() >= deadline:
            raise TimeoutError("native server deadline")

    try:
        endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        endpoint.bind(os.environ["UNISON_SYNC_BENCH_SOCKET"])
        endpoint.listen(1)
        endpoint.settimeout(0.05)
        while connection is None:
            check()
            try:
                connection, _ = endpoint.accept()
            except socket.timeout:
                pass
        endpoint.close()
        endpoint = None
        connection.settimeout(0.05)
        length = struct.unpack(">I", exact(connection, 4, check))[0]
        if length > 8192:
            raise RuntimeError("launcher control header limit")
        arguments = json.loads(exact(connection, length, check))
        binary = os.environ["UNISON_SYNC_BENCH_BINARY"]
        if not isinstance(arguments, list) or not arguments or arguments[0] != binary or "-server" not in arguments:
            raise RuntimeError("unexpected native server command")
        command = arguments + json.loads(os.environ["UNISON_SYNC_BENCH_SERVER_FLAGS"])
        native = NativeChild(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=None, bufsize=0)
        # NativeChild inherits this retained supervisor's group. Observe that
        # binding while the child PID is still reserved, before any wait4.
        server_group_binding = {"native_pid": native.pid,
            "native_process_group": os.getpgid(native.pid),
            "supervisor_pid": os.getpid(), "supervisor_process_group": os.getpgrp(),
            "observed_before_native_reap": native.status is None}
        if (server_group_binding["native_process_group"] != os.getpid()
                or server_group_binding["supervisor_process_group"] != os.getpid()):
            raise RuntimeError("native server not in retained supervisor group")
        # These hooks are only used by the synthetic failure controls. A fault
        # always rejects a measurement and is retained in its receipt.
        injection = os.environ.get("UNISON_SYNC_BENCH_FAULT")
        pid_path = os.environ.get("UNISON_SYNC_BENCH_CHILD_PID_FILE")
        if pid_path:
            Path(pid_path).write_text(json.dumps({"pid": native.pid, "supervisor_pid": os.getpid()}))
        if injection == "supervisor-exit":
            os._exit(73)

        def input_pump():
            try:
                while not cancelled.is_set():
                    try:
                        data = connection.recv(65536)
                    except socket.timeout:
                        continue
                    if not data:
                        break
                    position = 0
                    while position < len(data):
                        written = os.write(native.process.stdin.fileno(), data[position:])
                        if not written:
                            raise BrokenPipeError("zero-byte server input write")
                        counts["client_to_server_bytes"] += written
                        position += written
            except BaseException as error:
                if not cancelled.is_set():
                    errors.append("input pump: " + repr(error))
                    cancelled.set()
            finally:
                native.process.stdin.close()

        thread = threading.Thread(target=input_pump, daemon=True)
        thread.start()
        while True:
            check()
            ready, _, _ = select.select([native.process.stdout.fileno()], [], [], 0.025)
            if not ready:
                continue
            data = os.read(native.process.stdout.fileno(), 65536)
            if not data:
                break
            if injection == "output-pump":
                raise RuntimeError("injected output pump failure")
            position = 0
            while position < len(data):
                check()
                try:
                    written = connection.send(data[position:])
                except socket.timeout:
                    continue
                if not written:
                    raise BrokenPipeError("zero-byte client protocol write")
                counts["server_to_client_bytes"] += written
                position += written
    except BaseException as error:
        fault = repr(error)
    finally:
        # Even a transport exception must settle the exact native child before
        # this supervisor can exit. SIGTERM runs this path; a deadline never
        # relies on killing supervisor and native together as reap evidence.
        cancelled.set()
        if connection is not None:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if native is not None:
            # Allow ordinary native shutdown after EOF, without extending the
            # protocol deadline or delaying a known fault's TERM. The outer
            # owner permits five seconds for supervisor settlement; at most
            # two here leaves room for TERM/KILL and the input-pump join.
            normal_wait = max(0.0, min(2.0, deadline - time.monotonic()))
            cleanup, usage = native.finish(cancel_reason=fault,
                                          normal_exit_timeout=normal_wait)
            if cleanup["cancel_reason"] and fault is None:
                fault = cleanup["cancel_reason"]
        if thread is not None:
            thread.join(timeout=1)
            if thread.is_alive() and fault is None:
                fault = "input pump did not settle"
        if native is not None:
            if native.process.stdin and not native.process.stdin.closed:
                native.process.stdin.close()
            native.process.stdout.close()
        if connection is not None:
            connection.close()
        if endpoint is not None:
            endpoint.close()
    result = {"schema": "unison-loopback-protocol-count/1", "server_command": command,
              "server_pid": native.pid if native else None,
              "server_returncode": cleanup["returncode"] if cleanup else None,
              "server_cleanup": cleanup, "fault": fault,
              "server_group_binding": server_group_binding,
              "forwarded_protocol_bytes": counts,
              "server_wall_seconds": time.monotonic() - before,
              "server_resources": receipt(usage) if usage else None,
              "pump_errors": errors, "cancellation_signals": signals,
              "input_pump_joined": thread is None or not thread.is_alive(),
              "launcher_control_header_bytes_excluded": 4 + length if length is not None else None}
    output = Path(os.environ["UNISON_SYNC_BENCH_PROXY_RECEIPT"])
    temporary = output.with_suffix(".new")
    temporary.write_text(json.dumps(result) + "\n")
    temporary.replace(output)
    raise SystemExit(70 if fault else cleanup["returncode"] if cleanup else 70)


if __name__ == "__main__":
    main()
