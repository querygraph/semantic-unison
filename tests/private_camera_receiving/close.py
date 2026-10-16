"""Close owned descriptors once; preserve nested uncertainty for the owner."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import (UnresolvedIOOwnership, descriptor_observation,
                            uncertainty_records)


def close_descriptors(fds):
    original = sys.exception()
    pending = list(fds)
    records = list(uncertainty_records(original, {}))
    retained = list(getattr(original, 'retained_fds', ()))
    # Never touch a number already marked uncertain by an inner scope.
    excluded = set(retained) | {item['fd'] for item in records}
    if excluded.intersection(pending):
        raise UnresolvedIOOwnership(
            'overlapping cleanup ownership; retain without retry',
            retained_fds=retained + [fd for fd in pending if fd not in excluded],
            uncertain_closes=records, original_failure=original) from original
    while pending:
        fd = pending.pop()
        observation = descriptor_observation(fd, 'camera_owned_descriptor')
        try:
            os.close(fd)
        except BaseException as error:
            records.append(observation)
            raise UnresolvedIOOwnership(
                'camera close outcome unknown; retain owner',
                retained_fds=retained + pending, uncertain_closes=records,
                original_failure=original, close_failure=error) from error
    # Successful outer cleanup must not replace the inner carrier.
    # Python resumes the active original exception when finally returns.
