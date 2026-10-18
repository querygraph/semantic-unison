"""Original fixed phase-trace controls; no process/fixture/payload execution."""
import copy
import unittest
from unittest.mock import patch
import phase_stats as p
from run import internal_counters, diagnostic_text


def line(job=0,stage='hash',calls=1,seconds='0.125000000',server=False):
    tag='server: semantic-timings' if server else 'semantic-timings'
    return f'[{tag}] Semantic worker job {job} stage={stage} calls={calls} inclusive-seconds={seconds}.'


def publication(seconds='0.250000000',server=False):
    tag='server: semantic-timings' if server else 'semantic-timings'
    return f'[{tag}] Semantic bound publication native-inclusive-seconds={seconds}.'


def unavailable(server=False):
    tag='server: semantic-timings' if server else 'semantic-timings'
    return f'[{tag}] Semantic worker job 0 stage timing unavailable.'


class Phase(unittest.TestCase):
    def test_worker_endpoint_and_stage_namespaces(self):
        v=p.parse('\n'.join([line(),line(stage='parse'),line(server=True)]),required_workers=True)
        self.assertEqual(v['reported_worker_jobs'],2)
        self.assertEqual(v['observed_worker_stages'],['hash','parse'])
        self.assertEqual(p.validate(v),v)
    def test_overlap_is_not_summed_and_identical_publications_are_distinct(self):
        v=p.parse('\n'.join([line(),line(stage='verify'),publication(),publication()]))
        self.assertEqual(v['namespace_publication_observations'],2)
        self.assertNotIn('total_seconds',v)
        self.assertEqual(len(v['records']),4)
    def test_unknown_unavailable_and_measured_zero_differ(self):
        missing=p.parse('unrelated output')
        self.assertIsNotNone(missing['worker_absence']);self.assertIsNotNone(missing['namespace_absence'])
        zero=p.parse(line(seconds='0.000000000'))
        self.assertEqual(zero['records'][0]['inclusive_seconds'],0.)
        v=p.parse(unavailable(),required_workers=True)
        self.assertEqual(v['unavailable_worker_jobs'],1)
        self.assertIsNone(v['records'][0]['inclusive_seconds']);self.assertIsNone(v['worker_absence'])
        v=p.parse('[semantic-timings] Semantic bound publication timing unavailable.')
        self.assertEqual(v['namespace_publication_observations'],1)
        self.assertIsNone(v['records'][0]['inclusive_seconds']);self.assertEqual(p.validate(v),v)
    def test_duplicate_and_conflicting_worker_reports_refuse_both_orders(self):
        for values in ([line(),line()],[unavailable(),unavailable()],
                       [line(),unavailable()],[unavailable(),line()]):
            with self.assertRaises(ValueError):p.parse('\n'.join(values))
    def test_malformed_nonfinite_noncanonical_and_bounds_refuse(self):
        for text in [line(job=-1),line(job=p.MAXIMUM+1),line(calls=0),line(calls=p.MAXIMUM+1),
                     line(job='00'),line(calls='01'),line(job='\u0661'),line(seconds='00.125000000'),
                     line(seconds='nan'),line(seconds='inf'),line(seconds='-0.125000000'),
                     line(seconds='1e-9'),line(seconds='0.125'),line(stage='commit'),
                     line()+' trailing',line(server=True).replace('server: ','server:'),line().replace('semantic-timings]','semantic-timings-bad]')]:
            with self.subTest(text=text),self.assertRaises(ValueError):p.parse(text)
        with self.assertRaises(ValueError):p.parse('',required_workers=True)
    def test_log_record_and_type_bounds(self):
        for value in (None,True,'x'*(p.MAX_LOG+1)):
            with self.assertRaises(ValueError):p.parse(value)
        with patch.object(p,'MAX_RECORDS',1):
            with self.assertRaises(ValueError):p.parse(publication()+'\n'+publication())
        with self.assertRaises(ValueError):p.parse('[semantic-timings] '+'x'*300)
    def test_saved_values_rebind_raw_fields_counts_and_types(self):
        good=p.parse(line(calls=1,seconds='1.000000000'))
        for field,bad in [('calls',True),('inclusive_seconds',1),('inclusive_seconds',float('nan')),
                          ('endpoint','server'),('stage','parse')]:
            v=copy.deepcopy(good);v['records'][0][field]=bad
            with self.subTest(field=field,bad=bad),self.assertRaises(ValueError):p.validate(v)
        for field,bad in [('reported_worker_jobs',True),('scope','changed'),('extra',None)]:
            v=copy.deepcopy(good);v[field]=bad
            with self.assertRaises(ValueError):p.validate(v)
        v=copy.deepcopy(good);v['records'][0]['raw_line']+='\n'+publication()
        with self.assertRaises(ValueError):p.validate(v)
        self.assertIsNone(p.validate(None))
    def test_stream_boundaries_do_not_hide_or_manufacture_records(self):
        value=diagnostic_text(dict(stdout='no trailing newline',stderr=line(),supervisor_output=''))
        self.assertEqual(p.parse(value)['reported_worker_jobs'],1)
        first=line().removesuffix('0.125000000.')
        value=diagnostic_text(dict(stdout=first,stderr='0.125000000.',supervisor_output=''))
        with self.assertRaises(ValueError):p.parse(value)
    def test_benchmark_flag_default_and_partial_measurements(self):
        log=('Remote semantic clone wrote 4 logical metadata bytes in 1 write calls '
             '(4 payload bytes; 4096-byte comparison windows; org.firstpair.dng-xmp/0)\n')
        self.assertIsNone(internal_counters(log,'semantic',1,4096)['semantic_phase_observations'])
        with self.assertRaises(ValueError):internal_counters(log,'semantic',1,4096,phase_timings=True)
        v=internal_counters(log+line()+'\n'+publication(),'semantic',1,4096,phase_timings=True)
        self.assertEqual(len(v['semantic_phase_observations']['records']),2)
        self.assertIsNone(v['hash_parse_verify_commit_seconds'])
        self.assertIsNone(v['application_read_bytes'])


if __name__=='__main__':unittest.main()
