#!/usr/bin/env python3
"""Actual Unison receive gates on synthetic resumed/reused/external/merge data.

The executables are already-built private snapshots. The fixtures deliberately
are not valid DNGs: the endpoint-local Python driver qualifies the invocation
and publication contract, and makes no Adobe decoding/format assertion.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

ADMISSION_OPTIONS = []
HELPER_CONFIG = {}
SERVER_HELPER_DESCRIPTORS = None

DRIVER = r'''#!/usr/bin/python3
import hashlib,json,os,pathlib,sys,time,resource
here=pathlib.Path(__file__)
control=json.loads(here.with_suffix('.control.json').read_text())
args=sys.argv[1:]
assert len(args)==9 and args[0]=='--unison-dng-validation-v1',args
assert args[1]=='--expected-sha256' and args[3]=='--expected-size',args
assert args[5:8]==['--threads','1','--'],args
candidate=pathlib.Path(args[8])
assert candidate.is_absolute()
data=candidate.read_bytes()
digest=hashlib.sha256(data).hexdigest()
assert args[2]==digest and args[4]==str(len(data))
destination=pathlib.Path(control['destination'])
if control.get('directory',False):
    destination=destination/candidate.name
    assert candidate!=destination and candidate.parent.parent==destination.parent.parent
else:
    assert candidate!=destination and candidate.parent==destination.parent
before=destination.read_bytes() if destination.exists() else None
st=candidate.stat()
record=dict(candidate=str(candidate),destination=str(destination),sha256=digest,
    size=len(data),device=st.st_dev,inode=st.st_ino,argv=args,pid=os.getpid(),
    destination_sha256=None if before is None else hashlib.sha256(before).hexdigest(),
    mode=control['mode'],endpoint=control['endpoint'],nofile_hard=resource.getrlimit(resource.RLIMIT_NOFILE)[1])
fd=os.open(str(here.with_suffix('.calls.jsonl')),os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
try:
    encoded=(json.dumps(record,sort_keys=True)+'\n').encode()
    assert os.write(fd,encoded)==len(encoded)
finally:
    os.close(fd)
if control['mode']=='hang':
    while True:time.sleep(.02)
if control['mode']=='delay':
    def event(kind):
        fd=os.open(str(here.with_suffix('.events')),os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        try:
            encoded=(kind+' '+str(os.getpid())+'\n').encode()
            assert os.write(fd,encoded)==len(encoded)
        finally:os.close(fd)
    event('start');time.sleep(.2);event('end')
if control['mode']=='mutate':
    candidate.write_bytes(data+b'UNAPPROVED HELPER MUTATION')
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+('0'*64 if control['mode']=='wrong-receipt' else digest))
print('candidate-size '+str(len(data)))
print('driver-build '+control['build'])
print('structure valid')
print('decode success')
print('raw-digest missing')
print('errors '+('1' if control['mode']=='error' else '0'))
print('warnings 0')
print('END')
'''

COPY = r'''#!/usr/bin/python3
import hashlib,json,os,pathlib,sys,time,resource
here=pathlib.Path(__file__)
control=json.loads(here.with_suffix('.control.json').read_text())
assert len(sys.argv)==3,sys.argv
def local(spec):
    if spec.startswith('localhost:'):spec=spec[len('localhost:'):]
    path=pathlib.Path(spec)
    assert path.is_absolute()
    assert path.is_relative_to(here.parent)
    return path
source,destination=map(local,sys.argv[1:])
data=source.read_bytes()
if control['interrupt']=='partial':data=data[:len(data)//2]
with destination.open('wb') as stream:
    stream.write(data);stream.flush();os.fsync(stream.fileno())
st=destination.stat()
record=dict(source=str(source),destination=str(destination),size=len(data),
    sha256=hashlib.sha256(data).hexdigest(),inode=st.st_ino,device=st.st_dev,
    pid=os.getpid(),interrupt=control['interrupt'],nofile_hard=resource.getrlimit(resource.RLIMIT_NOFILE)[1])
fd=os.open(str(here.with_suffix('.calls.jsonl')),os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
try:
    encoded=(json.dumps(record,sort_keys=True)+'\n').encode()
    assert os.write(fd,encoded)==len(encoded)
finally:os.close(fd)
if control['interrupt']!='no':
    while True:time.sleep(.02)
'''

MERGE = r'''#!/usr/bin/python3
import hashlib,json,pathlib,sys,resource
here=pathlib.Path(__file__)
assert len(sys.argv)==4
inputs=[pathlib.Path(p).read_bytes() for p in sys.argv[1:3]]
result=here.with_suffix('.result').read_bytes()
pathlib.Path(sys.argv[3]).write_bytes(result)
with here.with_suffix('.calls.jsonl').open('a') as log:
    log.write(json.dumps(dict(inputs=[hashlib.sha256(p).hexdigest() for p in inputs],
        result=hashlib.sha256(result).hexdigest(),output=sys.argv[3],nofile_hard=resource.getrlimit(resource.RLIMIT_NOFILE)[1]),sort_keys=True)+'\n')
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f'{message}: actual={actual!r}, expected={expected!r}')


class Session:
    def __init__(self, root, binary):
        self.root, self.binary = root, binary
        root.mkdir()
        self.left, self.right, self.client_state, self.server_state = (
            root / n for n in ('left', 'right', 'client-state', 'server-state'))
        for path in (self.left, self.right, self.client_state, self.server_state):
            path.mkdir()
        self.drivers = {}
        for endpoint in ('client', 'server'):
            path = root / (endpoint + '-validator.py')
            path.write_text(DRIVER); path.chmod(0o700)
            self.drivers[endpoint] = path
        self.copy = root / 'external-copy.py'
        self.copy.write_text(COPY); self.copy.chmod(0o700)
        self.copy.with_suffix('.control.json').write_text(json.dumps({'interrupt': 'no'}))
        self.merger = root / 'merge.py'
        self.merger.write_text(MERGE); self.merger.chmod(0o700)
        self.launcher = root / 'loopback.py'
        self.launcher.write_text('#!/usr/bin/python3\nimport os,sys\n'
            'a=sys.argv[1:]\ni=a.index(' + repr(binary) + ')\n'
            'os.environ["UNISON"]=' + repr(str(self.server_state)) + '\n'
            'os.execv(a[i],a[i:])\n')
        self.launcher.chmod(0o700)
        server = self.config('server')
        if ADMISSION_OPTIONS:
            server['semanticvolumejobs'] = ADMISSION_OPTIONS[-1]
        (self.server_state / 'endpoint.prf').write_text(
            ''.join(f'{key} = {value}\n' for key, value in server.items()))
        self.sequence = 0
        self.control('image.dng')

    def config(self, endpoint):
        driver = self.drivers[endpoint]
        helper_config = dict(HELPER_CONFIG)
        if endpoint == 'server' and SERVER_HELPER_DESCRIPTORS is not None:
            helper_config['helperdescriptors'] = str(SERVER_HELPER_DESCRIPTORS)
        return {'adobevalidator': str(driver), 'adobevalidatorhash': sha(driver.read_bytes()),
                'adobevalidatorbuild': 'validation-path-' + endpoint + '-v1',
                'adobevalidatorthreads': '1', 'adobevalidatetimeout': '30', **helper_config}

    def control(self, name, *, client='pass', server='pass'):
        for endpoint, mode in (('client', client), ('server', server)):
            self.drivers[endpoint].with_suffix('.control.json').write_text(json.dumps({
                'endpoint': endpoint, 'build': self.config(endpoint)['adobevalidatorbuild'],
                'mode': mode, 'destination': str((self.left if endpoint == 'client' else self.right) / name)}))

    def calls(self, endpoint='server'):
        return records(self.drivers[endpoint].with_suffix('.calls.jsonl'))

    def command(self, *, policy='require', options=()):
        settings = [value for key, setting in self.config('client').items()
                    for value in ('-' + key, setting)]
        return [self.binary, str(self.left), 'ssh://localhost/' + str(self.right),
                '-sshcmd', str(self.launcher), '-servercmd', self.binary,
                '-batch', '-auto', '-fastcheck', 'false', '-clone', 'off',
                '-semanticworkers', '2', '-maxthreads', '1', '-adobevalidate', policy,
                '-debug', 'copy', '-debug', 'semantic'] + settings + ADMISSION_OPTIONS + list(options)

    def sync(self, *, policy='require', options=(), success=True):
        self.sequence += 1
        before = {endpoint: len(self.calls(endpoint)) for endpoint in ('client', 'server')}
        result = subprocess.run(self.command(policy=policy, options=options),
            env=dict(os.environ, UNISON=str(self.client_state)),
            capture_output=True, text=True, timeout=90)
        log = result.stdout + result.stderr
        (self.root / f'run-{self.sequence:02d}.log').write_text(log)
        assert_equal(result.returncode == 0, success, log)
        if ADMISSION_OPTIONS:
            for endpoint in ('client', 'server'):
                if len(self.calls(endpoint)) > before[endpoint]:
                    prefix = '[semantic]' if endpoint == 'client' else '[server: semantic]'
                    matching = [line for line in log.splitlines() if line.startswith(prefix)]
                    assert any(ADMISSION_OPTIONS[-1] + ' jobs per filesystem' in line for line in matching), \
                        'receiving endpoint did not report its requested filesystem execution limit:\n' + log
        return log

    def interruption(self, name, data, kind):
        """Crash after an external producer durably wrote staging, before validation.

        The subprocess group and exact recorded helper PID are ours. Killing
        them preserves only this disposable interrupted stage; no live file is
        created and no test-created helper survives the interruption.
        """
        self.control(name)
        (self.left / name).write_bytes(data)
        self.copy.with_suffix('.control.json').write_text(json.dumps({'interrupt': kind}))
        before = len(records(self.copy.with_suffix('.calls.jsonl')))
        log_path = self.root / 'interruption.log'
        process = None
        record = None
        with log_path.open('w') as output:
            try:
                process = subprocess.Popen(self.command(options=(
                    '-copythreshold', '0', '-copyprog', str(self.copy),
                    '-copyprogrest', str(self.copy), '-xferbycopying=false')),
                    env=dict(os.environ, UNISON=str(self.client_state)),
                    stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    observed = records(self.copy.with_suffix('.calls.jsonl'))
                    if len(observed) > before:
                        record = observed[-1]
                        break
                    if process.poll() is not None:
                        raise AssertionError(log_path.read_text())
                    time.sleep(.02)
                if record is None:
                    raise AssertionError('interrupted producer did not reach durable staging: ' + log_path.read_text())
                stage = Path(record['destination'])
                assert_equal(stage.read_bytes(), data if kind == 'complete' else data[:len(data)//2],
                             'external producer stage bytes')
                assert not (self.right / name).exists(), 'producer published before validation'
                assert not self.calls('client') and not self.calls('server'), 'validator ran before copy completion'
            finally:
                if record:
                    try: os.kill(record['pid'], signal.SIGKILL)
                    except ProcessLookupError: pass
                if process:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    process.wait(timeout=10)
        self.copy.with_suffix('.control.json').write_text(json.dumps({'interrupt': 'no'}))
        assert stage.exists(), 'crashed staging was discarded before recovery qualification'
        return record


def verify_call(call, data, *, previous=None, endpoint='server'):
    if HELPER_CONFIG:
        limit = SERVER_HELPER_DESCRIPTORS if endpoint == 'server' and SERVER_HELPER_DESCRIPTORS is not None else int(HELPER_CONFIG['helperdescriptors'])
        assert 3 <= call['nofile_hard'] <= limit, call
    assert_equal(call['sha256'], sha(data), 'candidate exact transferred/merged bytes')
    assert_equal(call['size'], len(data), 'candidate complete data length')
    assert_equal(call['destination_sha256'], None if previous is None else sha(previous),
                 'receiver live bytes during precommit invocation')
    assert_equal(call['endpoint'], endpoint, 'receiving endpoint owns helper')


def no_op(session, name, data):
    counts = [len(session.calls(e)) for e in ('client', 'server')]
    inodes = [(root / name).stat().st_ino for root in (session.left, session.right)]
    session.sync()
    assert_equal([len(session.calls(e)) for e in ('client', 'server')], counts,
                 'unchanged receive scope must not invoke validators')
    assert_equal([(root / name).stat().st_ino for root in (session.left, session.right)], inodes,
                 'unchanged synchronization replaced an inode')
    for root in (session.left, session.right):
        assert_equal((root / name).read_bytes(), data, 'no-op exact bytes')


def resumed(root, binary, kind, mode):
    session = Session(root, binary)
    name = 'resumed.DNG'
    data = bytes(range(256)) * 8192 + b'synthetic resume tail\n'
    produced = session.interruption(name, data, kind)
    session.control(name, server=mode)
    log = session.sync(success=mode == 'pass', options=('-xferbycopying=false',))
    marker = 'has already been transferred' if kind == 'complete' else 'Keeping '
    assert marker in log, 'did not exercise named resumed path:\n' + log
    if kind == 'partial':
        assert ' bytes previously transferred for file resumed.DNG' in log, log
    assert_equal(len(session.calls()), 1, 'resumed candidate receiving validation count')
    call = session.calls()[0]
    verify_call(call, data)
    assert_equal((call['device'], call['inode']), (produced['device'], produced['inode']),
                 'resume silently rebuilt a different staged output')
    assert not session.calls('client'), 'sender validated instead of resumed receiver'
    if mode != 'pass':
        assert 'Adobe DNG validation rejected' in log, log
        assert not (session.right / name).exists(), 'require committed resumed rejected stage'
        assert not Path(produced['destination']).exists(), 'rejected resumed stage remained reusable'
        session.control(name)
        retry = session.sync(options=('-xferbycopying=false',))
        assert 'has already been transferred' not in retry, 'retry reused rejected resumed stage'
        assert_equal(len(session.calls()), 2, 'fresh retry validation absent')
        verify_call(session.calls()[-1], data)
    assert_equal((session.right / name).read_bytes(), data, 'resume exact final destination')
    no_op(session, name, data)
    return {'kind': kind, 'mode': mode, 'candidate_inode': call['inode'],
            'calls': len(session.calls()), 'rejected_then_fresh_retry': mode != 'pass'}


def external(root, binary, mode, policy):
    session = Session(root, binary)
    name = 'external.dng'
    incoming = b'new external receive fixture\n' * 128
    session.control(name, server=mode)
    # External copy requires the `Copy` branch, so this is a new-file receive.
    # The absent destination makes gate atomicity directly observable and
    # prevents an update/rsync path masquerading as external copy.
    (session.left / name).write_bytes(incoming)
    before_calls = len(session.calls())
    rejected = policy == 'require' and mode != 'pass' or mode == 'mutate'
    log = session.sync(policy=policy, success=not rejected, options=(
        '-copythreshold', '0', '-copyprog', str(session.copy),
        '-copyprogrest', str(session.copy), '-xferbycopying=false'))
    copies = records(session.copy.with_suffix('.calls.jsonl'))
    assert_equal(len(copies), 1, 'external program must actually produce staging')
    assert str(session.copy) in log, log
    assert_equal(len(session.calls()) - before_calls, 0 if policy == 'off' else 1,
                 'external result receiving validation count')
    if policy != 'off':
        call = session.calls()[-1]
        verify_call(call, incoming)
        assert_equal(call['candidate'], copies[0]['destination'],
                     'validation did not inspect actual external result')
    if rejected:
        assert 'Adobe DNG validation rejected' in log, log
        assert not (session.right / name).exists(), 'rejected external result committed'
        assert not Path(copies[0]['destination']).exists(), 'external rejected stage remained reusable'
        session.control(name)
        session.sync(options=('-xferbycopying=false',))
        assert_equal(len(session.calls()) - before_calls, 2, 'external failure fresh retry gate')
    else:
        if mode != 'pass' and policy == 'warn':
            assert 'validation warning' in log, log
        assert_equal((session.right / name).read_bytes(), incoming, 'external exact commit')
    no_op(session, name, incoming)
    return {'mode': mode, 'policy': policy, 'external_calls': len(copies), 'rejected': rejected}


def moved(root, binary, mode, policy):
    session = Session(root, binary)
    donor, name = 'z-original.dng', 'a-moved.dng'
    data = b'exact moved-file content, no RAW decode claim\n' * 1024
    session.control(donor)
    (session.left / donor).write_bytes(data)
    session.sync()
    # Keep the donor in both replicas while introducing the same bytes at a
    # different name. This deterministically reaches Unison's moved-file hint
    # backend rather than its rename-only move (excluded from received scope).
    (session.left / name).write_bytes(data)
    session.control(name, server=mode)
    before = len(session.calls())
    rejected = policy == 'require' and mode != 'pass'
    log = session.sync(policy=policy, success=not rejected)
    assert 'Shortcut: copied ' in log and 'from local file ' in log, log
    assert_equal(len(session.calls()) - before, 1, 'moved-file reuse omitted receiver gate')
    verify_call(session.calls()[-1], data)
    assert_equal((session.right / donor).read_bytes(), data, 'receiver reuse donor changed')
    if rejected:
        assert 'Adobe DNG validation rejected' in log, log
        assert not (session.right / name).exists(), 'reuse require committed rejected candidate'
        assert not Path(session.calls()[-1]['candidate']).exists(), 'rejected hint-copy stage remained reusable'
        session.control(name)
        retry = session.sync()
        assert 'Shortcut: copied ' in retry, retry
        assert_equal(len(session.calls()) - before, 2, 'reuse retry omitted validation')
    elif mode != 'pass':
        assert 'validation warning' in log, log
    assert_equal((session.right / name).read_bytes(), data, 'reuse exact final destination')
    no_op(session, name, data)
    return {'mode': mode, 'policy': policy, 'receiver_calls': len(session.calls()) - before,
            'hint_reuse_not_rename_only': True}


def merged(root, binary, client_mode, server_mode):
    session = Session(root, binary)
    name = 'merge.dng'
    original = b'common archived bytes\n' * 128
    first = original + b'first replica edit'
    second = original + b'second replica edit'
    result = original + b'exact deterministic generated merge artifact'
    session.control(name)
    (session.left / name).write_bytes(original)
    session.sync()
    (session.left / name).write_bytes(first)
    (session.right / name).write_bytes(second)
    session.merger.with_suffix('.result').write_bytes(result)
    session.control(name, client=client_mode, server=server_mode)
    before = {endpoint: len(session.calls(endpoint)) for endpoint in ('client', 'server')}
    merge_options = ('-merge', 'Name *.dng -> ' + str(session.merger) + ' CURRENT1 CURRENT2 NEW')
    succeeds = client_mode == 'pass' and server_mode == 'pass'
    log = session.sync(options=merge_options, success=succeeds)
    outputs = records(session.merger.with_suffix('.calls.jsonl'))
    assert_equal(len(outputs), 1, 'merge command did not generate one exact result')
    assert_equal(outputs[0]['inputs'], [sha(first), sha(second)], 'merge actual conflict inputs')
    client = session.calls('client')[before['client']:]
    server = session.calls('server')[before['server']:]
    assert_equal(len(client), 1, 'first merge receiver gate absent')
    verify_call(client[0], result, previous=first, endpoint='client')
    if client_mode != 'pass':
        assert not server, 'second receiver reached after first require rejection'
        assert not Path(client[0]['candidate']).exists(), 'rejected first merge stage remained reusable'
        assert_equal((session.left / name).read_bytes(), first, 'first rejected merge replaced live input')
        assert_equal((session.right / name).read_bytes(), second, 'first failure replaced second live input')
    else:
        assert_equal(len(server), 1, 'second merge receiver gate absent')
        verify_call(server[0], result, previous=second)
        if server_mode != 'pass':
            assert not Path(server[0]['candidate']).exists(), 'rejected second merge stage remained reusable'
        assert_equal((session.left / name).read_bytes(), result, 'first accepted merge was not committed')
        assert_equal((session.right / name).read_bytes(), result if server_mode == 'pass' else second,
                     'second rejected merge must preserve its independent old live bytes')
    if not succeeds:
        assert 'Adobe DNG validation rejected' in log, log
        # Preserve actual partial-commit behavior for explicit review, then
        # recapture both live inputs before a finite retry of the same exact
        # merge artifact. Unison has no cross-replica atomic rename.
        session.control(name)
        retry = session.sync(options=merge_options)
        assert 'Merge command:' in retry, 'partial failure was silently treated as one-sided convergence'
        retried_outputs = records(session.merger.with_suffix('.calls.jsonl'))
        assert_equal(len(retried_outputs), 2, 'merge recovery must retain a real conflict and rerun the merge')
        assert_equal(retried_outputs[-1]['inputs'],
                     [sha(first if client_mode != 'pass' else result), sha(second)],
                     'retry did not recapture actual independently committed inputs')
        assert_equal((session.left / name).read_bytes(), result, 'merge recovery first exact bytes')
        assert_equal((session.right / name).read_bytes(), result, 'merge recovery second exact bytes')
        if server_mode != 'pass':
            assert_equal(len(session.calls('server')) - before['server'], 2,
                         'second receiver recovery bypassed required validation')
        if client_mode != 'pass':
            assert_equal(len(session.calls('client')) - before['client'], 2,
                         'first receiver recovery bypassed required validation')
        verify_call(session.calls('client')[-1], result,
                    previous=first if client_mode != 'pass' else result, endpoint='client')
        verify_call(session.calls('server')[-1], result, previous=second)
    no_op(session, name, result)
    return {'client_mode': client_mode, 'server_mode': server_mode,
            'first_committed_before_second_rejection': client_mode == 'pass' and server_mode != 'pass',
            'recovery': 'exact convergence with required receive gates' if not succeeds else 'not needed'}


def timed_out(root, binary, policy):
    session = Session(root, binary)
    name = 'timed.dng'
    original = b'previous live timeout fixture\n' * 128
    incoming = original + b'received timeout update'
    retry_data = incoming + b'fresh post-timeout successful update'
    session.control(name)
    (session.left / name).write_bytes(original)
    session.sync()
    session.control(name, server='hang')
    config = dict(session.config('server'), adobevalidatetimeout='1')
    if ADMISSION_OPTIONS:
        config['semanticvolumejobs'] = ADMISSION_OPTIONS[-1]
    (session.server_state / 'endpoint.prf').write_text(
        ''.join(f'{key} = {value}\n' for key, value in config.items()))
    (session.left / name).write_bytes(incoming)
    before = len(session.calls())
    started = time.monotonic()
    log = session.sync(policy=policy, success=policy == 'warn')
    elapsed = time.monotonic() - started
    assert elapsed < 15, 'timed-out receive failed to settle its own supervised child'
    assert 'SDK driver timed out' in log, log
    assert_equal(len(session.calls()) - before, 1, 'timeout receiving invocation count')
    call = session.calls()[-1]
    verify_call(call, incoming, previous=original)
    # HelperSupervisor returns only after the child is reaped. Checking its
    # exact recorded PID here distinguishes a settled timeout from abandoned
    # background execution; the helper is finite-owned by this disposable case.
    try:
        os.kill(call['pid'], 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError('timed-out validation child remained alive or unreaped')
    assert_equal((session.right / name).read_bytes(), incoming if policy == 'warn' else original,
                 'timeout receive policy changed old live bytes incorrectly')
    assert not Path(call['candidate']).exists(), 'timeout stage remained resumable after settlement'
    session.control(name)
    (session.left / name).write_bytes(retry_data)
    session.sync()
    verify_call(session.calls()[-1], retry_data, previous=incoming if policy == 'warn' else original)
    no_op(session, name, retry_data)
    return {'policy': policy, 'elapsed_seconds': elapsed, 'child_reaped_before_result': True,
            'followup_receive_progress': True}


def cancelled(root, binary, policy):
    session = Session(root, binary)
    name = 'cancelled.dng'
    original = b'previous live cancellation fixture\n' * 128
    incoming = original + b'reverse receive that must never commit after cancellation'
    session.control(name)
    (session.left / name).write_bytes(original)
    session.sync()
    # Receiving into the client lets an actual SIGINT exercise that endpoint's
    # owner-loop abort watcher and active supervised child. Remote client-only
    # SIGINT propagation is a separate transport question, not claimed here.
    (session.right / name).write_bytes(incoming)
    session.control(name, client='hang')
    before = len(session.calls('client'))
    log_path = session.root / 'cancellation.log'
    process = None
    call = None
    with log_path.open('w') as output:
        try:
            process = subprocess.Popen(session.command(policy=policy),
                env=dict(os.environ, UNISON=str(session.client_state)),
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                current = session.calls('client')
                if len(current) > before:
                    call = current[-1]
                    break
                if process.poll() is not None:
                    raise AssertionError(log_path.read_text())
                time.sleep(.02)
            if call is None:
                raise AssertionError('cancellation fixture did not start its receiving helper')
            verify_call(call, incoming, previous=original, endpoint='client')
            started = time.monotonic()
            process.send_signal(signal.SIGINT)
            status = process.wait(timeout=10)
            elapsed = time.monotonic() - started
            assert status != 0, 'cancellation was reported as successful convergence'
        finally:
            if process and process.poll() is None:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait(timeout=10)
    log = log_path.read_text()
    assert 'Update propagation interrupted' in log and 'Aborted by user request' in log, log
    try:
        os.kill(call['pid'], 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError('cancelled receiving helper remained alive or unreaped')
    assert_equal((session.left / name).read_bytes(), original, 'cancellation replaced old live receiver')
    assert_equal((session.right / name).read_bytes(), incoming, 'cancellation mutated sending source')
    assert not Path(call['candidate']).exists(), 'cancelled validation stage remained resumable'
    session.control(name)
    session.sync()
    verify_call(session.calls('client')[-1], incoming, previous=original, endpoint='client')
    no_op(session, name, incoming)
    return {'policy': policy, 'elapsed_seconds': elapsed, 'active_client_receiver_cancelled': True,
            'child_reaped_before_result': True, 'fresh_retry_validated': True,
            'remote_signal_forwarding': 'not qualified by this case'}


def directory_admission(root, binary):
    session = Session(root, binary)
    name = 'parallel-directory'
    album = session.left / name
    album.mkdir()
    expected = {}
    for number in range(6):
        filename = f'item-{number}.dng'
        data = (b'synthetic directory receive payload\n' + bytes([number])) * 128
        (album / filename).write_bytes(data)
        expected[filename] = data
    driver = session.drivers['server']
    driver.with_suffix('.control.json').write_text(json.dumps({
        'endpoint': 'server', 'build': session.config('server')['adobevalidatorbuild'],
        'mode': 'delay', 'destination': str(session.right / name), 'directory': True}))
    session.sync()
    calls = session.calls()
    assert_equal(len(calls), 6, 'directory receiver validation count')
    for call in calls:
        filename = Path(call['destination']).name
        verify_call(call, expected[filename])
        assert_equal((session.right / name / filename).read_bytes(), expected[filename],
                     'directory exact publication')
    # One atomic O_APPEND record per event avoids cross-process clock origins.
    active, peak = set(), 0
    events = [line.split() for line in driver.with_suffix('.events').read_text().splitlines()]
    for kind, pid in events:
        if kind == 'start':
            assert pid not in active
            active.add(pid); peak = max(peak, len(active))
        elif kind == 'end':
            assert pid in active
            active.remove(pid)
        else:
            raise AssertionError('unknown directory execution event')
    assert not active and len(events) == 12
    assert 1 <= peak <= 2, f'directory helpers exceeded shared CPU budget: {peak}'
    if ADMISSION_OPTIONS == ['-semanticvolumejobs', '1']:
        assert_equal(peak, 1, 'one filesystem execution credit did not serialize helpers')
    before = len(calls)
    inodes = {(session.right / name / filename).stat().st_ino for filename in expected}
    session.sync()
    assert_equal(len(session.calls()), before, 'unchanged directory invoked extra validation')
    assert_equal({(session.right / name / filename).stat().st_ino for filename in expected},
                 inodes, 'unchanged directory replaced a native file')
    return {'files': 6, 'peak_helpers': peak, 'cpu_budget': 2,
            'filesystem_limit_behaviorally_checked': ADMISSION_OPTIONS == ['-semanticvolumejobs', '1']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unison', type=Path, required=True)
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--volume-jobs', type=int,
                        help='request semanticvolumejobs (new admission integration; 1 detects nested waits)')
    parser.add_argument('--helper-limiter', type=Path)
    parser.add_argument('--helper-descriptors', type=int, default=64)
    parser.add_argument('--server-helper-descriptors', type=int)
    args = parser.parse_args()
    global SERVER_HELPER_DESCRIPTORS
    if args.server_helper_descriptors is not None:
        if not args.helper_limiter or args.server_helper_descriptors < 3:
            parser.error('--server-helper-descriptors requires limiter and at least3')
        SERVER_HELPER_DESCRIPTORS = args.server_helper_descriptors
    if args.helper_limiter:
        if args.helper_descriptors < 3:
            parser.error('--helper-descriptors must be at least3')
        limiter = args.helper_limiter.resolve()
        HELPER_CONFIG.update(helperlimiter=str(limiter),helperlimiterhash=sha(limiter.read_bytes()),
                            helperdescriptors=str(args.helper_descriptors))
    if args.volume_jobs is not None:
        if args.volume_jobs < 0:
            parser.error('--volume-jobs must be nonnegative')
        ADMISSION_OPTIONS.extend(['-semanticvolumejobs', str(args.volume_jobs)])
    binary = str(args.unison.resolve())
    root = Path(tempfile.mkdtemp(prefix='unison-validation-paths-', dir='/private/tmp'))
    results = []
    receipt = {'scope': 'Adobe-free actual Unison receive-gate integration; synthetic bytes only',
               'binary': binary, 'binary_sha256': sha(Path(binary).read_bytes()),
               'test_sha256': sha(Path(__file__).read_bytes()), 'work': str(root), 'cases': results,
               'admission_options': ADMISSION_OPTIONS, 'helper_limits': HELPER_CONFIG, 'server_helper_descriptors': SERVER_HELPER_DESCRIPTORS,
               'limitations': ['Synthetic receive-gate behavior, not Adobe format/decode correctness.',
                   'Reused file is a retained exact donor; rename-only moves remain outside received scope.',
                   'Merges use an existing configured external merge command, not an XMP semantic merge.',
                   'Process crashes are an interruption fixture; crash-durable publication is not claimed.']}
    try:
        for kind, mode in (('complete', 'pass'), ('complete', 'error'),
                           ('partial', 'pass'), ('partial', 'error')):
            label = 'resume-' + kind + '-' + mode
            value = resumed(root / label, binary, kind, mode)
            results.append({'name': label, 'status': 'passed', **value})
            print('PASS', label, flush=True)
        for mode, policy in (('pass', 'require'), ('error', 'require'),
                             ('error', 'warn'), ('error', 'off'), ('mutate', 'warn')):
            label = 'external-' + mode + '-' + policy
            value = external(root / label, binary, mode, policy)
            results.append({'name': label, 'status': 'passed', **value})
            print('PASS', label, flush=True)
        for mode, policy in (('pass', 'require'), ('error', 'require'), ('error', 'warn')):
            label = 'reuse-' + mode + '-' + policy
            value = moved(root / label, binary, mode, policy)
            results.append({'name': label, 'status': 'passed', **value})
            print('PASS', label, flush=True)
        for client, server in (('pass', 'pass'), ('error', 'pass'), ('pass', 'error'),
                               ('pass', 'wrong-receipt')):
            label = 'merge-' + client + '-' + server
            value = merged(root / label, binary, client, server)
            results.append({'name': label, 'status': 'passed', **value})
            print('PASS', label, flush=True)
        for policy in ('require', 'warn'):
            label = 'timeout-' + policy
            value = timed_out(root / label, binary, policy)
            results.append({'name': label, 'status': 'passed', **value})
            print('PASS', label, flush=True)
        for policy in ('require', 'warn'):
            label = 'cancel-' + policy
            value = cancelled(root / label, binary, policy)
            results.append({'name': label, 'status': 'passed', **value})
            print('PASS', label, flush=True)
        label = 'directory-execution-admission'
        value = directory_admission(root / label, binary)
        results.append({'name': label, 'status': 'passed', **value})
        print('PASS', label, flush=True)
        if HELPER_CONFIG:
            observed = []
            for path in root.rglob('*.calls.jsonl'):
                for call in records(path):
                    if 'nofile_hard' in call:
                        assert 3 <= call['nofile_hard'] <= args.helper_descriptors,call
                        observed.append(call['nofile_hard'])
            assert len(observed) >= 30, 'bounded helper receipts absent'
            receipt['observed_helper_hard_limits'] = observed
        receipt['status'] = 'passed'
        print(f'{len(results)} actual receive-path cases passed; no Adobe/Lightroom invocation. Work: {root}')
    finally:
        receipt.setdefault('status', 'failed')
        (root / 'RESULT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        if args.receipt:
            args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        if receipt['status'] == 'passed' and not args.keep_work:
            import shutil
            shutil.rmtree(root)


if __name__ == '__main__':
    main()
