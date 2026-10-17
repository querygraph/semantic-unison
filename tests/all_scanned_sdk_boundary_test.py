import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import all_scanned_sdk_boundary as boundary
from shared_cpu_pool import UnresolvedOwnership


class Boundary(unittest.TestCase):
    def fixture(self):
        root = Path(boundary.__file__).resolve().parents[1]
        transport = {name: 'a' * 64 for name in ('proxy.py', 'measure.py', 'launcher.py', 'ownership.py')}
        pins = {str(root / 'bench/sync' / name): digest for name, digest in transport.items()}
        identity = dict(st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o400, st_size=100,
                        st_mtime_ns=3, st_ctime_ns=4, st_nlink=1, st_uid=os.getuid())
        packet = dict(schema='unison-all-scanned-sdk-plan/1', workspace='/private/tmp/u-asv-inert',
            parameters=copy.deepcopy(boundary.PARAMETERS), execution_source_sha256=pins,
            interpreter=dict(path=boundary.PYTHON, sha256=boundary.PYTHON_SHA),
            source=dict(path='/private/tmp/inert/source.dng', identity=identity, sha256='b' * 64, bytes=100),
            tool=dict(path='/inert/sdk', sha256='c' * 64, build_id=boundary.BUILD, threads=1,
                      manifest='/inert/sdk-manifest', manifest_sha256='d' * 64),
            binaries={label: dict(label=label, path='/inert/' + label, sha256='e' * 64)
                      for label in ('stock', 'ox')},
            builds={label: dict(path='/inert/' + label + '-receipt', sha256='f' * 64)
                    for label in ('stock', 'ox')}, transport_source_sha256=transport)
        manifest = dict(executable='/inert/sdk', executable_sha256='c' * 64, build_id=boundary.BUILD)
        builds = {label: dict(complete=True, build_exit=0, binary='/inert/' + label,
                             binary_sha256='e' * 64, compiler='/Users/alexy/.opam/' +
                             ('default' if label == 'stock' else '5.2.0+ox') + '/bin/ocamlopt')
                  for label in ('stock', 'ox')}
        return packet, pins, copy.deepcopy(identity), manifest, builds

    def validate(self, fixture):
        p, pins, identity, manifest, builds = fixture
        return boundary.validate_packet(p, execution_pins=pins, observed_source=identity,
                                        tool_manifest=manifest, build_receipts=builds)

    def test_exact_pure_metadata_contract(self):
        f = self.fixture(); self.assertIs(self.validate(f), f[0])

    def test_scope_epoch_tool_build_and_execution_mutations_refuse(self):
        mutations = [lambda f: f[0]['parameters'].update(cpu_credits=True),
            lambda f: f[0]['parameters'].update(sdk_calls=8),
            lambda f: f[2].update(st_ino=99),
            lambda f: f[0]['source'].update(path='/Users/inert/original.dng'),
            lambda f: f[0]['tool'].update(threads=2),
            lambda f: f[3].update(executable_sha256='0' * 64),
            lambda f: f[4]['stock'].update(compiler=f[4]['ox']['compiler']),
            lambda f: f[4]['stock'].update(build_exit=False),
            lambda f: f[0].update(extra='unreviewed'),
            lambda f: f[0]['transport_source_sha256'].update(proxy='a' * 64),
            lambda f: f[0]['transport_source_sha256'].update({'proxy.py': None})]
        for mutate in mutations:
            fixture = self.fixture(); mutate(fixture)
            with self.assertRaises(ValueError): self.validate(fixture)

    def test_bounded_owned_document_and_duplicate_key_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'plan.json'; raw = b'{"original":true}\n'; path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            self.assertEqual(boundary.read_document(path, digest), dict(original=True))
            with self.assertRaises(ValueError): boundary.read_document(path, digest, limit=1)
            raw = b'{"x":1,"x":2}\n'; path.write_bytes(raw)
            with self.assertRaises(ValueError): boundary.read_document(path, hashlib.sha256(raw).hexdigest())

    def test_document_close_failure_preserves_identity_and_original_parse_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'; raw = b'not json'; path.write_bytes(raw)
            real_close = os.close; attempts = []
            def fail_close(fd):
                attempts.append(fd); real_close(fd); raise OSError('original injected uncertain close')
            with patch('private_camera_receiving.close.os.close', side_effect=fail_close):
                with self.assertRaises(UnresolvedOwnership) as caught:
                    boundary.read_document(path, hashlib.sha256(raw).hexdigest())
            held = caught.exception
            self.assertEqual(len(attempts), 1)
            self.assertIsInstance(held.original_failure, json.JSONDecodeError)
            self.assertEqual(held.uncertain_closes[0]['fd'], attempts[0])
            self.assertIsNotNone(held.uncertain_closes[0]['observed_before_close'])

    def checked_fixture(self, *, stale=False):
        packet, pins, identity, manifest, builds = self.fixture()
        root = Path(boundary.__file__).resolve().parents[1]
        sys.path.insert(0, str(root / 'tests/camera_sdk_concurrency'))
        from camera_sdk_concurrency import invocation
        pins[str(root / 'tests/build_snapshot.py')] = 'a' * 64
        names = ('candidateValidation', 'validationScanWork', 'update',
                 'dngCandidateValidation', 'dngValidation', 'semanticWorkers')
        for build in builds.values():
            build['runner_sha256'] = 'a' * 64
            build['source_sha256'] = {'src/' + name + '.ml': 'a' * 64 for name in names}
        if stale: builds['stock']['source_sha256']['src/update.ml'] = '0' * 64
        paths = []
        def read(path, digest, **kwargs):
            if str(path) == '/private/tmp/inert-plan': return packet
            if str(path) == packet['tool']['manifest']: return manifest
            return builds['stock' if 'stock' in str(path) else 'ox']
        def artifact(path):
            paths.append(str(path))
            self.assertTrue(str(path).startswith(str(root / 'src') + '/'))
            return 'a' * 64
        with patch.object(boundary, 'read_document', side_effect=read), \
             patch.object(boundary, 'current_sources', return_value=pins), \
             patch.object(boundary.os, 'lstat', return_value=SimpleNamespace(**identity)), \
             patch.object(invocation, 'artifact_sha', side_effect=artifact):
            result = boundary.checked_plan('/private/tmp/inert-plan', 'a' * 64)
        self.assertEqual(len(paths), 12)
        return result

    def test_checked_plan_binds_current_build_inventory_without_binary_or_payload_read(self):
        self.assertEqual(self.checked_fixture()['schema'], 'unison-all-scanned-sdk-plan/1')

    def test_checked_plan_stale_production_source_refuses(self):
        with self.assertRaises(ValueError): self.checked_fixture(stale=True)


if __name__ == '__main__': unittest.main()
