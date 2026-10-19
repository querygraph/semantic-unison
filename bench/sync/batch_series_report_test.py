import unittest
from unittest.mock import patch
from pathlib import Path
from batch_series import schedule
from batch_series_report import audit
from shared_cpu_pool import UnresolvedOwnership


class ReportOwnership(unittest.TestCase):
    def packet(self):
        return dict(workers=[1],samples=[dict(identity=row) for row in schedule()])

    def test_shrunken_schedule_refuses_before_directory_open(self):
        packet=self.packet();packet['samples'].pop()
        with patch('batch_series_report.Store') as store:
            with self.assertRaises(ValueError):audit('/private/tmp',packet)
            store.assert_not_called()

    def test_known_incomplete_result_closes_directory(self):
        with patch('batch_series_report.Store') as factory:
            store=factory.return_value
            store.read_json.return_value=dict(complete=False)
            with self.assertRaises(ValueError):audit('/private/tmp',self.packet())
            store.close.assert_called_once_with()

    def test_uncertain_read_preserves_owner_without_numeric_close_retry(self):
        failure=UnresolvedOwnership('injected uncertain metadata close',retained_fds=(111,),uncertain_fd=222)
        with patch('batch_series_report.Store') as factory:
            store=factory.return_value;store.read_json.side_effect=failure
            with self.assertRaises(UnresolvedOwnership) as caught:audit('/private/tmp',self.packet())
            self.assertIs(caught.exception,failure)
            self.assertEqual(caught.exception.retained_fds,(111,))
            self.assertEqual(caught.exception.uncertain_fd,222)
            store.close.assert_not_called()


if __name__=='__main__':unittest.main()
