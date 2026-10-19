"""Pure current live-merge command/accounting contract; no execution grant."""
from pathlib import PurePosixPath
import re

BUILD = 'unison-sdk171-2724-v1-single'
CODECS = ('uncompressed', 'jpeg', 'jxl')
STAGES = ('seed', 'update', 'noop')
MIB = 1048576
LIMITS = dict(cpu_credits=8, endpoint_workers=2, owner_credits=2,
              cli_calls=9, sdk_calls=6, codecs=3, states=12,
              observation_seconds=600, worker_seconds=570,
              per_cli_seconds=120, per_sdk_seconds=90,
              declared_logical_io_bytes=32*1024**3,
              physical_io_budget_enforced=False, retry_allowed=False)


def require(value, message):
    if not value:
        raise ValueError(message)


def path(value):
    require(type(value) is str and 0 < len(value) <= 4096 and '\0' not in value
            and value.startswith('/') and not value.startswith('//')
            and '..' not in PurePosixPath(value).parts
            and str(PurePosixPath(value)) == value, 'canonical absolute path required')
    return value


def digest(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None,
            'exact SHA256 required')
    return value


def binary(value, label):
    require(type(value) is dict and set(value) == {'label', 'path', 'sha256'}
            and value['label'] == label, 'exact client/server compiler identity required')
    path(value['path']); digest(value['sha256'])


def schedule(binaries, tool, workspace):
    """Three serial codecs, stock client/Ox server, exactly seed/merge/noop.

    The executable/source hashes here are declarations. The future owner must
    authenticate builds and hash artifacts after acquiring IO then CPU, preserve
    every intent/outcome, and separately prove all helper/group/FD settlement.
    """
    require(type(binaries) is dict and set(binaries) == {'stock', 'ox'},
            'exact stock/Ox pair required')
    for label in ('stock', 'ox'):
        binary(binaries[label], label)
    require(binaries['stock']['path'] != binaries['ox']['path'],
            'distinct compiled peers required')
    require(type(tool) is dict and set(tool) == {'path', 'sha256', 'build_id', 'threads'}
            and tool['build_id'] == BUILD
            and type(tool['threads']) is int and tool['threads'] == 1,
            'qualified single-thread reference SDK required')
    path(tool['path']); digest(tool['sha256'])
    root = PurePosixPath(path(workspace))
    require(root.parent == PurePosixPath('/private/tmp')
            and re.fullmatch('u-smg-[0-9a-f]{16}', root.name) is not None,
            'short private merge namespace required')

    source = 8*16*MIB + 262144
    publication = max(MIB, source) + 2048*MIB
    required_payload = source + 2*publication
    require(required_payload <= 6144*MIB and 8+2*24 <= 64,
            'source/publication admission headroom is insufficient')
    common = ['-clone', 'auto', '-semanticworkers', '2', '-semanticcpubudget', '2',
              '-maxthreads', '2', '-semanticvolumejobs', '1',
              '-semanticmaxinflight', '4', '-semanticpayloadbudget', '6144',
              '-semanticdescriptorbudget', '64', '-validationtreememory', '0',
              '-semanticmergebasecache',
              '-merge', 'Name *.dng -> unison:dng-xmp-scalars/0',
              '-adobevalidator', tool['path'], '-adobevalidatorhash', tool['sha256'],
              '-adobevalidatorbuild', BUILD, '-adobevalidatorthreads', '1',
              '-adobevalidatorworkspace', '2048', '-adobevalidatetimeout', '90',
              '-adobevalidatescope', 'received', '-debug', 'semantic',
              '-debug', 'validation-process', '-debug', 'validation-group',
              '-debug', 'validation-live', '-debug', 'validation-input']
    rows = []
    for codec in CODECS:
        directory = root / codec
        for stage in STAGES:
            require(len(str(directory/(stage+'.sock')).encode()) < 100,
                    'local transport socket pathname exceeds its bound')
            flags = common + ['-adobevalidate', 'off' if stage == 'seed' else 'require']
            rows.append(dict(codec=codec, stage=stage, directory=str(directory),
                identity=dict(label='stock', mode='semantic', workers=2,
                              directory=str(directory), stage=stage),
                command=[binaries['stock']['path'], str(directory/'left'),
                         'ssh://localhost/'+str(directory/'right'),
                         '-sshcmd', str(directory/'launcher.py'),
                         '-servercmd', binaries['ox']['path'],
                         '-batch', '-auto', '-fastcheck', 'false', '-times', *flags],
                server_flags=flags,
                server_command=[binaries['ox']['path'],'-server','__new-rpc-mode',*flags],
                expected_sdk_helpers=2 if stage == 'update' else 0,
                requires_unchanged_noop=stage == 'noop'))
    return dict(schema='unison-current-sdk-merge-schedule/1', rows=rows,
                limits=dict(LIMITS), token_indexes=list(range(8)),
                declared_endpoint_plus_owner_credits=2+2+2,
                minimum_payload_credits=required_payload,
                payload_credits=6144*MIB, minimum_descriptor_credits=56,
                descriptor_credits=64, transaction_slots=4,
                runtime_admitted=False, sdk_invoked=False,
                hard_rss_cap=False, os_thread_cap=False)
