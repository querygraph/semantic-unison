"""Original saved-number controls, no sync, source files, pools or helpers."""
import copy
import unittest
from resource_report import build_report


def fixture(system='Darwin'):
    resources=dict(wait4_user_seconds=.1,wait4_system_seconds=.2,
                   wait4_maxrss_native_units=4096,block_input_operations=2,block_output_operations=3)
    return dict(schema='unison-synthetic-sync/0',complete=True,host=dict(system=system),parameters={},
        samples=[dict(label='stock',mode='semantic',workers=1,phase='measured',repetition=1,
            update_sync=dict(wall_seconds=1.,resources=resources,
                proxy=dict(server_resources=resources,forwarded_protocol_bytes=dict(client_to_server_bytes=7,server_to_client_bytes=9))),
            counters=dict(primary_reader_reads=dict(reported_jobs=1,logical_bytes=64,
                records=[dict(logical_bytes=64)],scope='primary only',absence=None),
                semantic_logical_write_bytes=4,materialization_non_inherited_logical_bytes_model=4,
                materialization_model_basis='returned writes'))])


class Report(unittest.TestCase):
    def test_keeps_cpu_endpoints_separate_and_no_lifecycle_inference(self):
        r=build_report(fixture());row=r['rows'][0]
        self.assertAlmostEqual(row['client_wait4']['cpu_seconds'],.3)
        self.assertAlmostEqual(row['server_wait4']['cpu_seconds'],.3)
        self.assertNotIn('total_cpu_seconds',row)
        self.assertFalse(r['actual_parent_terminal_or_resource_release_inferred'])
    def test_rss_units_and_unknown_platform(self):
        for system,expected in [('Darwin',4096),('Linux',4096*1024),('Other',None)]:
            self.assertEqual(build_report(fixture(system))['rows'][0]['client_wait4']['maxrss_bytes'],expected)
    def test_unknown_reads_and_models_are_not_zero_or_physical(self):
        v=fixture();reads=v['samples'][0]['counters']['primary_reader_reads']
        reads.update(logical_bytes=None,reported_jobs=0,records=[],absence='not observed')
        row=build_report(v)['rows'][0]
        self.assertIsNone(row['primary_reader']['logical_bytes'])
        self.assertIsNone(row['application_read_bytes'])
        self.assertIsNone(row['physical_storage_write_bytes'])
        self.assertEqual(row['non_inherited_output_extent_model_bytes'],4)
    def test_real_zero_preserved_and_partial_not_passed(self):
        v=fixture();v['complete']=False;v['samples'][0]['update_sync']['resources']['wait4_user_seconds']=0.
        r=build_report(v);self.assertFalse(r['input_complete'])
        self.assertEqual(r['rows'][0]['client_wait4']['user_seconds'],0.)
        self.assertEqual(r['state'],'SAVED_OBSERVATIONS_ONLY')
    def test_nonfinite_negative_and_bool_numbers_refuse(self):
        for bad in [float('nan'),float('inf'),-1,True]:
            v=fixture();v['samples'][0]['update_sync']['wall_seconds']=bad
            with self.assertRaises(ValueError):build_report(v)
    def test_mismatched_reader_count_refuses(self):
        v=fixture();v['samples'][0]['counters']['primary_reader_reads']['logical_bytes']=63
        with self.assertRaises(ValueError):build_report(v)
    def test_derived_overflow_refuses(self):
        v=fixture();resources=v['samples'][0]['update_sync']['resources']
        resources.update(wait4_user_seconds=1e308,wait4_system_seconds=1e308)
        with self.assertRaises(ValueError):build_report(v)
        v=fixture('Linux');v['samples'][0]['update_sync']['resources']['wait4_maxrss_native_units']=1e308
        with self.assertRaises(ValueError):build_report(v)
    def test_missing_update_and_missing_server_remain_explicit(self):
        v=fixture();v['samples'][0]['update_sync']['proxy']=None
        row=build_report(v)['rows'][0];self.assertIsNone(row['server_wait4'])
        self.assertIsNone(row['forwarded_protocol_bytes'])
        del v['samples'][0]['update_sync']
        self.assertEqual(build_report(v)['rows'][0]['availability'],'NO_COMPLETED_UPDATE_RECEIPT')


if __name__=='__main__':unittest.main()
