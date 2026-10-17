import copy
import unittest
from all_scanned_sdk_parent import audit_complete
from all_scanned_sdk_plan import plan, BUILD
from all_scanned_sdk_audit_test import frame, SHA, SIZE
from invocation_journal import audit_attempted, audit_validation_attempted


class Parent(unittest.TestCase):
    def fixture(self):
        contract = dict(workspace='/private/tmp/u-scan-test',
                        binaries={label: dict(label=label, path='/inert/' + label, sha256='b' * 64)
                                  for label in ('stock', 'ox')},
                        tool=dict(path='/inert/sdk', sha256='c' * 64, build_id=BUILD, threads=1),
                        source=dict(sha256=SHA, bytes=SIZE))
        result = dict(schema='unison-all-scanned-sdk-worker/1', complete=True,
                      phase='FINISHED', invocations=[])
        proxies = []
        for index in range(4):
            label, phase = ('stock', 'ox')[index // 2], ('baseline', 'validate')[index % 2]
            directory = contract['workspace'] + '/' + label
            command = plan(contract['binaries'][label], contract['tool'], directory)[phase]
            argv = command['argv']
            def owner(pid):
                return dict(pid=pid, returncode=0, reaped=True,
                            group_cleanup_before_leader_reap=True,
                            other_group_members_absent_before_reap=True)
            raw = dict(schema='unison-loopback-protocol-count/1', server_pid=100 + index,
                       server_returncode=0, server_cleanup=owner(100 + index),
                       server_command=[argv[0], '-server', *command['server_flags']],
                       input_pump_joined=True, pump_errors=[], fault=None)
            log = '' if phase == 'baseline' else frame('client', 200 + index * 2) + frame('server', 201 + index * 2)
            out = dict(command=argv, returncode=0, timed_out=False, fault=None,
                       capture_truncated=False, supervisor_capture_truncated=False,
                       client_cleanup=owner(10 + index), supervisor_cleanup=owner(20 + index),
                       proxy=raw, stdout='Nothing to do: replicas have not changed since last sync.\n' + log,
                       stderr='', supervisor_output='')
            result['invocations'].append(dict(index=index, state='OUTCOME', command=argv,
                identity=dict(label=label, mode='validation', workers=3, directory=directory, stage=phase),
                outcome=out))
            proxies.append(copy.deepcopy(raw))
        return result, contract, proxies

    def test_complete_join_is_narrow_observation_not_fd_or_path_authority(self):
        result, contract, proxies = self.fixture()
        proof = audit_complete(result, contract, raw_proxy_receipts=proxies)
        self.assertEqual(proof['functional_status'], 'PASSED')
        self.assertEqual(proof['helper_calls'], 4)
        self.assertFalse(proof['resource_release_authorized'])
        self.assertFalse(proof['candidate_path_isolation_proved'])

    def test_mutated_order_commands_raw_proxy_and_lifetimes_reject(self):
        mutations = [
            lambda r, p: r['invocations'].reverse(),
            lambda r, p: r['invocations'][0].update(state='INTENT'),
            lambda r, p: r['invocations'][1]['identity'].update(stage='baseline'),
            lambda r, p: r['invocations'][0]['command'].append('-force'),
            lambda r, p: p[0].update(server_pid=999),
            lambda r, p: r['invocations'][0]['outcome']['client_cleanup'].update(reaped=False),
            lambda r, p: r['invocations'][0]['outcome']['proxy']['server_cleanup'].update(other_group_members_absent_before_reap=False),
            lambda r, p: r['invocations'][0]['outcome'].update(supervisor_capture_truncated=True),
        ]
        for mutate in mutations:
            r, contract, p = self.fixture(); mutate(r, p)
            with self.assertRaises(ValueError): audit_complete(r, contract, raw_proxy_receipts=p)

    def test_matching_mutated_raw_frame_cannot_hide_server_policy_or_failure(self):
        for mutate in [lambda out: out['proxy']['server_command'].append('-force'),
                       lambda out: out['proxy'].update(pump_errors=['failure']),
                       lambda out: out.update(timed_out=True),
                       lambda out: out.update(stdout='0 items transferred\n'),
                       lambda out: out.update(stdout=out['stdout'].replace('Nothing to do:', 'Not done:'))]:
            r, contract, _ = self.fixture(); mutate(r['invocations'][1]['outcome'])
            proxies = [copy.deepcopy(e['outcome']['proxy']) for e in r['invocations']]
            with self.assertRaises(ValueError): audit_complete(r, contract, raw_proxy_receipts=proxies)

    def test_partial_or_helperless_validation_never_passes(self):
        for kind in ('partial', 'missing', 'duplicate-status'):
            r, contract, proxies = self.fixture()
            if kind == 'partial': r.update(complete=False, failure='original failure')
            elif kind == 'missing': r['invocations'][1]['outcome']['stdout'] = 'Nothing to do: replicas have not changed since last sync.\n'
            else: r['invocations'][1]['outcome']['stdout'] += 'Nothing to do: replicas have not changed since last sync.\n'
            with self.assertRaises(ValueError): audit_complete(r, contract, raw_proxy_receipts=proxies)

    def test_validation_profile_does_not_relax_original_sync_journal(self):
        r, _, _ = self.fixture()
        self.assertEqual(audit_validation_attempted(r)['attempted_cli_invocations'], 4)
        with self.assertRaises(ValueError): audit_attempted(r)
        r['invocations'][0]['identity']['mode'] = 'semantic'
        with self.assertRaises(ValueError): audit_validation_attempted(r)


if __name__ == '__main__': unittest.main()
