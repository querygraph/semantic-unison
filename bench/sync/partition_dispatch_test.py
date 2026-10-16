#!/usr/bin/env python3
"""Pure admission/selection checks. Never invokes a compiler, binary or worker."""
import copy
import json
from pathlib import Path
import tempfile
import time
import io
import sys
from unittest.mock import patch

from fixtures import validate_dimensions
import partitions
import run_bounded as bounded
import run as sync


class MetadataReached(Exception):
    pass


def parser_controls():
    argv = [str(sync.__file__), '--binary', 'stock=' + sys.executable,
            '--binary', 'ox=' + sys.executable, '--workers', '1,6,8',
            '--file-mib', '2048', '--files', '2', '--partition', '0',
            '--output', 'NEVER-CREATED-OUTPUT.json']
    negatives = (['--partition', '6'], ['--partition', '-1'], ['--files', '5'],
                 ['--qualification'], ['--workers', '8,6,1'], ['--modes', 'semantic'])
    for extra in ([], *negatives):
        with patch.object(sys, 'argv', argv + extra), \
                patch.object(sys, 'stderr', io.StringIO()), \
                patch.object(sync, 'binary_info', side_effect=MetadataReached) as metadata, \
                patch.object(sync.subprocess, 'run', side_effect=AssertionError('process dispatch')):
            try:
                sync.main()
            except MetadataReached:
                assert not extra, 'invalid arguments reached binary metadata'
                assert metadata.call_count == 1
            except SystemExit as error:
                assert extra and error.code == 2
                assert metadata.call_count == 0
            else:
                raise AssertionError('parser escaped its pre-dispatch test seam')


def refuse(function):
    try:
        function()
    except (ValueError, KeyError):
        return
    raise AssertionError('invalid partition/dimension accepted')


def main():
    parser_controls()
    universe = [(label, mode, worker) for label in partitions.LABELS
                for mode in partitions.MODES for worker in partitions.WORKERS]
    selections = [partitions.select(universe, index) for index in range(6)]
    assert len({value for part in selections for value in part}) == 18
    assert sum(map(len, selections)) == 18
    for changed in (universe[:-1], universe + [universe[0]], universe[:-1] + [('other', 'semantic', 8)]):
        refuse(lambda: partitions.select(changed, 0))
    assert validate_dimensions(2048, 2, 8192) == 2 * 1024 ** 3
    assert validate_dimensions(2048, 4, 8192) * 4 == 8 * 1024 ** 3
    for values in ((2049, 1, 8192), (2048, 5, 8192), (0, 1, 8192),
                   (128, 0, 8192), (128, 1, 0), (True, 1, 8192),
                   (1, 1, 1048576)):
        refuse(lambda: validate_dimensions(*values))
    with tempfile.TemporaryDirectory(prefix='unison-partition-source-') as temporary:
        work = Path(temporary)
        plan = work / 'plan.json'
        plan.write_text(json.dumps({'pure_fixture': True}))
        workspace = work / 'NEVER-CREATED'
        command = ['not-an-executable']
        allocation = {'state': 'ROOT_ALLOCATED_FINITE_SYNC_PARTITION_V1',
            'plan': bounded.pin(plan), 'batch_index': 1, 'partition_index': 0,
            'workspace': str(workspace), 'command': command, 'source_pins': bounded.sources(),
            'limits': {'cpu_credits': 18, 'aggregate_seconds': 7200, 'cli_invocations': 54},
            'startDeadlineUnix': time.time() + 60}
        bounded.check_allocation(allocation, plan, 1, workspace, command, partition=0)
        for name, value in (('state', 'ROOT_ALLOCATED_FINITE_SYNC_BATCH_V1'),
                            ('partition_index', 1), ('partition_index', False),
                            ('limits', dict(allocation['limits'], cli_invocations=324)),
                            ('command', ['other']), ('startDeadlineUnix', 0)):
            changed = copy.deepcopy(allocation)
            changed[name] = value
            refuse(lambda: bounded.check_allocation(changed, plan, 1, workspace, command, partition=0))
        refuse(lambda: bounded.check_allocation(allocation, plan, 1, workspace, command))
        assert not workspace.exists()
    print('PASS actual2GiB/partition parser admission,6 parser refusals,6 selections and17 selection/dimension/allocation refusals; no dispatch')


if __name__ == '__main__':
    main()
