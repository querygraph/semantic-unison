"""Source-bound large batch capture; same retained process lifecycle kernel.

No public SDK default is raised. The trusted batch factory is fixed here, not
selected by a remote plan or arbitrary callback. Maximum4MiB per stream, four
streams for simultaneous client/proxy; this is not a process RSS hard ceiling.
"""
from shared_child import _start
from batch_capture import BatchCapture


def start(command, environment, *, pass_fds=(), capture_limit=4*1048576):
    return _start(command, environment, pass_fds=pass_fds, capture_limit=capture_limit,
                  capture_type=BatchCapture, maximum_capture=4*1048576)


def audit_child(out, command):
    """Independent batch child metadata + bounded diagnostic contract."""
    if (type(out) is not dict or set(out) != {'command', 'returncode', 'timed_out',
            'capture_truncated', 'stdout', 'stderr', 'client_cleanup',
            'aggregate_or_parent_terminal_proved', 'io_cpu_release_authorized'}
            or out['command'] != command or type(out['returncode']) is not int or out['returncode'] != 0
            or out['timed_out'] is not False or out['capture_truncated'] is not False
            or out['aggregate_or_parent_terminal_proved'] is not False
            or out['io_cpu_release_authorized'] is not False):
        raise ValueError('exact qualified non-releasing batch child required')
    cleanup = out['client_cleanup']
    if (type(cleanup) is not dict or set(cleanup) != {'pid', 'returncode', 'reaped', 'hard_kill_required',
            'other_group_members_absent_before_reap', 'group_cleanup_before_leader_reap'}
            or type(cleanup['pid']) is not int or not 0 < cleanup['pid'] < 2**31
            or type(cleanup['returncode']) is not int or cleanup['returncode'] != 0
            or cleanup['reaped'] is not True or cleanup['hard_kill_required'] is not False
            or cleanup['other_group_members_absent_before_reap'] is not True
            or cleanup['group_cleanup_before_leader_reap'] is not True):
        raise ValueError('batch child/group proof incomplete')
    for stream in ('stdout', 'stderr'):
        # UTF8 replacement diagnostics can expand original invalid bytes3x.
        # Raw artifact publication separately enforces the exact4MiB byte limit.
        if type(out[stream]) is not str or len(out[stream].encode('utf8')) > 3*4*1048576:
            raise ValueError('bounded batch diagnostic required')
    return cleanup['pid']
