import copy
import unittest
import all_scanned_sdk_parent_test as parent_controls
from all_scanned_sdk_groups import audit


class Groups(unittest.TestCase):
    def fixture(self):
        return parent_controls.Parent().fixture()[0]['invocations'][0]['outcome']

    def test_native_nonleader_is_joined_to_retained_proxy_group(self):
        out = self.fixture(); proof = audit(out)
        self.assertTrue(proof['observed_group_empty_before_group_leader_reap'])
        self.assertFalse(proof['native_was_group_leader'])
        self.assertFalse(proof['resource_release_authorized'])
        self.assertNotIn('group_cleanup_before_leader_reap', out['proxy']['server_cleanup'])

    def test_missing_binding_wrong_pgid_and_unsettled_group_refuse(self):
        for mutation in ('missing', 'pgid', 'reaped', 'late', 'bool', 'samepid'):
            out = self.fixture()
            if mutation == 'missing': out['proxy'].pop('server_group_binding')
            elif mutation == 'pgid': out['proxy']['server_group_binding']['native_process_group'] += 1
            elif mutation == 'reaped': out['supervisor_cleanup']['other_group_members_absent_before_reap'] = False
            elif mutation == 'late': out['proxy']['server_group_binding']['observed_before_native_reap'] = False
            elif mutation == 'bool': out['proxy']['server_group_binding']['native_pid'] = True
            else: out['proxy']['server_group_binding']['native_pid'] = out['supervisor_cleanup']['pid']
            with self.assertRaises(ValueError): audit(out)


if __name__ == '__main__': unittest.main()
