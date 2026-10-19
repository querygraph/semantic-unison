"""Original inert descriptor/store/native doubles; retain loop replaced by sentinel."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from sdk_merge_receiving import child_entry as child
from sdk_merge_receiving.admission import PYTHON

class Retained(Exception):pass

class Entries(unittest.TestCase):
    def config(self):
        return dict(directory='/private/tmp/inert',identity=dict(device=1,inode=2),stage='seed',
            binary='/qualified/ox',flags=['-semanticcpubudget','2'],deadline=100,
            worker_pid=11,resource_fds=[dict(fd=700+i,device=1,inode=700+i) for i in range(9)])

    def test_retained_diagnostic_preserves_all_saved_uncertainty_without_fd_query(self):
        from shared_io_pool import UnresolvedIOOwnership
        record=dict(fd=701,role='inert',observed_before_close=None)
        error=UnresolvedIOOwnership('original',retained_fds=(702,),uncertain_closes=[record],
                                    original_failure=ValueError('original cause'))
        error.proxy_native_child=SimpleNamespace(pid=123,returncode=None)
        with patch.object(child.os,'fstat',side_effect=AssertionError('must not query uncertain FD')):
            value=child.diagnostic('proxy',error)
        self.assertEqual(value['uncertain_closes'],[record]);self.assertEqual(value['retained_fds'],[702])
        self.assertEqual(value['native_child_pid'],123)
        self.assertFalse(value['resource_release_authorized']);self.assertFalse(value['process_settlement_proved'])

    def test_proxy_parent_guard_precedes_descriptor_or_native_access(self):
        with patch.object(child.os,'getppid',return_value=12), \
             patch.object(child,'descriptors') as descriptors,patch.object(child,'serve') as serve, \
             patch.object(child,'retain_after_record',side_effect=Retained):
            with self.assertRaises(Retained):child.proxy_main(self.config())
            descriptors.assert_not_called();serve.assert_not_called()

    def test_descriptor_uncertainty_precedes_native_and_is_retained(self):
        with patch.object(child.os,'getppid',return_value=11), \
             patch.object(child.sys,'executable',PYTHON), \
             patch.object(child,'descriptors',side_effect=ValueError('inert identity mismatch')), \
             patch.object(child,'serve') as serve,patch.object(child,'retain_after_record',side_effect=Retained):
            with self.assertRaises(Retained):child.proxy_main(self.config())
            serve.assert_not_called()

    def test_success_records_actual_proxy_parent_binding_before_serve(self):
        events=[]
        store=SimpleNamespace(write=lambda name,value:events.append(('write',name,value)),
                              close=lambda:events.append(('close',)))
        def serve(*args):events.append(('serve',args));return dict(original='fake frame')
        with patch.object(child.os,'getppid',return_value=11),patch.object(child.os,'getpid',return_value=22), \
             patch.object(child.sys,'executable',PYTHON),patch.object(child,'descriptors',return_value=dict(original='fake binding')), \
             patch.object(child,'Store',return_value=store),patch.object(child,'serve',side_effect=serve):
            self.assertEqual(child.proxy_main(self.config()),0)
        self.assertEqual([event[0] for event in events],['write','serve','write','close'])
        self.assertEqual(events[0][2]['proxy_pid'],22);self.assertEqual(events[0][2]['worker_pid'],11)

if __name__=='__main__':unittest.main()
