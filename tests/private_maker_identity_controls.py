"""Finite original model-field suite, CPU8 only, no retained camera reads."""
import unittest

if __name__ == '__main__':
    names = ['private_maker_identity_test', 'private_maker_identity_entry_test',
             'private_maker_coverage_test', 'private_maker_shape_test',
             'private_maker_slice_test', 'private_maker_plan_test', 'private_maker_dispatch_test']
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
