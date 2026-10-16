"""Prepared one-source diagnostic worker; only its shared IO owner may launch.

Never run this worker directly. It requires the exact Root admission and
one-use parent marker; no IO/CPU ownership is established by importing it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tests'))
from shared_io_pool import read_manifest
from shared_cpu_pool import require, unique_object

SOURCE = Path('/private/tmp/unison-dng-da-copy-57c830f336da4ef099150958b2f3d666/source-clone.DNG')
SOURCE_KEYS = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_nlink', 'st_uid')
PROGRAM_SOURCES = ('src/dngPrivateData.mli', 'src/dngPrivateData.ml',
                   'tools/private-dng-framing/inspect.ml', 'tools/private-dng-framing/controls.py')
LIMIT = 331558


def identity(value):
    return {key: getattr(value, key) for key in SOURCE_KEYS}


def check_input(fd, path, expected):
    require(identity(os.fstat(fd)) == expected == identity(os.lstat(path)),
            'exact held/visible source native epoch differs')
    require(stat.S_ISREG(expected['st_mode']) and stat.S_IMODE(expected['st_mode']) == 0o400
            and expected['st_nlink'] == 1 and expected['st_uid'] == os.getuid(),
            'owned mode0400 single-link source required')


def checked_plan(value):
    require(value['schema'] == 'unison-private-framing-input/1' and
            value['source']['path'] == str(SOURCE) and type(value['max_reads_each']) is int and
            value['max_reads_each'] == LIMIT and type(value['diagnostic_seconds_each']) is int and
            value['diagnostic_seconds_each'] == 10,
            'exact one-source bounded diagnostic scope required')
    expected = value['source']['identity']
    require(set(expected) == set(SOURCE_KEYS) and
            all(type(v) is int and v >= 0 for v in expected.values()), 'typed source identity required')
    require([p['label'] for p in value['programs']] == ['stock', 'ox'], 'two serial pinned programs required')
    return expected


def checked_program(item):
    report = read_manifest(item['build_report']['path'], item['build_report']['sha256'])
    require(report['schema'] == 'unison-private-framing-cli-controls/1' and report['complete'] is True,
            'qualified fixed-controls build report required')
    expected = {str(ROOT/p): hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PROGRAM_SOURCES}
    require(report['source_sha256'] == expected, 'compiled diagnostic source set differs')
    rows = [b for b in report['builds'] if b['compiler_label'] == item['label']]
    require(len(rows) == 1 and rows[0]['returncode'] == 0 and rows[0]['binary'] == item['path'] and
            rows[0]['binary_sha256'] == item['sha256'], 'program/build receipt binding differs')
    binary = Path(item['path']); work = Path(report['workspace'])/item['label']
    require(binary.is_absolute() and binary == work/'private-framing-diagnostic', 'private binary path differs')
    directory = os.lstat(work)
    require(stat.S_ISDIR(directory.st_mode) and directory.st_uid == os.getuid()
            and stat.S_IMODE(directory.st_mode) == 0o700, 'private owned binary directory required')
    fd = os.open(binary, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = identity(os.fstat(fd))
        require(stat.S_ISREG(before['st_mode']) and before['st_nlink'] == 1 and
                before['st_uid'] == os.getuid() and 0 < before['st_size'] <= 32*1048576,
                'bounded private compiled binary required')
        digest = hashlib.sha256(); total = 0
        while total <= 32*1048576:
            chunk = os.read(fd, min(1048576, 32*1048576+1-total))
            if not chunk: break
            digest.update(chunk); total += len(chunk)
        require(total == before['st_size'] and digest.hexdigest() == item['sha256'] and
                before == identity(os.fstat(fd)) == identity(os.lstat(binary)), 'compiled binary changed')
    finally:
        os.close(fd)
    return binary


def validate_diagnostic(value, size):
    require(value['schema'] == 'unison-private-framing-diagnostic/1' and
            value['diagnostic_only'] is True and value['semantic_eligibility'] is False and
            value['full_file_sha256_computed'] is False and value['sdk_validation'] is False and
            value['native_nanosecond_epoch_fence_performed_by_child'] is False,
            'diagnostic claims differ')
    require(type(value['logical_read_bytes']) is int and type(value['requested_read_bytes']) is int and
            0 <= value['logical_read_bytes'] == value['requested_read_bytes'] <= LIMIT and
            value['read_limit_bytes'] == LIMIT and type(value['read_requests']) is int and
            0 <= value['read_requests'] == len(value['read_ranges']) <= 773, 'diagnostic byte/count budget differs')
    for row in value['read_ranges']:
        require(set(row) == {'offset', 'length'} and type(row['offset']) is int and type(row['length']) is int and
                0 <= row['offset'] <= size and 0 <= row['length'] <= size-row['offset'],
                'diagnostic read outside admitted file')
    require(sum(row['length'] for row in value['read_ranges']) == value['requested_read_bytes'],
            'diagnostic ranges/byte count differ')
    require(type(value['locator_completed']) is bool and type(value['framing_recognized']) is bool,
            'typed diagnostic outcome required')
    return value


def parent_gate():
    admission = read_manifest(os.environ['SHARED_IO_ADMISSION'], os.environ['SHARED_IO_ADMISSION_SHA256'])
    command = [sys.executable, str(Path(__file__)), *sys.argv[1:]]
    require(admission['state'] == 'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB' and
            admission['target'] == 'private-dng-framing-input' and admission['command'] == command,
            'this exact worker requires its fresh shared IO admission')
    workspace = Path(admission['workspace'])
    marker = workspace/'SHARED-IO-ATTEMPT.json'
    # This trusted parent marker is cooperative ownership, not a same-UID
    # sandbox or independent proof of locks. Parent performs their acquisition.
    fd = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = identity(os.fstat(fd))
        require(stat.S_ISREG(before['st_mode']) and before['st_uid'] == os.getuid() and
                before['st_nlink'] == 1 and 0 < before['st_size'] <= 65536, 'bounded owned parent marker required')
        data = bytearray()
        while len(data) <= 65536:
            block = os.read(fd, min(8192, 65537-len(data)))
            if not block: break
            data.extend(block)
        require(len(data) == before['st_size'] and before == identity(os.fstat(fd)) == identity(os.lstat(marker)),
                'shared parent marker changed')
        intent = json.loads(data, object_pairs_hook=unique_object)
    finally:
        os.close(fd)
    require(intent['owner_pid'] == os.getppid() and intent['target'] == admission['target'] and
            intent['command'] == command and intent['admission'] ==
            {'path': os.environ['SHARED_IO_ADMISSION'], 'sha256': os.environ['SHARED_IO_ADMISSION_SHA256']},
            'qualified shared owner parent differs')
    fd = os.open(workspace/'DIAGNOSTIC-WORKER-START.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump({'pid': os.getpid(), 'parent': os.getppid(), 'command': command}, stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    parent_gate()
    plan = read_manifest(args.plan, args.plan_sha256); expected = checked_plan(plan)
    # Parent has already acquired IO then CPU. Hash executables here, never
    # the camera-derived input, and never compile/rebuild in this worker.
    programs = [checked_program(p) for p in plan['programs']]
    fd = os.open(SOURCE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    result = {'schema': 'unison-private-framing-input-result/1', 'complete': False, 'calls': [],
              'source_sha256_computed': False, 'semantic_eligibility': False, 'sdk_validation': False}
    environment = dict(os.environ)
    for key in ('OCAMLRUNPARAM', 'CAML_LD_LIBRARY_PATH', 'OCAMLPATH', 'OCAMLLIB'):
        environment.pop(key, None)
    try:
        check_input(fd, SOURCE, expected)
        for item, binary in zip(plan['programs'], programs):
            check_input(fd, SOURCE, expected)
            call = subprocess.run([str(binary)], stdin=fd, capture_output=True, timeout=10, env=environment)
            result['calls'].append({'compiler_label': item['label'], 'actual_wait_exit': call.returncode,
                'stdout': call.stdout.decode(), 'stderr': call.stderr.decode()})
            check_input(fd, SOURCE, expected)
            require(call.returncode == 0 and not call.stderr and len(call.stdout) <= 262144,
                    'bounded diagnostic child failed')
            validate_diagnostic(json.loads(call.stdout), expected['st_size'])
        require(result['calls'][0]['stdout'] == result['calls'][1]['stdout'], 'compiler observations differ')
        result.update(complete=True, source_native_epoch_before_after=expected, source_native_epoch_verified=True,
            total_logical_read_bytes=sum(json.loads(c['stdout'])['logical_read_bytes'] for c in result['calls']))
    except BaseException as error:
        result['failure'] = repr(error)
        print(json.dumps(result), flush=True)
        raise
    finally:
        os.close(fd)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
