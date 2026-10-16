"""Original tiny fake SDK diagnostic/case controls only; zero native helpers."""
from pathlib import Path
import unittest

if __name__ == '__main__':
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='*_test.py')
    raise SystemExit(0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1)
