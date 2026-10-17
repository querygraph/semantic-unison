"""Bind a native server to its actual retained proxy group leader.

The native server is NOT the group leader. Its own wait4 is separate from the
supervisor's later group census before supervisor leader reap. No PID polling.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bench/sync'))
from invocation_journal import audit_no_server_creation


def audit(outcome):
    proxy = outcome['proxy']; server = proxy['server_cleanup']
    if server is None:
        audit_no_server_creation(outcome)
        if proxy.get('server_group_binding', 'MISSING') is not None:
            raise ValueError('no-server proof contradicts group observation')
        return dict(server_created=False, group_cleanup_authority=False)
    supervisor = outcome['supervisor_cleanup']; binding = proxy.get('server_group_binding')
    if (type(binding) is not dict or set(binding) != {'native_pid', 'native_process_group',
            'supervisor_pid', 'supervisor_process_group', 'observed_before_native_reap'}
            or any(type(binding[k]) is not int or not 0 < binding[k] < 2**31 for k in (
                'native_pid', 'native_process_group', 'supervisor_pid', 'supervisor_process_group'))
            or binding['observed_before_native_reap'] is not True):
        raise ValueError('actual pre-reap native/supervisor group observation required')
    if (type(server.get('pid')) is not int or type(supervisor.get('pid')) is not int
            or binding['native_pid'] != server['pid'] or server['pid'] != proxy['server_pid']
            or binding['native_pid'] == binding['supervisor_pid']
            or binding['supervisor_pid'] != supervisor['pid']
            or binding['native_process_group'] != binding['supervisor_process_group']
            or binding['supervisor_process_group'] != supervisor['pid']
            or server.get('reaped') is not True or supervisor.get('reaped') is not True
            or supervisor.get('group_cleanup_before_leader_reap') is not True
            or supervisor.get('other_group_members_absent_before_reap') is not True):
        raise ValueError('native server group not fenced by actual retained supervisor leader')
    return dict(server_created=True, native_pid=server['pid'], group_leader_pid=supervisor['pid'],
                native_was_group_leader=False, observed_group_empty_before_group_leader_reap=True,
                resource_release_authorized=False)
