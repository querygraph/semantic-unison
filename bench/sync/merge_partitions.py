#!/usr/bin/env python3
"""Offline row-accounting merge; never dispatches Unison or releases resources."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

from batch_audit import require
from partitions import COUNT, merge

MAX_INPUT_BYTES = 16 * 1024 * 1024


def stamp(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def read_part(path):
    path = Path(path).resolve()
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, 'O_CLOEXEC', 0))
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_INPUT_BYTES,
                'partition input must be a bounded regular file')
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, MAX_INPUT_BYTES + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            require(size <= MAX_INPUT_BYTES, 'partition input exceeded limit during read')
            chunks.append(chunk)
        require(stamp(before) == stamp(os.fstat(fd)) and size == before.st_size,
                'partition input changed during read')
    finally:
        os.close(fd)
    data = b''.join(chunks)
    return json.loads(data), {'path': str(path), 'bytes': size,
                              'sha256': hashlib.sha256(data).hexdigest()}


def merge_files(paths, output):
    require(len(paths) == COUNT, 'exactly six input files required')
    names = [Path(path).resolve() for path in paths]
    require(len(set(names)) == COUNT, 'duplicate input path')
    require(Path(output).resolve() not in names, 'output aliases an input path')
    parts, receipts = [], []
    for path in names:
        part, receipt = read_part(path)
        parts.append(part)
        receipts.append(receipt)
    result = merge(parts)
    result['partition_input_receipts'] = receipts
    # Serialize before exclusive creation; never overwrite an existing result.
    # An I/O failure can leave an incomplete diagnostic file, not a success
    # receipt. Use a new output after investigating such a failure.
    encoded = json.dumps(result, indent=2) + '\n'
    with Path(output).open('x', encoding='utf-8') as stream:
        stream.write(encoded)
    return result['partition_merge_proof']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--part', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    proof = merge_files(args.part, args.output)
    print(json.dumps({'output': str(args.output), 'row_accounting': proof,
                      'resource_release': False}))


if __name__ == '__main__':
    main()
