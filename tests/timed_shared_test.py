"""Fixed fabricated receipts only; no subprocess, payload or canonical IO."""
import copy
import itertools
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import manual
import shared_dispatch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bench/sync'))
import phase_stats
import timed_shared


def fixture():
    result = dict(schema='unison-synthetic-sync/0', complete=True,
                  purpose='warm-cache performance', parameters=copy.deepcopy(timed_shared.PARAMETERS),
                  binaries={'stock': {}, 'ox': {}}, samples=[], invocations=[])
    phases = phase_stats.parse('\n'.join([
        '[semantic-timings] Semantic worker job 1 stage=' + stage +
        ' calls=1 inclusive-seconds=0.000000000.' for stage in ('hash','parse','verify','write')
    ] + ['[semantic-timings] Semantic bound publication native-inclusive-seconds=0.000000000.']))
    for label, mode, workers in itertools.product(('stock','ox'), timed_shared.PARAMETERS['modes'], (1,2,3)):
        for phase, count in (('warmup',1), ('measured',5)):
            for repetition in range(1,count+1):
                row = dict(label=label,mode=mode,workers=workers,phase=phase,repetition=repetition,
                           exact_result_and_unchanged_basis=True,noop_preserved_receiver_inode=True,
                           staging_cleaned=True,private_fixture_removed=True,
                           counters={'semantic_phase_observations':copy.deepcopy(phases)})
                directory = '/fabricated/' + str(len(result['samples']))
                for stage, field in (('seed','seed_sync'),('update','update_sync'),('noop','noop_sync')):
                    owner = dict(pid=100,returncode=0,reaped=True,cancel_reason=None,
                                 group_cleanup_before_leader_reap=True,other_group_members_absent_before_reap=True)
                    run = dict(command=['/fabricated/unison',directory], returncode=0,timed_out=False,
                               capture_truncated=False,supervisor_capture_truncated=False,
                               client_cleanup=copy.deepcopy(owner),supervisor_cleanup=copy.deepcopy(owner),
                               proxy=dict(schema='unison-loopback-protocol-count/1',server_cleanup=copy.deepcopy(owner),
                                          server_pid=100,server_returncode=0,server_command=['/fabricated/unison'],
                                          fault=None,pump_errors=[],input_pump_joined=True))
                    row[field] = run
                    result['invocations'].append(dict(index=len(result['invocations']),state='OUTCOME',
                        command=copy.deepcopy(run['command']),outcome=copy.deepcopy(run),
                        identity=dict(label=label,mode=mode,workers=workers,directory=directory,stage=stage)))
                result['samples'].append(row)
    return result


class Timed(unittest.TestCase):
    def command(self):
        environment = dict(SHARED_CPU_CREDITS='8', SHARED_IO_ADMISSION='/fake/admission',
                           SHARED_IO_ADMISSION_SHA256='a'*64, STOCK_RECEIPT='stock', OX_RECEIPT='ox')
        receipt = dict(binary='/fake/unison', compiler='/fake/ocamlopt',
                       binary_sha256='b'*64, compiler_sha256='c'*64)
        with patch.object(manual, 'checked_build', return_value=receipt):
            argv = manual.command('sync-timed', Path('/fake/output'), environment)
        return argv, environment

    def test_exact_entrypoint_and_refusals_before_pool_access(self):
        argv, env = self.command()
        timed_shared.check_argv(argv, interpreter=sys.executable,
            script=str(manual.ROOT/'bench/sync/run.py'), output=Path('/fake/output/RESULT.json'))
        for extra in (['--workers','18'], ['--files=100'], ['--qualification'], ['--reference','x=/fake']):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                timed_shared.check_argv(argv+extra, interpreter=sys.executable,
                    script=str(manual.ROOT/'bench/sync/run.py'), output=Path('/fake/output/RESULT.json'))
        for key in ('SHARED_IO_ADMISSION', 'SHARED_CPU_CREDITS'):
            broken=dict(env);del broken[key]
            with self.assertRaises(ValueError):manual.command('sync-timed',Path('/fake/output'),broken)
        with patch.object(shared_dispatch.Pool, 'read', side_effect=AssertionError('pool touched')):
            with self.assertRaises(ValueError):shared_dispatch.run('sync-timed',argv,Path('/fake/output'),8)
        self.assertEqual(manual.shared_resource_plan('sync-timed',env)['declared_peak_credits'],8)

    def test_complete_matrix_and_no_input_mutation(self):
        value=fixture(); before=copy.deepcopy(value)
        proof=timed_shared.audit(value)
        self.assertEqual((proof['rows'],proof['cli_invocations']), (108,324))
        self.assertTrue(proof['phase_measurements_qualified'])
        self.assertEqual(value,before)

    def test_missing_measurement_does_not_invent_lifetime_uncertainty(self):
        value=fixture(); row=next(r for r in value['samples'] if r['mode']=='semantic')
        row['counters']['semantic_phase_observations']=None
        proof=timed_shared.audit(value)
        self.assertFalse(proof['phase_measurements_qualified'])
        self.assertTrue(proof['all_client_server_supervisor_settled'])

    def test_unknown_group_and_intent_refuse(self):
        for mutation in ('group','intent','row','missing','typed'):
            value=fixture()
            if mutation=='group':value['invocations'][0]['outcome']['client_cleanup']['other_group_members_absent_before_reap']=False
            if mutation=='intent':value['invocations'][0]['state']='INTENT'
            if mutation=='row':value['samples'][0]['seed_sync']['command']=['different']
            if mutation=='missing':value['samples'].pop()
            if mutation=='typed':value['parameters']['warmups']=True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):timed_shared.audit(value)

    def test_failed_prefix_is_separate_from_full_matrix(self):
        value=fixture(); value['complete']=False; value['invocations']=value['invocations'][:1]
        self.assertEqual(timed_shared.audit_attempted(value)['attempted_cli_invocations'],1)
        with self.assertRaises(ValueError):timed_shared.audit(value)

if __name__=='__main__':unittest.main()
