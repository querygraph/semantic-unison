"""Only original tiny mocked controls; no payload or native clone dispatch."""
from pathlib import Path
import unittest

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='*_test.py')
    raise SystemExit(0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1)
