"""Mock-only IO dispatcher admissions; no IO namespace or child access."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
import shared_dispatch as d
import shared_io_pool as pool


class Controls(unittest.TestCase):
    def test_framing_input_never_has_cpu_only_route(self):
        argv = ['/python', str(d.ROOT/'tools/private-dng-framing/admitted.py')]
        with patch.object(d.Pool, 'read') as read:
            with self.assertRaises(ValueError):
                d.run('private-dng-framing-input', argv, Path('/none'), 8)
            read.assert_not_called()

    def test_property_matrix_has_no_cpu_only_route(self):
        argv=['/python',str(d.ROOT/'bench/sync/run.py'),'--property-removal-controls']
        with patch.object(d.Pool,'read') as read:
            with self.assertRaises(ValueError):d.run('sync-functional',argv,Path('/none'),8)
            read.assert_not_called()

    def test_layout_matrix_has_no_cpu_only_route(self):
        argv=['/python',str(d.ROOT/'bench/sync/run.py'),'--layout-only-controls']
        with patch.object(d.Pool,'read') as read:
            with self.assertRaises(ValueError):d.run('sync-functional',argv,Path('/none'),8)
            read.assert_not_called()

    def test_framing_input_exact_source_superset(self):
        argv = ['/python', str(d.ROOT/'tools/private-dng-framing/admitted.py'), '--plan', '/fixed']
        base = {Path(d.__file__), d.ROOT/'tests/manual.py', d.ROOT/'tests/shared_io_pool.py',
                d.ROOT/'tests/shared_cpu_pool.py', d.ROOT/'tests/shared_process_owner.py',
                d.ROOT/'bench/sync/ownership.py', Path(argv[1])}
        extra = {d.ROOT/p for p in ('src/dngPrivateData.ml', 'src/dngPrivateData.mli',
                 'tools/private-dng-framing/inspect.ml', 'tools/private-dng-framing/controls.py')}
        value = {'state':'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB', 'target':'private-dng-framing-input',
                 'command':argv, 'workspace':'/none', 'cpu_credits':8,
                 'io_manifest_sha256':pool.CANONICAL_SHA256, 'start_deadline_unix':200,
                 'execution_source_sha256': {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in base|extra}}
        request = {'path':'/never-opened', 'sha256':'0'*64}
        with patch.object(pool, 'read_manifest', return_value=value), \
             patch.object(pool.GlobalPool, 'read', return_value='metadata-only') as read, \
             patch.object(d.time, 'time', return_value=100):
            self.assertEqual(d.checked_io_request(request, 'private-dng-framing-input', argv,
                             Path('/none'), 8), ('metadata-only',200))
            for path in extra:
                saved = value['execution_source_sha256'].pop(str(path));read.reset_mock()
                with self.assertRaises(ValueError):
                    d.checked_io_request(request, 'private-dng-framing-input', argv, Path('/none'), 8)
                read.assert_not_called();value['execution_source_sha256'][str(path)] = saved

    def test_sync_requires_all_transport_sources(self):
        argv = ['/python', str(d.ROOT/'bench/sync/run.py'), '--shared-qualification',
                '--expected-binary-sha256','stock='+'a'*64,'--expected-binary-sha256','ox='+'b'*64,
                '--expected-compiler-sha256','stock='+'c'*64,'--expected-compiler-sha256','ox='+'d'*64]
        paths = {Path(d.__file__), d.ROOT/'tests/manual.py', d.ROOT/'tests/shared_io_pool.py',
                 d.ROOT/'tests/shared_cpu_pool.py', d.ROOT/'tests/shared_process_owner.py',
                 d.ROOT/'bench/sync/ownership.py', Path(argv[1])}
        paths.update((d.ROOT/'bench/sync').glob('*.py'))
        value={'state':'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB','target':'sync-functional',
               'command':argv,'workspace':'/none','cpu_credits':8,
               'io_manifest_sha256':pool.CANONICAL_SHA256,'start_deadline_unix':200,
               'execution_source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
        with patch.object(pool,'read_manifest',return_value=value),patch.object(pool.GlobalPool,'read',return_value='pool') as read,patch.object(d.time,'time',return_value=100):
            self.assertEqual(d.checked_io_request({'path':'/mock','sha256':'0'*64},'sync-functional',argv,Path('/none'),8),('pool',200))
            valid = argv.copy()
            for flag in ('--expected-binary-sha256','--expected-compiler-sha256'):
                at=argv.index(flag); saved=argv[at+1];argv[at+1]='missing-or-bad'
                read.reset_mock()
                with self.assertRaises(ValueError):d.checked_io_request({'path':'/mock','sha256':'0'*64},'sync-functional',argv,Path('/none'),8)
                read.assert_not_called();argv[at+1]=saved
            self.assertEqual(argv,valid)
            for name in ('artifact_pins.py','phase_stats.py'):
                key=str(d.ROOT/'bench/sync'/name)
                saved=value['execution_source_sha256'].pop(key)
                read.reset_mock()
                with self.assertRaises(ValueError):d.checked_io_request({'path':'/mock','sha256':'0'*64},'sync-functional',argv,Path('/none'),8)
                read.assert_not_called()
                value['execution_source_sha256'][key]=saved

    def test_no_io_admission_on_default_existing_path(self):
        # Default API stays CPU-only, never silently enables IO.
        import inspect
        self.assertIsNone(inspect.signature(d.run).parameters['io_admission'].default)

    def test_forbidden_target_before_manifest_read(self):
        with patch.object(pool, 'read_manifest', side_effect=AssertionError('IO metadata touched')):
            with self.assertRaises(ValueError):
                d.checked_io_request({'path': '/none', 'sha256': '0'*64},
                                     'stock-build', [], Path('/none'), 8)

    def test_manual_mode_requires_complete_admission_and_supported_target(self):
        import manual
        for env in ({'SHARED_IO_ADMISSION':'/none'},
                    {'SHARED_IO_ADMISSION_SHA256':'0'*64},
                    {'SHARED_IO_ADMISSION':'/none','SHARED_IO_ADMISSION_SHA256':'0'*64}):
            with self.assertRaises(ValueError):
                manual.command('private-dng-local-clone',Path('/none'),env)
        env={'SHARED_CPU_CREDITS':'8','SHARED_IO_ADMISSION':'/none',
             'SHARED_IO_ADMISSION_SHA256':'0'*64}
        with self.assertRaises(ValueError):
            manual.command('sync-functional',Path('/none'),env)
        self.assertEqual(manual.command('private-dng-local-clone',Path('/none'),env)[-1],
                         str(d.ROOT/'tests/private_dng_local_clone/run.py'))

    def test_command_workspace_deadline_and_source_refusals(self):
        argv = ['/python', str(Path(d.__file__))]
        paths = {Path(d.__file__), d.ROOT/'tests/manual.py', d.ROOT/'tests/shared_io_pool.py',
                 d.ROOT/'tests/shared_cpu_pool.py', d.ROOT/'tests/shared_process_owner.py',
                 d.ROOT/'bench/sync/ownership.py', d.ROOT/'tests/inspector_io_contract.py', Path(argv[1])}
        value = {'state':'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB', 'target':'inspect-file',
                 'command':argv, 'workspace':'/none', 'cpu_credits':8,
                 'io_manifest_sha256':pool.CANONICAL_SHA256, 'start_deadline_unix':200,
                 'execution_source_sha256': {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in paths}}
        request = {'path':'/never-opened','sha256':'0'*64}
        with patch.object(pool, 'read_manifest', return_value=value), \
             patch('inspector_io_contract.check', return_value=set()), \
             patch.object(pool.GlobalPool, 'read', return_value='metadata-only') as read, \
             patch.object(d.time, 'time', return_value=100):
            # This is the common envelope boundary, not a fabricated real
            # inspector/build/input qualification. Its stricter contract has
            # separate original controls and is deliberately stubbed here.
            self.assertEqual(d.checked_io_request(request, 'inspect-file', argv, Path('/none'), 8),
                             ('metadata-only',200))
            for key, bad in [('state','wrong'),('command',[]),('workspace','/wrong'),
                             ('cpu_credits',7),('start_deadline_unix',99),
                             ('execution_source_sha256',{})]:
                original=value[key];value[key]=bad;read.reset_mock()
                with self.assertRaises(ValueError):
                    d.checked_io_request(request,'inspect-file',argv,Path('/none'),8)
                read.assert_not_called();value[key]=original


if __name__ == '__main__':
    unittest.main()
