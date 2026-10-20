"""Original fixed grouping/endpoint/reset controls, no native or payload calls."""
import unittest
from grouped_trace import decode

HEADER='[server: semantic-timings] Semantic worker job 7 stage=hash calls=1 inclusive-seconds=0.125000000.'
PARSE='Semantic worker job 7 stage=parse calls=1 inclusive-seconds=0.001000000.'
VERIFY='Semantic worker job 7 stage=verify calls=3 inclusive-seconds=0.250000000.'

class Grouped(unittest.TestCase):
    def test_group_preserves_raw_anchor_and_numbers(self):
        rows=decode('\n'.join([HEADER,PARSE,VERIFY]),endpoint='server',stream='supervisor_output')
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[1]['raw_line'],PARSE)
        self.assertTrue(rows[1]['inherited_prefix']);self.assertEqual(rows[1]['group_anchor']['raw_line'],HEADER)
        self.assertEqual(rows[2]['decoded']['calls'],3)
        self.assertNotIn('raw_line',rows[1]['decoded'])
    def test_orphan_noise_reset_job_order_and_duplicate_refuse(self):
        for text in (PARSE,HEADER+'\nnoise\n'+PARSE,HEADER+'\n\n'+PARSE,
                     HEADER+'\n'+PARSE.replace('job 7','job 8'),
                     HEADER+'\n'+VERIFY+'\n'+PARSE,HEADER+'\n'+PARSE+'\n'+PARSE):
            with self.subTest(text=text),self.assertRaises(ValueError):decode(text,endpoint='server',stream='saved')
    def test_endpoint_and_streams_never_inherited_across_boundary(self):
        with self.assertRaises(ValueError):decode(HEADER,endpoint='client',stream='stderr')
        decode(HEADER,endpoint='server',stream='supervisor_output')
        with self.assertRaises(ValueError):decode(PARSE,endpoint='server',stream='another')
    def test_explicit_new_headers_and_nonworker_records_reset_group(self):
        later='[server: semantic-timings] Semantic worker job 8 stage=parse calls=1 inclusive-seconds=0.000000000.'
        rows=decode(HEADER+'\n'+later,endpoint='server',stream='saved')
        self.assertEqual([r['decoded']['job'] for r in rows],[7,8])
        pub='[server: semantic-timings] Semantic bound publication native-inclusive-seconds=0.000000000.'
        with self.assertRaises(ValueError):decode(HEADER+'\n'+pub+'\n'+PARSE,endpoint='server',stream='saved')

if __name__=='__main__':unittest.main()
