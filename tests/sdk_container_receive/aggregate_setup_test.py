#!/usr/bin/env python3
"""Finite mock acquisition faults; no real descriptor, fork or SDK operation."""
from types import SimpleNamespace
from unittest.mock import patch

import live_merge_aggregate as aggregate


class SetupFailure(Exception):
    pass


def main():
    cases = ('first-pipe', 'second-pipe', 'stdout-flush', 'stderr-flush',
             'fork', 'fork-close-failure')
    for case in cases:
        failure = SetupFailure(case)
        acquired, closed, calls = [], [], []

        def pipe():
            index = len(calls)
            calls.append('pipe')
            if case == ('first-pipe' if index == 0 else 'second-pipe'):
                raise failure
            pair = (100 + 2 * index, 101 + 2 * index)
            acquired.extend(pair)
            return pair

        def flush(stream):
            if case == stream + '-flush':
                raise failure

        def fork():
            raise failure

        def close(fd):
            closed.append(fd)
            if case == 'fork-close-failure' and len(closed) == 1:
                raise OSError('original mock close failure')

        # All OS resource methods are substituted. Writing a marker is also
        # mocked; failures must retain marker ownership, never publish CLOSED.
        with patch.object(aggregate.os, 'pipe', side_effect=pipe), \
                patch.object(aggregate.os, 'fork', side_effect=fork), \
                patch.object(aggregate.os, 'close', side_effect=close), \
                patch.object(aggregate, 'write') as writes, \
                patch.object(aggregate.sys, 'stdout', SimpleNamespace(flush=lambda: flush('stdout'))), \
                patch.object(aggregate.sys, 'stderr', SimpleNamespace(flush=lambda: flush('stderr'))):
            try:
                aggregate.supervise(lambda _deadline: None, 'NEVER-CREATED',
                                    seconds=12, expected_helper_calls=0)
            except SetupFailure as error:
                assert error is failure, 'original exception identity changed'
            else:
                raise AssertionError('setup fault accepted: ' + case)
        assert writes.call_count == 2, 'setup failure published a closure receipt'
        assert closed == acquired, (case, acquired, closed)
    print('PASS six mocked setup failures; all acquired descriptors attempted, first exception retained')


if __name__ == '__main__':
    main()
