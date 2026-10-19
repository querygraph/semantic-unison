"""Original retained-proxy diagnostic controls; fake owners, no child or lock."""
import errno
import os
import unittest
from unittest.mock import Mock,patch
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership
from sdk_merge_receiving import child_entry


class Diagnostics(unittest.TestCase):
    def execute(self,error):
        store=Mock();store.closed=False
        config=dict(directory='/private/tmp/inert',identity=dict(device=1,inode=2),stage='seed',
                    binary='/inert',flags=[],deadline=1,worker_pid=os.getppid(),resource_fds=[])
        stopped=RuntimeError('retain loop intercepted by original control')
        def retain(callback):callback();raise stopped
        with patch.object(child_entry,'descriptors',return_value={}), \
             patch.object(child_entry,'Store',return_value=store), \
             patch.object(child_entry,'serve',side_effect=error), \
             patch.object(child_entry,'retain_after_record',side_effect=retain):
            with self.assertRaises(RuntimeError) as got:child_entry.proxy_main(config)
            self.assertIs(got.exception,stopped)
        store.close.assert_not_called()
        return store

    def test_plain_forwarding_failure_saved_before_retention(self):
        error=UnresolvedOwnership('forwarding unresolved');error.proxy_failure_phase='forwarding'
        error.proxy_original_errno=errno.ENOTCONN;error.proxy_pump_state=dict(client_eof=True,server_eof=True)
        store=self.execute(error)
        self.assertEqual([call.args[0] for call in store.write.call_args_list],['seed-INHERITED.json','seed-RETAINED.json'])
        record=store.write.call_args.args[1]
        self.assertEqual(record['failure_phase'],'forwarding');self.assertEqual(record['original_errno'],errno.ENOTCONN)
        self.assertFalse(record['resource_release_authorized'])

    def test_uncertain_close_never_opens_new_diagnostic_file(self):
        error=UnresolvedIOOwnership('close uncertain',uncertain_closes=[dict(fd=17,role='test',device=1,inode=2)])
        store=self.execute(error)
        self.assertEqual([call.args[0] for call in store.write.call_args_list],['seed-INHERITED.json'])


if __name__=='__main__':unittest.main()
