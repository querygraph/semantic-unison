"""Original phase-composition controls; file IO/sync replaced by explicit seams."""
from contextlib import ExitStack
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from corpus_workloads import plan
from batch_sample import sample


class SampleTests(unittest.TestCase):
    def exercise(self, corpus, invoke, *, different_noop=False):
        events = []; created = []; edited = []; verified = []
        def create(path, size, packet, index):
            created.append(index)
            return dict(before_sha256=hashlib.sha256(f'before{index}'.encode()).hexdigest(), size_bytes=size)
        def edit(path, info, kind):
            edited.append(kind)
            return hashlib.sha256((info['before_sha256']+'after').encode()).hexdigest()
        def verify(root, rows, *, phase):
            verified.append((str(root), phase, len(rows)))
            # Two receiver target passes: update then no-op.
            n = sum('/right' in p for p, _, _ in verified)
            return [dict(observation='changed' if different_noop and n == 2 else 'same')]
        with tempfile.TemporaryDirectory(prefix='unison-batch-phase-control-') as temp, ExitStack() as stack:
            left = Path(temp)/'left'; right = Path(temp)/'right'
            left.mkdir(mode=0o700); right.mkdir(mode=0o700)
            stack.enter_context(patch('batch_sample.create_corpus', side_effect=create))
            stack.enter_context(patch('batch_sample.edit', side_effect=edit))
            stack.enter_context(patch('batch_sample.verify_expected'))
            stack.enter_context(patch('batch_sample.verify', side_effect=verify))
            result = sample(corpus, left, right,
                            invoke=lambda stage: invoke(stage, created, edited), record=events.append)
        return result, events, created, edited

    def test_new_files_are_created_only_after_empty_seed_sync(self):
        stages = []
        def invoke(stage, created, edited):
            stages.append(stage)
            if stage == 'seed': self.assertEqual(created, [])
            else: self.assertEqual(len(created), 1024)
            self.assertEqual(edited, [])
        result, events, _, _ = self.exercise(plan('new-files', count=1024), invoke)
        self.assertEqual(stages, ['seed', 'update', 'noop'])
        self.assertFalse(result['resource_release_authorized'])
        rows = next(e['files'] for e in events if e['stage'] == 'update-inventory')
        self.assertTrue(all(r['before_sha256'] is None for r in rows))

    def test_seed_failure_does_not_edit_or_start_more_calls(self):
        stages = []
        def invoke(stage, created, edited):
            stages.append(stage); self.assertEqual(len(created), 1024); self.assertEqual(edited, [])
            raise RuntimeError('failed seed')
        with self.assertRaisesRegex(RuntimeError, 'failed seed'):
            self.exercise(plan('many-small', count=1024), invoke)
        self.assertEqual(stages, ['seed'])

    def test_noop_identity_change_refuses_completion(self):
        with self.assertRaisesRegex(ValueError, 'no-op changed'):
            self.exercise(plan('many-small', count=1024), lambda *args: None, different_noop=True)

    def test_shrunk_corpus_refuses_before_creation(self):
        corpus = plan('many-small', count=1024)
        with self.assertRaises(ValueError):
            self.exercise(replace(corpus, files=corpus.files[:-1]), lambda *args: None)


if __name__ == '__main__': unittest.main()
