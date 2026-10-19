import unittest
from pathlib import Path
from final_archive_roundtrip_owner import command

class Commands(unittest.TestCase):
    def test_generations_and_fixed_state_roots_across_all_twenty_calls(self):
        artifacts={name:dict(path='/private/tmp/'+name) for name in ('stock','ox','old-stock')}
        for case in range(2):
            roots=[]
            for phase in range(10):
                row=command(artifacts,Path('/private/tmp/u-archive-original'),case,phase)
                argv=row['command'];roots.append(argv[1:3])
                self.assertEqual(row['server_command'][:3],[row['server'],'-server','__new-rpc-mode'])
                self.assertLessEqual(row['configured_endpoint_plus_owner_bound'],row['reserved_credits'])
                if phase in (2,3):
                    self.assertEqual(row['server'],'/private/tmp/old-stock');self.assertNotIn('-semanticdng',argv)
                    self.assertEqual(row['server_flags'],['-maxthreads','2'])
                else:
                    self.assertIn('-semanticmergebasecache',argv);self.assertEqual(argv[argv.index('-adobevalidate')+1],'off')
                    self.assertEqual(argv[argv.index('-semanticcpubudget')+1],'2')
            self.assertTrue(all(r==roots[0] for r in roots))
    def test_invalid_case_is_preentry_refused(self):
        for n in (-1,2,True):
            with self.assertRaises(ValueError):command({},Path('/private/tmp/u-archive-original'),n,0)

if __name__=='__main__':unittest.main()
