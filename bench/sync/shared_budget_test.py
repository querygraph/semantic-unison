#!/usr/bin/env python3
"""Pure pre-dispatch budget controls; run after the current quiet allocation."""
import io
import sys
from unittest.mock import patch
import run as sync


class MetadataReached(Exception):
    pass


cases = (
    (['--workers', '4', '--loopback-cpu-credits', '10', '--orchestration-cpu-credits', '2'], True),
    (['--workers', '2', '--loopback-cpu-credits', '6', '--orchestration-cpu-credits', '2'], True),
    (['--workers', '4', '--modes', 'source-clone', '--loopback-cpu-credits', '6', '--orchestration-cpu-credits', '2'], True),
    (['--workers', '4', '--loopback-cpu-credits', '8'], True),
    (['--workers', '4', '--loopback-cpu-credits', '9', '--orchestration-cpu-credits', '2'], False),
    (['--workers', '6', '--loopback-cpu-credits', '10', '--orchestration-cpu-credits', '2'], False),
    (['--orchestration-cpu-credits', '-1'], False),
    (['--orchestration-cpu-credits', '19'], False),
    (['--orchestration-cpu-credits', '2'], False),
    (['--workers', '4', '--modes', 'source-clone', '--loopback-cpu-credits', '5', '--orchestration-cpu-credits', '2'], False),
    (['--shared-qualification', '--loopback-cpu-credits', '8', '--orchestration-cpu-credits', '2'], True),
    (['--shared-qualification', '--loopback-cpu-credits', '8'], False),
    (['--shared-qualification', '--loopback-cpu-credits', '5', '--orchestration-cpu-credits', '2'], False),
    (['--shared-qualification', '--qualification', '--loopback-cpu-credits', '8', '--orchestration-cpu-credits', '2'], False),
    (['--shared-qualification', '--partition', '0', '--loopback-cpu-credits', '8', '--orchestration-cpu-credits', '2'], False),
)

for options, admitted in cases:
    argv = [str(sync.__file__), '--binary', 'stock=' + sys.executable,
            '--output', 'NEVER-CREATED-SHARED-RESULT.json'] + options
    with patch.object(sys, 'argv', argv), patch.object(sys, 'stderr', io.StringIO()), \
            patch.object(sync, 'binary_info', side_effect=MetadataReached) as metadata, \
            patch.object(sync.subprocess, 'run', side_effect=AssertionError('tool dispatch')):
        try:
            sync.main()
        except MetadataReached:
            assert admitted and metadata.call_count == 1
        except SystemExit as error:
            assert not admitted and error.code == 2 and metadata.call_count == 0
        else:
            raise AssertionError('escaped pre-dispatch boundary')
print('PASS five budget admissions/ten refusals before tool metadata; no child/output')
