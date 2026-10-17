"""Metadata-only admission binding for an existing inspector and one input.

No input payload is opened here. The retained inspector runner verifies its
binary and compiled sources again after the dispatcher acquires IO then CPU.
"""
from pathlib import Path
import stat

FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_size',
          'st_mtime_ns', 'st_ctime_ns')


def identity(path):
    info = Path(path).lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError('single regular inspector input required')
    return {name: getattr(info, name) for name in FIELDS}


def check(value, argv, root):
    from shared_io_pool import read_manifest
    contract = value.get('inspector_contract')
    if not isinstance(contract, dict) or set(contract) != {
            'build_receipt', 'build_receipt_sha256', 'binary_sha256',
            'input', 'input_identity', 'mode'}:
        raise ValueError('exact inspector contract required')
    if contract['mode'] != 'components' or not Path(contract['input']).is_absolute():
        raise ValueError('one absolute advisory component input required')
    expected = [__import__('sys').executable, str(root / 'tools/semantic-inspect/run.py'),
                '--use-build', contract['build_receipt'], '--', '--components', contract['input']]
    if argv != expected:
        raise ValueError('inspector command differs from contract')
    receipt = read_manifest(contract['build_receipt'], contract['build_receipt_sha256'])
    if (receipt.get('schema') != 'unison-semantic-inspector-build/1'
            or receipt.get('complete') is not True or receipt.get('build_only') is not True
            or receipt.get('build_exit') != 0
            or receipt.get('binary_sha256') != contract['binary_sha256']):
        raise ValueError('successful pinned inspector build required')
    # No binary payload read before IO admission: run.py checks its digest after
    # acquisition. Exact kernel sources are admission pins, checked by dispatcher.
    if identity(contract['input']) != contract['input_identity']:
        raise ValueError('inspector input identity changed')
    import importlib.util
    runner = root / 'tools/semantic-inspect/run.py'
    spec = importlib.util.spec_from_file_location('inspector_contract_runner', runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if set(receipt['source_sha256']) != {str(name) for name in module.SOURCES}:
        raise ValueError('exact inspector kernel source set required')
    return {root / name for name in module.SOURCES}


def postcheck(binding):
    """No opened FD: metadata refusal is functional failure, not FD uncertainty."""
    try:
        observed = identity(binding['input'])
    except (OSError, ValueError) as error:
        return {'unchanged': False, 'observed': None, 'error': repr(error)}
    return {'unchanged': observed == binding['input_identity'],
            'observed': observed, 'error': None}
