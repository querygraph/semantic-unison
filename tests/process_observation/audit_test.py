"""Reparse original component evidence and independently corrupt its bindings."""
import copy
import json
from pathlib import Path
import unittest
from audit import audit

ROOT=Path(__file__).resolve().parents[2]
RECEIPT=ROOT/'tests/qualification/retained-os-probe-actual-20261016.json'


class Audit(unittest.TestCase):
    def setUp(self):
        self.r=json.loads(RECEIPT.read_text())['result']
    def check(self):
        return audit(self.r['observed_child'],self.r['probe_children'],
                     probe_path='/private/tmp/unison-os-process-observation-20261016a/controls/probe',
                     probe_sha256='fc122e591ef1b5e2c943675c4193ac19b43870ba4e08597e7f894f7a91a1b017',
                     recorded_probe_sha256=self.r['probe_sha256'])
    def test_actual_saved_three_samples_reparse(self):
        result=self.check();self.assertEqual(result['available_samples'],3)
        self.assertFalse(result['resource_release_authorized'])
    def test_missing_stays_missing_without_zeros(self):
        p=self.r['observed_child']['client_cleanup']['pid']
        self.r['probe_children'][0]['stdout']=json.dumps(dict(pid=p,available=False,errno=3))
        self.r['observed_child']['process_observations']['samples'][0]['observation']=dict(pid=p,available=False)
        self.assertEqual(self.check()['missing_samples'],1)
    def test_corruptions_refuse(self):
        original=copy.deepcopy(self.r)
        mutations=[
            lambda r:r['probe_children'].pop(),
            lambda r:r['probe_children'][0]['client_cleanup'].update(reaped=False),
            lambda r:r['probe_children'][0]['command'].__setitem__(1,'999'),
            lambda r:r['probe_children'][1].update(client_cleanup=r['probe_children'][0]['client_cleanup']),
            lambda r:r['observed_child']['process_observations']['samples'][0]['observation'].update(resident_bytes=0),
            lambda r:r['observed_child']['process_observations']['samples'][0]['observation'].update(threads=True),
            lambda r:r['observed_child']['process_observations']['samples'][0].update(after_monotonic_ns=0),
            lambda r:r['probe_children'][0].update(stdout='{"pid":1,"pid":2,"available":false}'),
            lambda r:r['probe_children'][0].update(capture_truncated=True),
            lambda r:r.update(probe_sha256='0'*64),
            lambda r:r['observed_child']['process_observations'].update(resource_release_authorized=True),
        ]
        for mutate in mutations:
            self.r=copy.deepcopy(original);mutate(self.r)
            with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
