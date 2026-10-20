"""Original disposable Git fixtures; no build, Photo input or resource pools."""
import subprocess
import tempfile
from pathlib import Path
import unittest
from build_source_snapshot import populate


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        (self.repo / 'unit.ml').write_text('let original = 1\n')
        self.git('add', 'unit.ml')
        self.git('-c', 'user.name=Original Fixture', '-c', 'user.email=fixture@invalid',
                 'commit', '-qm', 'original fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'unit.ml').write_text('let current = 2\n')
        (self.repo / 'untracked.ml').write_text('let extra = 3\n')

    def git(self, *argv):
        return subprocess.check_output(['git', *argv], cwd=self.repo, text=True)

    def destination(self, name):
        p = self.base / name
        p.mkdir()
        return p

    def test_exact_commit_excludes_current_and_untracked_edits(self):
        out = self.destination('exact')
        paths, origin = populate(self.repo, out, self.commit)
        self.assertEqual(paths, b'unit.ml\0')
        self.assertEqual((out / 'unit.ml').read_text(), 'let original = 1\n')
        self.assertFalse((out / 'untracked.ml').exists())
        self.assertEqual(origin['commit'], self.commit)
        self.assertEqual(origin['kind'], 'git-commit')
        self.assertTrue((out / 'SOURCE.tar').is_file())
        self.assertEqual((self.repo / 'unit.ml').read_text(), 'let current = 2\n')

    def test_default_keeps_current_snapshot_behavior(self):
        out = self.destination('current')
        paths, origin = populate(self.repo, out)
        self.assertEqual(set(paths.split(b'\0')) - {b''}, {b'unit.ml', b'untracked.ml'})
        self.assertEqual((out / 'unit.ml').read_text(), 'let current = 2\n')
        self.assertEqual((out / 'untracked.ml').read_text(), 'let extra = 3\n')
        self.assertEqual(origin, {'kind': 'working-tree'})

    def test_reserved_archive_collision_refuses_before_writing(self):
        (self.repo / 'SOURCE.tar').write_bytes(b'original fixture')
        self.git('add', 'SOURCE.tar')
        self.git('-c', 'user.name=Original Fixture', '-c', 'user.email=fixture@invalid',
                 'commit', '-qm', 'reserved fixture')
        commit=self.git('rev-parse','HEAD').strip()
        out=self.destination('reserved')
        with self.assertRaises(ValueError):populate(self.repo,out,commit)
        self.assertEqual(list(out.iterdir()),[])

    def test_refnames_options_and_unknown_commits_refuse(self):
        for i, revision in enumerate(('HEAD', '--all', self.commit[:8], self.commit.upper(), '0' * 40)):
            with self.subTest(revision=revision):
                out = self.destination('refuse' + str(i))
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    populate(self.repo, out, revision)
                self.assertEqual(list(out.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
