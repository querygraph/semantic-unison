"""Bounded metadata boundary for a future one-use all-scanned SDK executor.

No executable invocation, token acquisition, source payload read or admission
grant. All descriptor uncertainty propagates the original qualified carrier.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from shared_cpu_pool import unique_object
from private_camera_receiving.close import close_descriptors
from sdk_multifile.clone import FIELDS, stamp
from all_scanned_sdk_plan import plan as command_plan, BUILD

PYTHON = '/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PYTHON_SHA = '56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'
PARAMETERS = dict(cpu_credits=8, compiler_cases=2, cli_calls=4, sdk_calls=4,
    endpoint_workers=3, observation_seconds=600, worker_seconds=570,
    per_cli_seconds=240, per_sdk_seconds=90, declared_logical_io_bytes=16 * 1073741824,
    io_budget_enforced=False, native_clone_only=True)


def require(value, message):
    if not value: raise ValueError(message)


def typed_equal(a, b):
    if type(a) is not type(b): return False
    if type(b) is dict:
        return a.keys() == b.keys() and all(typed_equal(a[k], v) for k, v in b.items())
    if type(b) is list:
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def read_document(path, digest, *, limit=65536):
    require(Path(path).is_absolute() and '..' not in Path(path).parts,
            'explicit absolute metadata path required')
    require(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest) is not None,
            'exact metadata document SHA required')
    require(type(limit) is int and 0 < limit <= 1048576, 'bounded metadata ceiling required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and before.st_uid == os.getuid() and before.st_mode & 0o022 == 0
                and 0 < before.st_size <= limit,
                'owned bounded regular document required')
        raw = bytearray()
        while len(raw) < before.st_size:
            block = os.read(fd, min(8192, before.st_size - len(raw)))
            require(bool(block), 'short metadata read'); raw.extend(block)
        require(not os.read(fd, 1) and stamp(before) == stamp(os.fstat(fd)) == stamp(os.lstat(path)),
                'metadata document changed')
        require(hashlib.sha256(raw).hexdigest() == digest, 'metadata document SHA differs')
        return json.loads(raw, object_pairs_hook=unique_object)
    finally:
        close_descriptors([fd])


def validate_packet(value, *, execution_pins, observed_source, tool_manifest, build_receipts):
    """Pure exact contract join; caller supplies freshly authenticated metadata."""
    require(type(value) is dict and set(value) == {
        'schema', 'workspace', 'parameters', 'execution_source_sha256', 'binaries',
        'builds', 'tool', 'source', 'transport_source_sha256', 'interpreter'},
        'exact all-scanned packet fields required')
    require(value['schema'] == 'unison-all-scanned-sdk-plan/1'
            and typed_equal(value['parameters'], PARAMETERS), 'fixed finite scope required')
    require(value['execution_source_sha256'] == execution_pins and bool(execution_pins),
            'execution closure differs')
    require(type(execution_pins) is dict and all(type(path) is str and Path(path).is_absolute()
            and type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest) is not None
            for path, digest in execution_pins.items()), 'typed exact execution pins required')
    require(value['interpreter'] == dict(path=PYTHON, sha256=PYTHON_SHA), 'qualified interpreter required')
    workspace = Path(value['workspace'])
    require(workspace.parent == Path('/private/tmp') and workspace.name.startswith('u-asv-')
            and 8 < len(workspace.name) <= 32, 'fresh short private namespace required')
    require(set(value['binaries']) == set(value['builds']) == set(build_receipts) == {'stock', 'ox'},
            'exact compiler pair required')
    for label in ('stock', 'ox'):
        binary, build = value['binaries'][label], build_receipts[label]
        require(type(binary) is dict and set(binary) == {'label', 'path', 'sha256'}
                and binary['label'] == label, 'exact compiler binary required')
        switch = 'default' if label == 'stock' else '5.2.0+ox'
        require(build['complete'] is True and type(build['build_exit']) is int and build['build_exit'] == 0
                and build['compiler'] == '/Users/alexy/.opam/' + switch + '/bin/ocamlopt'
                and build['binary'] == binary['path'] and build['binary_sha256'] == binary['sha256'],
                'successful source-pinned build binding differs')
        require(set(value['builds'][label]) == {'path', 'sha256'}, 'exact build receipt pin required')
    source = value['source']
    require(type(source) is dict and set(source) == {'path', 'identity', 'sha256', 'bytes'}
            and type(source['identity']) is dict and set(source['identity']) == set(FIELDS)
            and all(type(v) is int for v in source['identity'].values()), 'exact borrowed source identity required')
    require(typed_equal(source['identity'], observed_source) and type(source['bytes']) is int
            and source['bytes'] == observed_source['st_size'] and 0 < source['bytes'] <= 256 * 1048576
            and stat.S_ISREG(observed_source['st_mode']) and stat.S_IMODE(observed_source['st_mode']) == 0o400
            and observed_source['st_nlink'] == 1 and observed_source['st_uid'] == os.getuid(),
            'readonly private source epoch/type/mode differs')
    require(Path(source['path']).is_absolute() and Path(source['path']).is_relative_to('/private/tmp')
            and '..' not in Path(source['path']).parts, 'explicit retained Unison private source required')
    tool = value['tool']
    require(type(tool) is dict and set(tool) == {'path', 'sha256', 'build_id', 'threads', 'manifest', 'manifest_sha256'}
            and tool['build_id'] == BUILD and type(tool['threads']) is int and tool['threads'] == 1,
            'qualified single-thread SDK contract required')
    require(tool_manifest['executable'] == tool['path'] and tool_manifest['executable_sha256'] == tool['sha256']
            and tool_manifest['build_id'] == BUILD, 'SDK manifest binding differs')
    for item in [*value['binaries'].values(), *value['builds'].values(), tool,
                 dict(path=tool['manifest'], sha256=tool['manifest_sha256']), source]:
        require(type(item['path']) is str and Path(item['path']).is_absolute()
                and '..' not in Path(item['path']).parts and type(item['sha256']) is str
                and re.fullmatch('[0-9a-f]{64}', item['sha256']) is not None,
                'exact absolute artifact/document/source path and SHA required')
    transport = value['transport_source_sha256']
    require(type(transport) is dict and set(transport) == {'proxy.py', 'measure.py', 'launcher.py', 'ownership.py'},
            'all copied transport pins required')
    require(all(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest) is not None
                for digest in transport.values()), 'exact transport hashes required')
    root = Path(__file__).resolve().parents[1]
    require(transport == {name: execution_pins.get(str(root / 'bench/sync' / name)) for name in transport},
            'transport source pins differ from closure')
    for label in ('stock', 'ox'): command_plan(value['binaries'][label], tool, workspace / label)
    return value


def current_sources():
    """Read the declared harness/driver source closure, never executables/media."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'tests/camera_sdk_concurrency'))
    from camera_sdk_concurrency.invocation import artifact_sha
    paths = set((root / 'tests').glob('all_scanned_sdk*.py'))
    paths.update((root / 'bench/sync').glob('*.py'))
    for package in ('sdk_host_matrix', 'camera_sdk_concurrency', 'camera_sdk_receiving',
                    'private_camera_receiving', 'sdk_multifile', 'validation_process'):
        paths.update((root / 'tests' / package).glob('*.py'))
    paths.update(root / 'tests' / name for name in ('shared_cpu_pool.py', 'shared_io_pool.py',
        'shared_process_owner.py', 'shared_dispatch.py', 'manual.py', 'build_snapshot.py'))
    paths.update((root / 'tools/adobe-validator').glob('*.h'))
    paths.add(root / 'tools/adobe-validator/driver.cpp')
    return {str(path): artifact_sha(path) for path in sorted(paths)}


def checked_plan(path, digest):
    """Metadata/source preflight only. Artifact executable hashes wait for IO."""
    require(sys.executable == PYTHON, 'qualified interpreter invocation required')
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'canonical plan pathname required')
    value = read_document(path, digest)
    pins = current_sources()
    tool = value['tool']
    manifest = read_document(tool['manifest'], tool['manifest_sha256'])
    builds = {label: read_document(item['path'], item['sha256'], limit=1048576)
              for label, item in value['builds'].items()}
    root = Path(__file__).resolve().parents[1]
    for build in builds.values():
        require(build['runner_sha256'] == pins[str(root / 'tests/build_snapshot.py')],
                'build inventory producer changed')
        source_pins = build['source_sha256']
        require(all(name in source_pins for name in (
            'src/candidateValidation.ml', 'src/validationScanWork.ml', 'src/update.ml',
            'src/dngCandidateValidation.ml', 'src/dngValidation.ml', 'src/semanticWorkers.ml')),
            'compiled validation/scan inventory missing')
        from camera_sdk_concurrency.invocation import artifact_sha
        for name, expected in source_pins.items():
            if name.startswith('src/'):
                require('..' not in Path(name).parts and artifact_sha(root / name) == expected,
                        'production build source changed: ' + name)
    source = value['source']; source_path = Path(source['path'])
    require(source_path.is_relative_to('/private/tmp') and '..' not in source_path.parts
            and source_path.resolve() == source_path, 'canonical retained private source path required')
    return validate_packet(value, execution_pins=pins, observed_source=stamp(os.lstat(source_path)),
                           tool_manifest=manifest, build_receipts=builds)
