"""Prepared remote case using existing strict loopback owners; not a CLI.

A future qualified outer owner must hold IO+both endpoint CPU grants, retain
unknown outcomes and audit every separate-session server. This module never
acquires grants or dispatches on import and has no standalone main entrypoint.
"""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'bench/sync'))
from run import measure_invocation, InvocationFailure
from audit import invocation, require, PAIRS
from ledger import begin, record

spec=importlib.util.spec_from_file_location('private_tag_fixture_source',
                         ROOT/'tests/private_dng_local_clone/run.py')
fixtures=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def prepare(directory):
    """Only future admitted owner may call; creates original synthetic bytes."""
    directory.mkdir(mode=0o700)
    for name in ('left','right','state'):(directory/name).mkdir(mode=0o700)
    for name in ('proxy.py','measure.py','launcher.py','ownership.py'):
        shutil.copyfile(ROOT/'bench/sync'/name,directory/name)
    (directory/'launcher.py').chmod(0o700)
    return fixtures.fixture(directory/'left/synthetic-private.dng',True)


def execute_case(directory, client, server, *, deadline_monotonic):
    """client/server are trusted pinned {label,path,sha256} records.

    Exceptions retain partial result files. They are NOT blanket settlement
    evidence: the caller must inspect every actual outcome and retain all owner
    handles/leases on unknown. This function has no permission/admission policy.
    """
    require((client['label'],server['label']) in PAIRS,'fixed compiler pair required')
    packet_length=prepare(directory)
    source=directory/'left/synthetic-private.dng'
    target=directory/'right/synthetic-private.dng'
    basis=directory/'prior-receiver-inode'
    before=fixtures.sha(source)
    def complement(path):
        data=path.read_bytes()
        require(len(data)==1048576,'synthetic length differs')
        return hashlib.sha256(data[:fixtures.XMP]+data[fixtures.XMP+packet_length:]).hexdigest()
    complement_before=complement(source)
    calls={}
    result={'compiler_pair':[client['label'],server['label']],'calls':calls}
    def save():(directory/'CASE.json').write_text(json.dumps(result,indent=2)+'\n')
    def call(stage):
        require(deadline_monotonic-time.monotonic()>10,'no new remote call near outer deadline')
        for item in (client,server):
            require(fixtures.sha(item['path'])==item['sha256'],'pinned binary changed')
        flags=['-clone','auto','-semanticdng','-semanticworkers','2','-maxthreads','2',
               '-adobevalidate','off','-debug','copy','-debug','semantic']
        socket=directory/(stage+'.sock')
        require(len(os.fsencode(socket))<100,'private Unix socket name too long')
        environment=dict(os.environ,UNISON=str(directory/'state'),
             UNISON_SYNC_BENCH_BINARY=server['path'],
             UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(flags),
             UNISON_SYNC_BENCH_PROXY_RECEIPT=str(directory/(stage+'-proxy.json')),
             UNISON_SYNC_BENCH_SOCKET=str(socket),UNISON_SYNC_BENCH_DEADLINE_SECONDS='25')
        command=[client['path'],str(directory/'left'),'ssh://localhost/'+str(directory/'right'),
             '-sshcmd',str(directory/'launcher.py'),'-servercmd',server['path'],
             '-batch','-auto','-fastcheck','false','-times',*flags]
        begin(directory, stage, command)
        try:
            outcome=measure_invocation(command,environment,
                     min(20,deadline_monotonic-time.monotonic()-5),directory/'proxy.py',
                     strict_group_settlement=True)
        except InvocationFailure as error:
            record(directory, stage, error.outcome)
            calls[stage]=error.outcome;save();raise
        record(directory, stage, outcome)
        calls[stage]=outcome;save()
        invocation(outcome)  # Each owner/server/pump must already have closed.
    call('seed')
    require(fixtures.sha(target)==before,'seed bytes differ')
    os.link(target,basis)  # Exclusively generated fixture, never a Photo file.
    old=fixtures.stamp(source)
    with source.open('r+b') as stream:
        stream.seek(fixtures.XMP);packet=stream.read(packet_length)
        require(packet.count(b'>1<')==1,'synthetic packet differs')
        stream.seek(fixtures.XMP);stream.write(packet.replace(b'>1<',b'>2<'))
    os.utime(source,ns=(source.stat().st_atime_ns,old['st_mtime_ns']+2000000000))
    expected=fixtures.sha(source)
    require(complement(source)==complement_before,'source complement changed')
    call('update')
    require(fixtures.sha(target)==expected and fixtures.sha(basis)==before,'update or basis differs')
    target_stamp=fixtures.stamp(target)
    call('noop')
    require(fixtures.stamp(target)==target_stamp and fixtures.sha(target)==expected
            and fixtures.sha(source)==expected and fixtures.sha(basis)==before,'noop preservation differs')
    require({p.name for p in (directory/'right').iterdir()}=={'synthetic-private.dng'},
            'receiver staging residue')
    require(complement(source)==complement_before,'source complement changed during calls')
    result.update(complement_sha256=complement_before,exact_output=True,basis_unchanged=True,noop_five_unchanged=True,
                  source_complement_unchanged=True,staging_cleaned=True,
                  before_sha256=before,after_sha256=expected)
    save()
    return result
