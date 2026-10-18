"""Original saved-only summary controls, no fixture or executable IO."""
import copy
import unittest
from timed_shared_test import fixture
import sync_timed_summary as report


def saved():
    value=fixture();value['host']={'system':'Darwin'}
    for row in value['samples']:
        update=row['update_sync'];update['wall_seconds']=1000 if row['phase']=='warmup' else row['repetition']
        update['proxy']['forwarded_protocol_bytes']={'client_to_server_bytes':0,'server_to_client_bytes':10}
        row['counters']['semantic_logical_write_bytes']=0
    # Rebind journal after adding actual observation fields.
    for index,row in enumerate(value['samples']):
        for offset,field in enumerate(('seed_sync','update_sync','noop_sync')):
            value['invocations'][index*3+offset]['outcome']=copy.deepcopy(row[field])
    return value


class Summary(unittest.TestCase):
    def test_all_samples_retained_warmup_separate(self):
        value=saved();before=copy.deepcopy(value);result=report.summarize(value)
        self.assertEqual(result['raw_rows_retained'],108)
        self.assertEqual(len(result['groups']),18)
        for group in result['groups']:
            self.assertEqual(group['update_wall_seconds']['samples'],[1,2,3,4,5])
            self.assertEqual(group['update_wall_seconds']['median'],3)
            self.assertEqual(group['update_wall_seconds']['p90_nearest_rank'],5)
            self.assertFalse(group['client_cpu_seconds']['available'])
            self.assertEqual(group['semantic_returned_write_bytes']['median'],0)
        self.assertEqual(value,before)

    def test_unknown_is_not_zero_and_bad_numbers_refuse(self):
        self.assertIsNone(report.distribution([0,None,1])['median'])
        self.assertEqual(report.distribution([0,0,0])['median'],0)
        for bad in (True,-1,float('nan'),float('inf')):
            with self.subTest(bad=bad),self.assertRaises(ValueError):report.distribution([bad,None])

    def test_no_summary_of_partial_or_unbound_rows(self):
        value=saved();value['complete']=False
        with self.assertRaises(ValueError):report.summarize(value)
        value=saved();value['samples'][0]['update_sync']['wall_seconds']=999
        with self.assertRaises(ValueError):report.summarize(value)

if __name__=='__main__':unittest.main()
