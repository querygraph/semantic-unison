"""Finite original fixture and mocked-owner controls; never runs transport."""
from pathlib import Path
import sys
import unittest


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    suite = unittest.defaultTestLoader.discover(str(here), pattern='*_test.py')
    # Include the dispatcher regression for the exact observed pre-entry
    # failure; fake grants/owners only, not a canonical IO attempt.
    sys.path.insert(0, str(here.parent))
    import shared_io_dispatch_lifecycle_test
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(shared_io_dispatch_lifecycle_test))
    raise SystemExit(0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1)
