"""Retained batch peer composition and independently pinned server audit.

Uses the existing retained proxy wire schema. Owning caller supplies exact pinned
commands/environments and proxy record reader. No admission/resource acquisition
or release is provided; source-bound external-child policy remains mandatory.
"""
import json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.transport import wait_socket
from sdk_merge_receiving.evidence import unique
from batch_transport import launch, restore
from batch_artifacts import publish, read


def audit(store, evidence, *, client_command, proxy_command, server_command):
    if type(evidence) is not dict or set(evidence) != {'client', 'proxy', 'server_frame'}:
        raise ValueError('exact pinned peer evidence required')
    client = restore(store, evidence['client'], client_command)
    proxy = restore(store, evidence['proxy'], proxy_command)
    raw = read(store, evidence['server_frame'])
    if len(raw) > 65536: raise ValueError('bounded proxy record required')
    frame = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite proxy frame')))
    fields = {'schema', 'server_command', 'server_pid', 'server_returncode', 'server_reaped',
              'server_group', 'input_eof_forwarded', 'output_eof_forwarded',
              'forwarded_protocol_bytes', 'parent_group_audit_required',
              'sdk_helper_audit_required', 'resource_release_authorized'}
    if type(frame) is not dict or set(frame) != fields:
        raise ValueError('exact native proxy record required')
    cp = client['client_cleanup']['pid']; pp = proxy['client_cleanup']['pid']
    if (frame['schema'] != 'unison-retained-merge-proxy/1'
            or frame['server_command'] != server_command
            or type(frame['server_pid']) is not int or frame['server_pid'] <= 0
            or len({cp, pp, frame['server_pid']}) != 3
            or type(frame['server_returncode']) is not int or frame['server_returncode'] != 0
            or frame['server_reaped'] is not True
            or type(frame['server_group']) is not int or frame['server_group'] != pp
            or frame['input_eof_forwarded'] is not True or frame['output_eof_forwarded'] is not True
            or frame['parent_group_audit_required'] is not True
            or frame['sdk_helper_audit_required'] is not True
            or frame['resource_release_authorized'] is not False):
        raise ValueError('native command/peer/group/EOF binding differs')
    counts = frame['forwarded_protocol_bytes']
    if (type(counts) is not dict or set(counts) != {'client_to_server_bytes', 'server_to_client_bytes'}
            or any(type(n) is not int or not 0 < n < 2**63 for n in counts.values())):
        raise ValueError('exact positive protocol counts required')
    return dict(client_pid=cp, proxy_pid=pp, server_pid=frame['server_pid'],
                external_children_source_audit_required=True, resource_release_authorized=False)


def invoke(client_command, client_environment, *, proxy_command, proxy_environment,
           server_command, socket_path, deadline, pass_fds, store, name, read_proxy_bytes):
    import os, re, time
    if (type(name) is not str or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,23}', name) is None
            or type(deadline) not in (int, float) or not time.monotonic() < deadline < float('inf')
            or type(server_command) is not list or not server_command
            or any(type(x) is not str for x in server_command)):
        raise ValueError('bounded one-use pair and fresh observation required')
    if os.path.lexists(socket_path): raise ValueError('one-use socket already exists')
    started_ns=time.monotonic_ns()
    proxy = client = None
    evidence = {}
    try:
        proxy = launch(proxy_command, proxy_environment, pass_fds=pass_fds,
                       store=store, name=name+'-proxy')
        wait_socket(socket_path, proxy.pending, deadline)
        client = launch(client_command, client_environment, pass_fds=pass_fds,
                        store=store, name=name+'-client')
        evidence['client'] = client.finish(deadline)
        evidence['proxy'] = proxy.finish(deadline)
        raw = read_proxy_bytes()
        if type(raw) is not bytes or not 0 < len(raw) <= 65536:
            raise ValueError('complete bounded proxy raw record required')
        evidence['server_frame'] = publish(store, name+'-server-frame', raw)
        joined = audit(store, evidence, client_command=client_command,
                       proxy_command=proxy_command, server_command=server_command)
        evidence_ns=time.monotonic_ns()
        measurements=store.write(name+'-TIMING.json',dict(schema='unison-batch-pair-observation/1',
            started_ns=started_ns,evidence_ready_ns=evidence_ns,elapsed_ns=evidence_ns-started_ns,
            client=client.observation,proxy=proxy.observation,
            scope='pair orchestration through captured evidence persistence; not bare native runtime',
            resource_release_authorized=False))
        pin = store.write(name+'-pair.json', dict(schema='unison-batch-pair/2',
                          evidence=evidence, audit=joined,measurements=measurements))
        return pin
    except BaseException as error:
        retained = error if isinstance(error, UnresolvedOwnership) else UnresolvedOwnership(
            'batch pair unresolved; retain actual handles, evidence and resource owner')
        if retained is not error: retained.original_failure = error
        retained.batch_pair_handles = [h for h in (proxy, client) if h is not None]
        retained.batch_pair_evidence = evidence
        if retained is error: raise
        raise retained from error
