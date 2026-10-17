"""Real tiny disposable preparation/hash fences with modeled CLI/SDK outcomes."""
import copy
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import all_scanned_sdk_worker as worker
import all_scanned_sdk_prepare as prep
import all_scanned_sdk_prepare_test as preparation_controls
from all_scanned_sdk_plan import plan, BUILD


class ComposedVerification(unittest.TestCase):
    def test_worker_really_verifies_all_disposable_pairs_at_every_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'retained.dng'
            data = b'original tiny all-scanned integration fixture'
            source.write_bytes(data); source.chmod(0o400)
            expected = prep.stamp(source.lstat()); digest = hashlib.sha256(data).hexdigest()
            workspace = root / 'work'; workspace.mkdir(mode=0o700)
            contract = dict(workspace=str(workspace), source=dict(bytes=len(data), sha256=digest),
                tool=dict(path='/inert/sdk', sha256='b' * 64, build_id=BUILD, threads=1),
                binaries={label: dict(label=label, path='/inert/' + label, sha256='a' * 64)
                          for label in ('stock', 'ox')}, transport_source_sha256={})
            raw, calls = {}, []
            def frame(endpoint, pid):
                body = ('UNISON-DNG-VALIDATION 1\ncandidate-sha256 ' + digest +
                    '\ncandidate-size ' + str(len(data)) + '\ndriver-build ' + BUILD +
                    '\nstructure valid\ndecode success\nraw-digest missing\nerrors 0\nwarnings 0\nEND\n').encode()
                prefix = '[server: validation-' if endpoint == 'server' else '[validation-'
                return (prefix + 'process] Helper result v0 pid=' + str(pid) +
                    ' status=exit:0 outcome=completed candidate-sha256=' + digest +
                    ' candidate-bytes=' + str(len(data)) +
                    ' capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex=' +
                    body.hex() + ' stderr-hex=\n' + prefix + 'group] Retained group v0 pid=' +
                    str(pid) + ' candidate-sha256=' + digest + ' other-members=0\n')
            class Invoke:
                def __init__(self, directory, *, binary, phase, journal, **kwargs):
                    self.d, self.binary, self.phase, self.journal = Path(directory), binary, phase, journal
                def __call__(self):
                    index = len(calls)
                    proposal = plan(self.binary, contract['tool'], self.d)[self.phase]
                    argv = proposal['argv']
                    def owner(pid):
                        return dict(pid=pid, returncode=0, reaped=True,
                                    group_cleanup_before_leader_reap=True,
                                    other_group_members_absent_before_reap=True)
                    proxy = dict(schema='unison-loopback-protocol-count/1', server_pid=100 + index,
                        server_returncode=0, server_cleanup=owner(100 + index),
                        server_command=[argv[0], '-server', *proposal['server_flags']],
                        input_pump_joined=True, pump_errors=[], fault=None)
                    log = '' if self.phase == 'baseline' else frame('client', 200 + 2 * index) + frame('server', 201 + 2 * index)
                    out = dict(command=argv, returncode=0, timed_out=False, fault=None,
                        client_cleanup=owner(10 + index), supervisor_cleanup=owner(20 + index),
                        capture_truncated=False, supervisor_capture_truncated=False,
                        stdout='Nothing to do: replicas have not changed since last sync.\n' + log,
                        stderr='', supervisor_output='', proxy=proxy)
                    self.journal.begin(dict(label=self.binary['label'], mode='validation', workers=3,
                        directory=str(self.d), stage=self.phase), argv)
                    calls.append(out); raw[str(self.d / (self.phase + '-proxy.json'))] = copy.deepcopy(proxy)
                    self.journal.finish(out); return out
            def prepare(directory, label):
                return prep.prepare(source, expected, digest, directory,
                    clone=preparation_controls.Preparation.fake_clone)
            with patch.object(worker, 'prepare_scripts', return_value={}), patch.object(worker, 'Invoker', Invoke):
                result = worker.execute(contract, workspace, time.monotonic() + 600,
                    prepare_sources=prepare, read_proxy=lambda p: raw[str(p)],
                    persist=lambda _: None, check_sources=lambda: None)
            self.assertTrue(result['complete']); self.assertEqual(len(calls), 4)
            checks = []
            for row in result['cases']:
                checks.append(row['initial_root_verification'])
                checks.extend(call['root_verification'] for call in row['calls'])
            self.assertEqual(len(checks), 6)
            self.assertTrue(all(c['payload_read_bytes'] == 2 * len(data) for c in checks))
            self.assertTrue(all(c['schema'] == 'unison-all-scanned-sdk-root-verification/1' for c in checks))
            self.assertEqual(prep.stamp(source.lstat()), expected)
            self.assertFalse(result['parent_audit']['resource_release_authorized'])


if __name__ == '__main__': unittest.main()
