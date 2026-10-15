#!/usr/bin/env python3
"""Pure missing-capability refusals: no fork, process, fixture or SDK invocation."""
from unittest.mock import patch

import live_merge_aggregate as aggregate


def forbidden(*_args, **_kwargs):
    raise AssertionError('preflight attempted resource creation or dispatch')


def main():
    aggregate.require_worker_ownership_support()
    methods = ('fork', 'setsid', 'waitid', 'wait4', 'waitstatus_to_exitcode', 'killpg')
    constants = ('P_PID', 'WEXITED', 'WNOHANG', 'WNOWAIT')
    for name in methods + constants:
        # The whole aggregate must refuse before resolving a workspace,
        # writing a marker or opening readiness pipes, not merely before wait4.
        with patch.object(aggregate.os, name, None, create=True), \
                patch.object(aggregate, 'Path', side_effect=forbidden), \
                patch.object(aggregate, 'write', side_effect=forbidden), \
                patch.object(aggregate.os, 'pipe', side_effect=forbidden):
            try:
                aggregate.supervise(forbidden, 'NEVER-CREATED', seconds=12,
                                    expected_helper_calls=0)
            except RuntimeError as error:
                assert 'before worker dispatch' in str(error), str(error)
            else:
                raise AssertionError('missing capability accepted: ' + name)
    print('PASS current interpreter support and ten missing-capability refusals before resources/worker dispatch')


if __name__ == '__main__':
    main()
