import unittest
from pathlib import Path
from final_upstream_peer_owner import command,CASES


class Commands(unittest.TestCase):
    artifacts={name:dict(path='/private/tmp/'+name) for name in ('stock','ox','old-stock')}
    def test_both_current_compilers_and_orientations_keep_old_peer_flags_separate(self):
        self.assertEqual(len(CASES),4)
        for index in range(4):
            row=command(self.artifacts,Path('/private/tmp/u-peer-fixture'),index)
            self.assertEqual(row['server_command'][:3],[row['server'],'-server','__new-rpc-mode'])
            old=row['orientation']=='upstream-client'
            if old:
                self.assertEqual(row['client'],'/private/tmp/old-stock')
                self.assertNotIn('-semanticworkers',row['command'])
                self.assertIn('-semanticcpubudget',row['server_flags'])
            else:
                self.assertEqual(row['server_flags'],['-maxthreads','2'])
                self.assertIn('-adobevalidate',row['command'])
            self.assertLessEqual(row['configured_endpoint_plus_owner_bound'],row['reserved_credits'])

    def test_invalid_case_or_missing_artifact_refuses_before_launch(self):
        for index in (True,-1,4):
            with self.assertRaises(ValueError):command(self.artifacts,Path('/private/tmp/u-peer-fixture'),index)
        with self.assertRaises(ValueError):command({},Path('/private/tmp/u-peer-fixture'),0)


if __name__=='__main__':unittest.main()
