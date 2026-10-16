#!/usr/bin/env python3
"""Disposable ssh-command shim for the benchmark's harness-owned Unix socket."""
import json
import os
import socket
import struct
import sys
import threading


def main():
    arguments = sys.argv[1:]
    index = arguments.index(os.environ["UNISON_SYNC_BENCH_BINARY"])
    command = json.dumps(arguments[index:]).encode("utf-8")
    if len(command) > 8192:
        raise RuntimeError("launcher control header limit")
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(os.environ["UNISON_SYNC_BENCH_SOCKET"])
    connection.sendall(struct.pack(">I", len(command)) + command)

    def input_pump():
        try:
            while True:
                data = os.read(sys.stdin.fileno(), 65536)
                if not data:
                    break
                connection.sendall(data)
        except BrokenPipeError:
            pass
        finally:
            try:
                connection.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    threading.Thread(target=input_pump, daemon=True).start()
    while True:
        data = connection.recv(65536)
        if not data:
            break
        position = 0
        while position < len(data):
            amount = os.write(sys.stdout.fileno(), data[position:])
            if not amount:
                raise BrokenPipeError("zero-byte launcher output write")
            position += amount


if __name__ == "__main__":
    main()
