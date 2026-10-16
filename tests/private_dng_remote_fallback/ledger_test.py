"""Fixed fabricated ledger controls; no transport, native or payload dispatch."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from ledger import begin, record, settled, audit_directory


def outcome():
    def group(pid):
        return dict(pid=pid, reaped=True, returncode=0,
                    group_cleanup_before_leader_reap=True,
                    other_group_members_absent_before_reap=True)
    return dict(command=['/fixed/fake-unison', 'synthetic'], returncode=0,
                client_cleanup=group(991), supervisor_cleanup=group(992),
                proxy=dict(server_cleanup=dict(pid=993, reaped=True, returncode=0),
                           server_pid=993, server_returncode=0, input_pump_joined=True))


class Controls(unittest.TestCase):
    def test_complete_prefix(self):
        with tempfile.TemporaryDirectory() as name:
            for stage in ('seed', 'update', 'noop'):
                v = outcome(); begin(name, stage, v['command']); record(name, stage, v)
            self.assertEqual(len(audit_directory(name)), 3)

    def test_failed_but_settled_is_not_success(self):
        v = outcome(); v['returncode'] = v['client_cleanup']['returncode'] = 1
        v['proxy']['server_returncode'] = v['proxy']['server_cleanup']['returncode'] = -15
        v['proxy']['fault'] = 'preserved failure'; v['proxy']['pump_errors'] = ['preserved']
        self.assertTrue(settled(v)['test_success_not_inferred'])

    def test_all_direct_group_fields_required(self):
        for key in ('client_cleanup', 'supervisor_cleanup'):
            for field, bad in (('pid', True), ('reaped', False), ('returncode', False),
                               ('group_cleanup_before_leader_reap', False),
                               ('other_group_members_absent_before_reap', False)):
                v = outcome(); v[key][field] = bad
                with self.subTest(key=key, field=field), self.assertRaises(ValueError): settled(v)

    def test_server_binding_and_join(self):
        for change in ('pid', 'reaped', 'returncode', 'join', 'binding', 'collision', 'client-binding'):
            v = outcome(); p = v['proxy']
            if change == 'pid': p['server_cleanup']['pid'] = True
            elif change == 'reaped': p['server_cleanup']['reaped'] = False
            elif change == 'returncode': p['server_returncode'] = True
            elif change == 'join': p['input_pump_joined'] = False
            elif change == 'binding': p['server_pid'] = 994
            elif change == 'collision': p['server_pid'] = p['server_cleanup']['pid'] = 991
            else: v['returncode'] = 1
            with self.subTest(change=change), self.assertRaises(ValueError): settled(v)

    def test_pending_or_orphan_never_settled(self):
        for orphan in (False, True):
            with tempfile.TemporaryDirectory() as name:
                v = outcome(); begin(name, 'seed', v['command'])
                if orphan:
                    record(name, 'seed', v); (Path(name)/'seed-INTENT.json').unlink()
                with self.subTest(orphan=orphan), self.assertRaises(ValueError): audit_directory(name)

    def test_prefix_and_exact_command(self):
        with tempfile.TemporaryDirectory() as name:
            v = outcome(); begin(name, 'update', v['command']); record(name, 'update', v)
            with self.assertRaises(ValueError): audit_directory(name)
        with tempfile.TemporaryDirectory() as name:
            v = outcome(); begin(name, 'seed', v['command'])
            other = deepcopy(v); other['command'] = ['/different']
            with self.assertRaises(ValueError): record(name, 'seed', other)
            record(name, 'seed', v)
            with self.assertRaises(FileExistsError): record(name, 'seed', v)
            with self.assertRaises(FileExistsError): begin(name, 'seed', v['command'])

    def test_malformed_and_unknown_remain_unknown(self):
        with tempfile.TemporaryDirectory() as name:
            self.assertEqual(audit_directory(name), [])
            (Path(name)/'seed-INTENT.json').write_text('{')
            (Path(name)/'seed-OUTCOME.json').write_text('{}')
            with self.assertRaises(json.JSONDecodeError): audit_directory(name)
        with tempfile.TemporaryDirectory() as name:
            for suffix in ('INTENT', 'OUTCOME'):
                (Path(name)/('extra-'+suffix+'.json')).write_text('{}')
            with self.assertRaises(ValueError): audit_directory(name)


if __name__ == '__main__': unittest.main()
