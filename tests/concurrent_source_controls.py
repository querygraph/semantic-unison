"""Run the original concurrent-receiving source suites; no receiving/SDK entry."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'tests/camera_sdk_concurrency'
sys.path.insert(0,str(HERE))
if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern='*_test.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
