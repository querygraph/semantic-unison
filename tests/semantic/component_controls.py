"""Production-linked stock/Ox component-hash and scoped refinement controls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    modules=['semanticHash','semanticFile','componentHash']
    root=Path(tempfile.mkdtemp(prefix='unison-component-controls-',dir='/private/tmp'))
    sources=[ROOT/'src'/(m+ext) for m in modules for ext in ('.ml','.mli','.ox.mli.in')]
    sources += [ROOT/'src'/name for name in ('semantic_mode_filter.ml','semanticHash_stubs.c',
                                           'semanticHash_evp.h','semanticFile_stubs.c')]
    sources += [ROOT/'tests/semantic'/name for name in ('component_hash.ml','component_checkpoint.ml',
                                                       'record_publication_fault.ml','record_fault_stubs.c','reader_fault.ml','reader_fault_stubs.c')]
    sources += [Path(__file__)]
    result=dict(complete=False,calls=[],source_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sources},work=str(root),SDK_invoked=False,media_payload_opened=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    def call(argv,expected=0):
        out=invoke(argv,env,time.monotonic()+60)
        result['calls'].append(out);save(root,result)
        closed=out['client_cleanup']
        if not (closed['reaped'] and closed['other_group_members_absent_before_reap']):
            raise UnresolvedOwnership('layout control child/group unresolved')
        assert out['returncode']==expected and not out['capture_truncated'],out['stderr']
        return out
    mode=root/'semantic-mode-filter'
    shutil.copyfile(ROOT/'src/semantic_mode_filter.ml',root/'semantic_mode_filter.ml')
    call(['/Users/alexy/.opam/default/bin/ocamlopt',str(root/'semantic_mode_filter.ml'),'-o',str(mode)])
    for label,switch in [('stock','default'),('ox','5.2.0+ox')]:
        compiler='/Users/alexy/.opam/'+switch+'/bin/ocamlopt'
        version=call([compiler,'-version'])['stdout'].strip()
        work=root/label;work.mkdir(mode=0o700)
        for module in modules:
            for ext in ('.mli','.ml'):
                out=call([str(mode),version,str(ROOT/'src'/(module+ext))])
                (work/(module+ext)).write_text(out['stdout'])
        for name in ('semanticHash_stubs.c','semanticHash_evp.h','semanticFile_stubs.c'):
            shutil.copyfile(ROOT/'src'/name,work/name)
        for name in ('component_hash.ml','component_checkpoint.ml','record_publication_fault.ml','record_fault_stubs.c','reader_fault.ml','reader_fault_stubs.c'):
            shutil.copyfile(ROOT/'tests/semantic'/name,work/name)
        command=[compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c']
        for module in modules:command += [module+'.mli',module+'.ml']
        command += ['component_hash.ml','component_checkpoint.ml','-o','component-controls']
        previous=Path.cwd()
        try:
            os.chdir(work);call(command);call([str(work/'component-controls')])
            if label=='ox':
                path=work/'checkpoint_portable.ml'
                path.write_text('let share (value:ComponentHash.checkpoint) = Domain.Safe.spawn (fun () -> ignore(ComponentHash.checkpoint_bytes value))\n')
                call([compiler,'-c',path.name])
                for typ,operation in [('session','ignore(ComponentHash.bytes_requested shared)'),
                                      ('snapshot','ignore(ComponentHash.full_sha256 shared)'),
                                      ('reader','ignore(ComponentHash.read shared 0L 1)'),
                                      ('record_publication','ignore(ComponentHash.record_published shared)'),
                                      ('metadata_quota','ignore(ComponentHash.metadata_slot_reserved shared)')]:
                    path=work/('leak_'+typ+'.ml')
                    path.write_text('let leak (shared:ComponentHash.'+typ+') = Domain.Safe.spawn (fun () -> '+operation+')\n')
                    outcome=call([compiler,'-c',path.name],expected=2)
                    assert 'nonportable' in outcome['stderr'] or 'contended' in outcome['stderr']

            # Independent original positional-read syscall faults. The shim has
            # no production switch; only this copied native object is redirected.
            call([compiler,'-c','reader_fault_stubs.c'])
            call([compiler,'-ccopt','-Dpread=unison_reader_control_pread','-c','semanticFile_stubs.c'])
            reader_fault=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
            reader_fault += ['reader_fault.ml','semanticHash_stubs.o','semanticFile_stubs.o',
                             'reader_fault_stubs.o','-o','reader-fault-controls']
            call(reader_fault);call([str(work/'reader-fault-controls')])
            result.setdefault('test_only_reader_fault_builds',{})[label]={
                'macro':'pread=unison_reader_control_pread','production_fault_switch':False,
                'executable_sha256':hashlib.sha256((work/'reader-fault-controls').read_bytes()).hexdigest()}
            save(root,result)

            # Explicit original fault build, never the production executable:
            # compile the shim without the macro, then compile only the native
            # record implementation with fsync redirected to that shim.
            call([compiler,'-c','record_fault_stubs.c'])
            call([compiler,'-ccopt','-Dfsync=unison_record_control_fsync','-c','semanticFile_stubs.c'])
            fault=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
            fault += ['component_hash.cmx','record_publication_fault.ml','semanticHash_stubs.o',
                      'semanticFile_stubs.o','record_fault_stubs.o','-o','record-publication-fault']
            call(fault);call([str(work/'record-publication-fault')])
            result.setdefault('test_only_fault_builds',{})[label]={
                'macro':'fsync=unison_record_control_fsync','production_fault_switch':False,
                'executable_sha256':hashlib.sha256((work/'record-publication-fault').read_bytes()).hexdigest()}
            save(root,result)

        finally:os.chdir(previous)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in result['source_pins'].items())
    result['complete']=True;save(root,result);print(root,flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
