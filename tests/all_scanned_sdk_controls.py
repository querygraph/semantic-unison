"""Original inert planner/transport/diagnostic controls; zero SDK or media IO."""
import unittest


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'all_scanned_sdk_plan_test',
        'all_scanned_sdk_transport_test',
        'all_scanned_sdk_audit_test',
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
