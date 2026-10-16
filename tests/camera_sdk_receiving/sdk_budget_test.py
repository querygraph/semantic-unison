"""Original pure arithmetic checks; no files, pools, SDK or payload."""
import unittest
import sdk_budget as b


class Controls(unittest.TestCase):
    def test_explicit_gate_fits_source_and_consumer(self):
        proof=b.validate()
        self.assertEqual(proof['minimum_gate_bytes'],2416443392)
        self.assertLessEqual(proof['minimum_gate_bytes'],4096*b.MIB)
        self.assertFalse(proof['hard_rss_cap'])
    def test_actual_failed_configuration_refused(self):
        with self.assertRaises(ValueError):b.validate(gate_mib=512,workspace_mib=2048)
    def test_estimate_alone_fitting_gate_is_insufficient(self):
        with self.assertRaises(ValueError):b.validate(gate_mib=2048,workspace_mib=2048)
    def test_typed_positive_bounded_declarations(self):
        for values in ((True,1),(4096,True),(0,1),(4096,0),(32769,1),(-1,1)):
            with self.subTest(values=values),self.assertRaises(ValueError):
                b.validate(gate_mib=values[0],workspace_mib=values[1])


if __name__=='__main__':unittest.main()
