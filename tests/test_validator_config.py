#!/usr/bin/env python3
"""Keep remote validator commands pinned to each endpoint's local configuration.

All drivers and files are synthetic. --legacy-sender is a pre-v1 feature-branch
binary; requested warn/require must fail v0/v1 negotiation in both directions.
Validation off remains compatible. --old-peer is unmodified Unison.
"""
import argparse
import contextlib
import hashlib
import os
from pathlib import Path
import subprocess
import shutil
import tempfile


DRIVER = '''#!/usr/bin/python3
import hashlib,pathlib,sys
here=pathlib.Path(__file__)
data=pathlib.Path(sys.argv[-1]).read_bytes()
assert sys.argv[sys.argv.index('--threads')+1]=='1'
with here.with_suffix('.calls').open('a') as log:
    log.write(sys.argv[-1]+'\\n')
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+hashlib.sha256(data).hexdigest())
print('candidate-size '+str(len(data)))
print('driver-build BUILD_ID')
print('structure valid')
print('decode success')
print('raw-digest missing')
print('errors 0')
print('warnings 0')
print('END')
'''


def driver(root, name):
    name = name.replace(' ', '-')
    executable = root / (name + '.py')
    executable.write_text(DRIVER.replace('BUILD_ID', name))
    executable.chmod(0o700)
    return dict(adobevalidator=str(executable),
                adobevalidatorhash=hashlib.sha256(executable.read_bytes()).hexdigest(),
                adobevalidatorbuild=name, adobevalidatorthreads='1', adobevalidatetimeout='30')


def call_count(config):
    path = Path(config['adobevalidator']).with_suffix('.calls')
    return len(path.read_text().splitlines()) if path.exists() else 0


def flags(config):
    return [value for key, setting in config.items() for value in ['-' + key, setting]]


class Session:
    def __init__(self, root, client, server):
        self.root, self.client, self.server = root, client, server
        self.left, self.right, self.client_state, self.server_state = (
            root / name for name in ('left', 'right', 'client-state', 'server-state'))
        for path in (self.left, self.right, self.client_state, self.server_state):
            path.mkdir(parents=True)
        self.launcher = root / 'loopback.py'
        self.sequence = 0
        self.server_options([])

    def server_options(self, options):
        self.launcher.write_text('#!/usr/bin/python3\nimport os,sys\n'
                                 'a=sys.argv[1:]\ni=a.index(' + repr(self.server) + ')\n'
                                 'os.environ["UNISON"]=' + repr(str(self.server_state)) + '\n'
                                 'os.execv(a[i],a[i:]+' + repr(options) + ')\n')
        self.launcher.chmod(0o700)

    def receiver_profile(self, config):
        path = self.server_state / 'endpoint.prf'
        if config is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(''.join(key + ' = ' + value + '\n' for key, value in config.items()))

    def sync(self, sender, policy='require', success=True):
        command = [self.client, str(self.left), 'ssh://localhost/' + str(self.right),
                   '-sshcmd', str(self.launcher), '-servercmd', self.server,
                   '-batch', '-auto', '-fastcheck', 'false', '-clone', 'off',
                   '-semanticworkers', '2', '-adobevalidate', policy] + flags(sender)
        result = subprocess.run(command, env=dict(os.environ, UNISON=str(self.client_state)),
                                capture_output=True, text=True, timeout=60)
        log = result.stdout + result.stderr
        self.sequence += 1
        (self.root / f'run-{self.sequence:02d}.log').write_text(log)
        import json
        (self.root / f'run-{self.sequence:02d}.command.json').write_text(json.dumps({
            'argv': command, 'endpoint_state': str(self.client_state),
            'exit_code': result.returncode, 'expected_success': success}, indent=2) + '\n')
        assert (result.returncode == 0) == success, log
        return log


def exercise(root, client, server, label):
    session = Session(root, client, server)
    sender = driver(root, label + '-sender')
    receiver = driver(root, label + '-receiver')
    startup = driver(root, label + '-startup-cli')
    wrong_sender = dict(sender, adobevalidatorhash='0' * 64,
                        adobevalidatorbuild='sender-mismatched-build',
                        adobevalidatorthreads='4096', adobevalidatetimeout='0')
    session.receiver_profile(receiver)
    source, destination = session.left / 'image.dng', session.right / 'image.dng'
    original = b'synthetic receive gate fixture\n' * 128
    source.write_bytes(original)
    session.sync(wrong_sender)
    assert destination.read_bytes() == original
    assert call_count(receiver) == 1 and call_count(sender) == 0
    # Server startup options override only this server's endpoint defaults.
    session.receiver_profile(wrong_sender)
    session.server_options(flags(startup))
    source.write_bytes(original + b'CLI receiver update')
    session.sync(wrong_sender)
    assert destination.read_bytes() == source.read_bytes()
    assert call_count(startup) == 1 and call_count(sender) == 0
    session.server_options([])
    # A well-configured sender cannot fill an absent receiver configuration.
    session.receiver_profile(None)
    previous = destination.read_bytes()
    changed = original + b'missing receiver update'
    source.write_bytes(changed)
    log = session.sync(sender, success=False)
    assert 'Adobe DNG validation rejected' in log, log
    assert destination.read_bytes() == previous
    assert call_count(sender) == 0
    log = session.sync(sender, policy='warn')
    assert 'validation warning' in log, log
    assert destination.read_bytes() == changed
    source.write_bytes(original + b'validation off update')
    log = session.sync(sender, policy='off')
    assert 'validation warning' not in log and destination.read_bytes() == source.read_bytes()
    # Receiver pin mismatches cannot be rescued by the sender's valid driver.
    session.receiver_profile(dict(receiver, adobevalidatorhash='0' * 64))
    previous = destination.read_bytes()
    source.write_bytes(original + b'wrong local pin update')
    log = session.sync(sender, success=False)
    assert 'Adobe DNG validation rejected' in log, log
    assert destination.read_bytes() == previous and call_count(sender) == 0
    session.receiver_profile(receiver)
    session.sync(sender)
    assert destination.read_bytes() == source.read_bytes()
    before_receiver = call_count(receiver)
    # Receiving into the client uses the client's independently configured tool.
    destination.write_bytes(original + b'reverse receive update')
    session.sync(sender)
    assert source.read_bytes() == destination.read_bytes()
    assert call_count(sender) == 1 and call_count(receiver) == before_receiver
    print(label + ': receiver profile/startup CLI; sender override ignored; missing/bad receiver pin rejection; warn/off; reverse receive passed.')


def old_peer(root, current, old):
    session = Session(root, current, old)
    sender = driver(root, 'old-peer-sender')
    (session.left / 'image.dng').write_bytes(b'old peer must reject requested validation')
    log = session.sync(sender, success=False)
    assert 'dng-validation-v1 support on both replicas' in log, log
    assert not (session.right / 'image.dng').exists() and call_count(sender) == 0
    print('Unmodified peer: requested validation rejected before commit.')


def incompatible_validation(root, current, legacy):
    for direction, client, server in (('v1-to-v0', current, legacy),
                                      ('v0-to-v1', legacy, current)):
        for policy in ('require', 'warn'):
            session = Session(root / (direction + '-' + policy), client, server)
            sender = driver(session.root, direction + '-' + policy + '-sender')
            receiver = driver(session.root, direction + '-' + policy + '-receiver')
            session.receiver_profile(receiver)
            source, destination = session.left / 'image.dng', session.right / 'image.dng'
            original = b'synthetic capability refusal fixture\n' * 128
            source.write_bytes(original)
            log = session.sync(sender, policy=policy, success=False)
            assert ('dng-validation-v1 support on both replicas' in log or
                    'dng-validation-v0 support on both replicas' in log), log
            assert not destination.exists(), 'incompatible validation published a receive'
            assert source.read_bytes() == original
            assert call_count(sender) == call_count(receiver) == 0
            session.sync(sender, policy='off')
            assert destination.read_bytes() == original
            assert call_count(sender) == call_count(receiver) == 0
            print(direction + ': ' + policy + ' refused before publication/helper; off compatible.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--unison', type=Path, required=True)
    parser.add_argument('--legacy-sender', type=Path)
    parser.add_argument('--old-peer', type=Path)
    parser.add_argument('--keep-work', action='store_true')
    args = parser.parse_args()
    current = str(args.unison.resolve())
    with contextlib.ExitStack() as cleanup:
        temp = tempfile.mkdtemp(prefix='unison-validator-config-', dir='/private/tmp')
        if not args.keep_work:
            cleanup.callback(shutil.rmtree, temp)
        else:
            print('Retained configuration artifacts: ' + temp, flush=True)
        root = Path(temp)
        exercise(root / 'current', current, current, 'current sender')
        if args.legacy_sender:
            incompatible_validation(root / 'legacy', current, str(args.legacy_sender.resolve()))
        if args.old_peer:
            old_peer(root / 'old', current, str(args.old_peer.resolve()))


if __name__ == '__main__':
    main()
