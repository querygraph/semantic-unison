"""Original inert planner/transport/diagnostic controls; zero SDK or media IO."""
import unittest


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'all_scanned_sdk_plan_test',
        'all_scanned_sdk_transport_test',
        'all_scanned_sdk_audit_test',
        'all_scanned_sdk_parent_test',
        'all_scanned_sdk_prepare_test',
        'all_scanned_sdk_worker_test',
        'all_scanned_sdk_verify_test',
        'all_scanned_sdk_worker_verify_test',
        'all_scanned_sdk_paths_test',
        'all_scanned_sdk_prefix_test',
        'all_scanned_sdk_boundary_test',
        'all_scanned_sdk_entry_test',
        'all_scanned_sdk_groups_test',
        'invocation_journal_test',
        'shared_cpu_pool_test',
        'shared_io_pool_test',
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
