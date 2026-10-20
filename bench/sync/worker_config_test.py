"""Original selection/accounting controls; no binary or transport execution."""
import copy
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import worker_config as config
import run as sync


class MetadataReached(Exception):
    pass


class WorkerConfig(unittest.TestCase):
    def test_legacy_arguments_unchanged(self):
        for n in config.WORKER_CHOICES:
            self.assertEqual(config.worker_options(n),
                             ['-semanticworkers',str(n),'-maxthreads',str(max(2,n))])
            self.assertEqual(config.endpoint_bound(n),n)
        self.assertEqual(config.parse_workers('1,2,4,8'),[1,2,4,8])

    def test_auto_is_labeled_and_bounded_not_a_numeric_worker_count(self):
        self.assertEqual(config.parse_workers('1,2,4,8,auto'),[1,2,4,8,'auto'])
        self.assertEqual(config.endpoint_bound('auto',8),8)
        self.assertEqual(config.worker_options('auto',3),
                         ['-semanticworkers','0','-semanticcpubudget','3','-maxthreads','3'])
        self.assertEqual(config.worker_options(2,8),
                         ['-semanticworkers','2','-semanticcpubudget','8','-maxthreads','2'])

    def test_invalid_or_silently_clipped_comparison_refuses(self):
        for text in ['', 'auto,auto', '1,1', '0', '-1', 'true', 'Auto', '1.5']:
            with self.subTest(text=text),self.assertRaises(ValueError):config.parse_workers(text)
        for choice,ceiling in [('auto',None),(8,3),(True,8),(1,0),(1,-1),(1,37),(1,True)]:
            with self.subTest(choice=choice,ceiling=ceiling),self.assertRaises(ValueError):
                config.endpoint_bound(choice,ceiling)

    def test_main_rejects_unsafe_auto_before_metadata(self):
        cases=[
            (['--workers','auto'],False),
            (['--workers','auto','--endpoint-cpu-budget','3'],False),
            (['--workers','auto','--endpoint-cpu-budget','3','--loopback-cpu-credits','8','--orchestration-cpu-credits','2'],True),
            (['--workers','1,2,4,8,auto','--endpoint-cpu-budget','8','--loopback-cpu-credits','18','--orchestration-cpu-credits','2'],True),
            (['--workers','auto','--endpoint-cpu-budget','4','--loopback-cpu-credits','8','--orchestration-cpu-credits','2'],False),
            (['--workers','8','--endpoint-cpu-budget','3','--loopback-cpu-credits','18'],False),
            (['--workers','auto','--endpoint-cpu-budget','3','--loopback-cpu-credits','8','--shared-qualification','--orchestration-cpu-credits','2'],False),
            (['--workers','1,6,8','--endpoint-cpu-budget','8','--loopback-cpu-credits','18','--partition','0'],False),
            (['--workers','auto','--endpoint-cpu-budget','3','--loopback-cpu-credits','8','--reference','old='+sys.executable],False),
        ]
        for options,accepted in cases:
            argv=[str(sync.__file__),'--binary','stock='+sys.executable,
                  '--output','NEVER-CREATED-AUTO-BENCH.json',*options]
            with self.subTest(options=options),patch.object(sys,'argv',argv), \
                 patch.object(sys,'stderr',io.StringIO()), \
                 patch.object(sync,'binary_info',side_effect=MetadataReached) as metadata, \
                 patch.object(sync.subprocess,'run',side_effect=AssertionError('tool dispatch')):
                try:sync.main()
                except MetadataReached:self.assertTrue(accepted)
                except SystemExit as error:
                    self.assertFalse(accepted);self.assertEqual(error.code,2)
                else:self.fail('escaped pre-execution boundary')
                self.assertEqual(metadata.call_count,1 if accepted else 0)
        self.assertFalse(Path('NEVER-CREATED-AUTO-BENCH.json').exists())

    def test_prepare_records_selection_and_conservative_bound_separately(self):
        argv=[str(sync.__file__),'--binary','stock='+sys.executable,
              '--workers','1,2,4,8,auto','--endpoint-cpu-budget','8',
              '--loopback-cpu-credits','18','--orchestration-cpu-credits','2',
              '--prepare-only','--output','NEVER-CREATED-AUTO-BENCH.json']
        captured=[]
        def fake_save(path,value):captured.append(copy.deepcopy(value))
        with patch.object(sys,'argv',argv),patch.object(sync,'binary_info',return_value={'path':sys.executable,'sha256':'a'*64}), \
             patch.object(sync.platform,'system',return_value='NoNativeMetadata'), \
             patch.object(sync.subprocess,'check_output',return_value='fixed-control-head\n'), \
             patch.object(sync.subprocess,'run',side_effect=AssertionError('tool dispatch')), \
             patch.object(sync,'save',side_effect=fake_save):
            sync.main()
        self.assertEqual(len(captured),2)
        self.assertTrue(all(x['parameters']['endpoint_cpu_budget_ceiling']==8 for x in captured))
        self.assertNotIn('preparation_complete',captured[0])
        self.assertTrue(captured[1]['preparation_complete'])
        params=captured[0]['parameters']
        self.assertEqual(params['workers'],[1,2,4,8,'auto'])
        self.assertEqual(params['maximum_declared_cpu_credit_sum'],18)
        self.assertEqual(params['endpoint_cpu_permit_upper_bounds'],[
            {'selection':x,'upper_bound':n} for x,n in zip([1,2,4,8,'auto'],[1,2,4,8,8])])
        self.assertFalse(captured[0]['complete'])
        self.assertFalse(Path('NEVER-CREATED-AUTO-BENCH.json').exists())

if __name__=='__main__':unittest.main()
