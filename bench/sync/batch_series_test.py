import copy,unittest
from batch_series import schedule,summarize


class Series(unittest.TestCase):
    def rows(self):
        return [dict(identity=row,complete=True,update=dict(client_elapsed_ns=1000000000+row['repetition'],pair_elapsed_ns=2000000000+row['repetition'])) for row in schedule()]
    def test_all_modes_both_compilers_and_repetitions_retained(self):
        rows=self.rows();out=summarize(rows)
        self.assertEqual(len(rows),36);self.assertEqual(len(out),6)
        self.assertEqual(sum(r['identity']['phase']=='warmup' for r in rows),6)
        self.assertTrue(all(len(g['client_elapsed_seconds']['raw'])==5 for g in out))
        measured=[r['identity'] for r in rows if r['identity']['phase']=='measured']
        self.assertEqual(measured[6]['label'],'ox')
    def test_partial_duplicate_failed_or_bool_clock_refuse(self):
        for mutation in (lambda r:r.pop(),lambda r:r.__setitem__(1,copy.deepcopy(r[0])),
                         lambda r:r[3].update(complete=False),lambda r:r[0]['update'].update(client_elapsed_ns=True)):
            rows=self.rows();mutation(rows)
            with self.assertRaises(ValueError):summarize(rows)
    def test_worker_overcommit_or_reduced_repetitions_refuse(self):
        for kwargs in (dict(workers=(4,)),dict(repetitions=4),dict(warmups=0),dict(workers=(1,1))):
            with self.assertRaises(ValueError):schedule(**kwargs)


if __name__=='__main__':unittest.main()
