"""Two original tiny Python peer calls; no Unison/SDK/camera or canonical IO."""
import json
import os
from pathlib import Path
import sys
import tempfile

from invocation_journal import Journal, audit_attempted
from run import InvocationFailure, measure_invocation, save


PEER = '''import json,os,socket,struct,sys,time
from pathlib import Path
if '-server' in sys.argv:
    assert sys.stdin.buffer.read()==b'ping'
    sys.stdout.buffer.write(b'pong');sys.stdout.buffer.flush()
else:
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    sock.connect(os.environ['UNISON_SYNC_BENCH_SOCKET'])
    args=json.dumps([sys.executable,__file__,'-server']).encode()
    sock.sendall(struct.pack('>I',len(args))+args+b'ping')
    sock.shutdown(socket.SHUT_WR)
    result=b''
    while True:
        chunk=sock.recv(1024)
        if not chunk:break
        result+=chunk
    sock.close();assert result==b'pong'
    deadline=time.monotonic()+3
    while not Path(os.environ['UNISON_SYNC_BENCH_PROXY_RECEIPT']).exists():
        if time.monotonic()>deadline:raise RuntimeError('missing peer receipt')
        time.sleep(.005)
    sys.exit(int(sys.argv[1]))
'''


def main():
    os.umask(0o077)
    # Keep Unix socket names below Darwin's short path limit.
    work = Path(tempfile.mkdtemp(prefix='uj-', dir='/private/tmp'))
    peer = work / 'peer.py'
    peer.write_text(PEER)
    result = {'complete': False}
    output = work / 'journal.json'
    journal = Journal(result, lambda: save(output, result))
    here = Path(__file__).resolve().parent
    for expected in (0, 7):
        directory = work / str(expected)
        directory.mkdir()
        env = dict(os.environ, UNISON_SYNC_BENCH_BINARY=sys.executable,
                   UNISON_SYNC_BENCH_SERVER_FLAGS='[]',
                   UNISON_SYNC_BENCH_PROXY_RECEIPT=str(directory/'proxy.json'),
                   UNISON_SYNC_BENCH_SOCKET=str(directory/'s'),
                   UNISON_SYNC_BENCH_DEADLINE_SECONDS='10')
        command = [sys.executable, str(peer), str(expected)]
        journal.begin({'label': 'stock', 'mode': 'ordinary', 'workers': 1,
                       'directory': str(directory), 'stage': 'seed'}, command)
        try:
            outcome = measure_invocation(command, env, 10, here/'proxy.py',
                                         strict_group_settlement=True)
        except InvocationFailure as error:
            outcome = error.outcome
            assert expected == 7
        else:
            assert expected == 0
        journal.finish(outcome)
        assert outcome['returncode'] == expected
        # A later verification failure must not erase this call's evidence.
        result['failure'] = 'original synthetic post-call verification refusal'
        save(output, result)
        saved = json.loads(output.read_text())
        proof = audit_attempted(saved)
        assert proof['attempted_cli_invocations'] == (1 if expected == 0 else 2)
        assert proof['functional_success_inferred'] is False
    print(json.dumps({'workspace': str(work), 'journal': str(output),
                      'proof': proof, 'actual_calls': 2,
                      'scope': 'original Python peers and actual proxy/client/server ownership only'}))


if __name__ == '__main__':
    main()
