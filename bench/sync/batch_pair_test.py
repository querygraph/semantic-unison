"""Original pinned fake peer evidence; no process/socket or native invocation."""
import json
import unittest
from unittest.mock import patch
from batch_artifacts import publish
from batch_artifacts_test import MemoryStore
from batch_transport_test import pending
from batch_transport import Call
from batch_pair import audit, invoke


def evidence(mutate=lambda x: None):
    store = MemoryStore()
    pins = {}
    for peer, pid in (('client', 42), ('proxy', 43)):
        handle = pending(); out = handle.finish(1)
        out['command'] = [peer]; out['client_cleanup']['pid'] = pid;handle.owner.pid=pid
        pins[peer] = Call(handle, [peer], store, peer).finish(1)
    frame = dict(schema='unison-retained-merge-proxy/1', server_command=['server'],
                 server_pid=44, server_returncode=0, server_reaped=True, server_group=43,
                 input_eof_forwarded=True, output_eof_forwarded=True,
                 forwarded_protocol_bytes=dict(client_to_server_bytes=10, server_to_client_bytes=20),
                 parent_group_audit_required=True, sdk_helper_audit_required=True,
                 resource_release_authorized=False)
    mutate(frame)
    pins['server_frame'] = publish(store, 'server', json.dumps(frame).encode())
    return store, pins


class PairTests(unittest.TestCase):
    def test_distinct_source_bound_roles_require_external_audit(self):
        store, pins = evidence()
        out = audit(store, pins, client_command=['client'], proxy_command=['proxy'], server_command=['server'])
        self.assertEqual((out['client_pid'], out['proxy_pid'], out['server_pid']), (42,43,44))
        self.assertTrue(out['external_children_source_audit_required'])
        self.assertFalse(out['resource_release_authorized'])

    def test_false_native_binding_and_incomplete_forwarding_refuse(self):
        for mutate in (lambda x:x.update(server_pid=42), lambda x:x.update(server_group=42),
                       lambda x:x.update(server_reaped=False), lambda x:x.update(server_returncode=True),
                       lambda x:x.update(input_eof_forwarded=False), lambda x:x.update(server_command=['other']),
                       lambda x:x['forwarded_protocol_bytes'].update(client_to_server_bytes=True)):
            store, pins = evidence(mutate)
            with self.assertRaises(ValueError):
                audit(store, pins, client_command=['client'], proxy_command=['proxy'], server_command=['server'])

    def test_bad_pair_preflight_starts_nothing(self):
        with patch('batch_pair.launch') as launch:
            with self.assertRaises(ValueError):
                invoke(['client'], {}, proxy_command=['proxy'], proxy_environment={},
                       server_command=['server'], socket_path='/never-created', deadline=0,
                       pass_fds=(), store=MemoryStore(), name='case', read_proxy_bytes=lambda:b'')
            launch.assert_not_called()

    def test_live_peer_handle_is_preserved_on_readiness_failure(self):
        import time
        handle = object()
        with patch('batch_pair.launch', return_value=type('Handle', (), {'pending': handle})()), \
             patch('batch_pair.wait_socket', side_effect=RuntimeError('readiness failure')):
            from shared_cpu_pool import UnresolvedOwnership
            with self.assertRaises(UnresolvedOwnership) as got:
                invoke(['client'], {}, proxy_command=['proxy'], proxy_environment={},
                       server_command=['server'], socket_path='/never-created', deadline=time.monotonic()+10,
                       pass_fds=(), store=MemoryStore(), name='case', read_proxy_bytes=lambda:b'')
            self.assertIs(got.exception.batch_pair_handles[0].pending, handle)


if __name__ == '__main__': unittest.main()
