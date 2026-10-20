import unittest
from unittest.mock import patch
from pathlib import Path
from batch_series import schedule
from batch_series_report import audit,markdown
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

    def test_interpretation_follows_samples_instead_of_canned_speedup_claim(self):
        def row(mode,value):
            return dict(label='stock',workers=3,mode=mode,
                client_elapsed_seconds=dict(median=value,minimum=value,maximum=value),
                pair_elapsed_seconds=dict(median=value+1))
        report=dict(summary=[row('ordinary',1),row('receiver-clone',2),row('semantic',3)])
        self.assertIn('Ordinary transfer is faster',markdown(report))
        report['summary'][2]=row('semantic',.5)
        self.assertNotIn('Ordinary transfer is faster',markdown(report))
        self.assertIn('not instrumented',markdown(report))


if __name__=='__main__':unittest.main()
