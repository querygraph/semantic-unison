import math
import unittest
from report_warm512_distribution import empirical


class Distribution(unittest.TestCase):
    def test_empirical_ranks_preserve_equal_and_outlying_samples(self):
        raw=[dict(seconds=v,source_row=i) for i,v in enumerate([10.,1.,1.,100.])]
        got=empirical(raw)
        self.assertEqual([s['source_row'] for s in got],[1,2,0,3])
        self.assertEqual([s['cumulative_fraction'] for s in got],[.25,.5,.75,1.])
        self.assertEqual([s['rank'] for s in got],[1,2,3,4])
        self.assertEqual(raw[0],dict(seconds=10.,source_row=0))
    def test_no_empty_imputed_or_nonfinite_samples(self):
        with self.assertRaises(ValueError):empirical([])
        for value in [0.,-1.,True,1,None,math.inf,math.nan]:
            with self.assertRaises(ValueError):empirical([dict(seconds=value,source_row=0)])


if __name__=='__main__':unittest.main()
