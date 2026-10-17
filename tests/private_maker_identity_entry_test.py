"""Inert plan/result/dispatcher controls, no camera IO or canonical acquisition."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import private_maker_identity_entry as entry
import shared_dispatch
from private_maker_identity import interpret
from private_maker_identity_test import shape


def plan():
    return dict(schema='unison-private-maker-model-plan/1', target=entry.TARGET,
                workspace='/private/tmp/unison-private-maker-model-' + 'a'*32,
                source=dict(path=entry.SOURCE, identity=dict(entry.IDENTITY)),
                saved_result=dict(path=entry.SAVED_RESULT, sha256='b'*64),
                worker_seconds=10, cpu_credits=8, io_mode='EX_GLOBAL',
                max_requested_read_bytes=9, semantic_eligibility=False,
                sdk_validation=False, source_hash_requested=False)


def result():
    value = interpret(b'MODEL123\0')
    value.update(read_range=dict(offset=11440, requested=9, received=9),
                 source_epoch_unchanged=True, full_input_hash_computed=False,
                 fd_closure_proved_by_return=True)
    return dict(schema='unison-private-maker-model-worker/1', complete=True,
                diagnostic=value, failure=None, parent_pid=100, worker_pid=101,
                canonical_metadata_bound=True, external_children_started=0)


class Boundary(unittest.TestCase):
    def audit(self, value):
        return entry.audit_worker(value, plan(), parent_pid=100, worker_pid=101)

    def test_exact_plan(self):
        self.assertEqual(entry.check(plan())['max_requested_read_bytes'], 9)
        for field, value in (('worker_seconds', True), ('cpu_credits', 18),
                             ('max_requested_read_bytes', 10), ('semantic_eligibility', True),
                             ('workspace', '/private/tmp/reused')):
            bad = plan(); bad[field] = value
            with self.assertRaises(ValueError): entry.check(bad)
        bad = plan(); bad['source']['identity']['st_nlink'] = True
        with self.assertRaises(ValueError): entry.check(bad)

    def test_metadata_bind_saved_shape_without_payload_open(self):
        saved = dict(schema='unison-private-maker-worker/1', complete=True,
                     diagnostic=dict(outcome='CANDIDATE_SHAPE', shape=shape()))
        with patch.object(entry, 'document', side_effect=[plan(), saved]) as document:
            self.assertEqual(entry.checked_plan('/inert', 'c'*64), plan())
            self.assertEqual(document.call_args_list[1].args, (entry.SAVED_RESULT, 'b'*64))
        saved['complete'] = False
        with patch.object(entry, 'document', side_effect=[plan(), saved]):
            with self.assertRaises(ValueError): entry.checked_plan('/inert', 'c'*64)

    def test_independent_success_and_known_failure(self):
        proof = self.audit(result())
        self.assertTrue(proof['worker_complete'])
        self.assertFalse(proof['resource_release_authorized'])
        value = result(); value.update(complete=False, diagnostic=None, failure='read error')
        self.assertFalse(self.audit(value)['worker_complete'])

    def test_contradictory_scope_and_incorrect_read_bound_refuse(self):
        for key, changed in [('semantic_eligibility', True), ('fd_closure_proved_by_return', False),
                             ('candidate_text', 'RELABELED'), ('raw_hex', '0'*19)]:
            value = result(); value['diagnostic'][key] = changed
            with self.assertRaises(ValueError): self.audit(value)
        value = result(); value['diagnostic']['read_range']['requested'] = 10
        with self.assertRaises(ValueError): self.audit(value)
        value = result(); value['diagnostic']['read_range']['received'] = True
        with self.assertRaises(ValueError): self.audit(value)

    def test_parent_worker_and_no_children_binding(self):
        for key, changed in [('parent_pid', 102), ('worker_pid', 100),
                             ('external_children_started', True), ('canonical_metadata_bound', False)]:
            value = result(); value[key] = changed
            with self.assertRaises(ValueError): self.audit(value)

    def test_failed_result_cannot_hide_observation_or_omit_error(self):
        for diagnostic, failure in ((result()['diagnostic'], 'error'), (None, ''), (None, None)):
            value = result(); value.update(complete=False, diagnostic=diagnostic, failure=failure)
            with self.assertRaises(ValueError): self.audit(value)

    def test_cpu_only_route_refused_before_pool_or_child(self):
        command = entry.child_argv('/inert', 'c'*64, plan()['workspace'])
        with patch.object(shared_dispatch.Pool, 'read', side_effect=AssertionError('pool opened')):
            with self.assertRaisesRegex(ValueError, 'CPU-only'):
                shared_dispatch.run(entry.TARGET, command, Path(plan()['workspace']), 8)

    def test_exact_command_and_sources(self):
        command = entry.child_argv('/inert', 'c'*64, plan()['workspace'])
        self.assertEqual(len(command), 9)
        self.assertEqual(command[2:], ['--worker', '--plan', '/inert', '--plan-sha256',
                                      'c'*64, '--workspace', plan()['workspace']])
        self.assertTrue(all(p.is_file() and p.is_absolute() for p in entry.sources()))
        self.assertIn(Path(entry.__file__).resolve(), entry.sources())


if __name__ == '__main__': unittest.main()
