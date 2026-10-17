"""Production-linked stock/Ox exact-layout fixtures and strict-profile regressions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import struct
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler-scope',choices=('stock','ox','both'),default='both')
    args=parser.parse_args()
    modules=['semanticHash','semanticFile','componentHash','formatExtension','xmpObservation','xmpMerge',
             'dngSemantic','dngExtended','dngLayout','dngComponents','semanticDelta']
    root=Path(tempfile.mkdtemp(prefix='unison-dng-component-controls-',dir='/private/tmp'))
    sources=[ROOT/'src'/(m+ext) for m in modules for ext in ('.ml','.mli','.ox.mli.in') if (ROOT/'src'/(m+ext)).exists()]
    sources += [ROOT/'src'/name for name in ('semantic_mode_filter.ml','semanticHash_stubs.c',
                                           'semanticHash_evp.h','semanticFile_stubs.c')]
    sources += [ROOT/'tests/semantic'/name for name in ('layout_only.ml','private_safety.ml','dng_components.ml','archive_reference_fault.ml','record_fault_stubs.c')]
    sources += [ROOT/'tools/semantic-inspect/inspect.ml',ROOT/'tools/semantic-inspect/run.py',Path(__file__)]
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
        if args.compiler_scope not in ('both',label):
            continue
        compiler='/Users/alexy/.opam/'+switch+'/bin/ocamlopt'
        version=call([compiler,'-version'])['stdout'].strip()
        work=root/label;work.mkdir(mode=0o700)
        for module in modules:
            for ext in ('.mli','.ml'):
                out=call([str(mode),version,str(ROOT/'src'/(module+ext))])
                (work/(module+ext)).write_text(out['stdout'])
        for name in ('semanticHash_stubs.c','semanticHash_evp.h','semanticFile_stubs.c'):
            shutil.copyfile(ROOT/'src'/name,work/name)
        for name in ('layout_only.ml','private_safety.ml','dng_components.ml','archive_reference_fault.ml','record_fault_stubs.c'):
            shutil.copyfile(ROOT/'tests/semantic'/name,work/name)
        command=[compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c']
        for module in modules:command += [module+'.mli',module+'.ml']
        command += ['private_safety.ml','layout_only.ml','dng_components.ml','-o','dng-component-controls']
        previous=Path.cwd()
        try:
            os.chdir(work);call(command);call([str(work/'dng-component-controls')])
            shutil.copyfile(ROOT/'tools/semantic-inspect/inspect.ml',work/'inspect.ml')
            inspect_command=command[:-5]+['inspect.ml','-o','component-inspector']
            call(inspect_command)
            data=bytearray(256)
            struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
            for i,entry in enumerate(((273,4,1,160),(279,4,1,64),(700,1,16,96),(50706,1,4,257))):
                struct.pack_into('<HHII',data,10+12*i,*entry)
            data[96:112]=b'<x>value</x>    '
            fixture=work/'original-tiny.dng';fixture.write_bytes(data)
            report=json.loads(call([str(work/'component-inspector'),'--components',str(fixture)])['stdout'])
            assert report['schema']=='unison-dng-components/0'
            assert report['target']['sha256']==hashlib.sha256(data).hexdigest()
            assert report['target']['projections']['encoded_pixels']['bytes']==64
            legacy=json.loads(call([str(work/'component-inspector'),str(fixture)])['stdout'])
            assert legacy['target']['status']=='supported'
            result.setdefault('inspector_reports',{})[label]=report
            save(root,result)
            if label=='ox':
                portable=work/'frozen_decoder_capture.ml'
                portable.write_text('let publish (frozen:DngComponents.decoders) = Domain.Safe.spawn (fun () -> ignore frozen)\nlet publish_entry (entry:DngComponents.owner_entry) = Domain.Safe.spawn (fun () -> ignore(DngComponents.owner_entry_bytes entry))\nlet publish_index (index:DngComponents.owner_index) = Domain.Safe.spawn (fun () -> ignore(DngComponents.owner_index_usage index))\n')
                call([compiler,'-c',portable.name])
                for typ,operation in [('cache_capture','cache_capture_state'),
                                      ('owner_index_publication','owner_index_published')]:
                    leak=work/('owner_only_'+typ+'.ml')
                    leak.write_text('let leak (capture:DngComponents.'+typ+') = Domain.Safe.spawn (fun () -> ignore(DngComponents.'+operation+' capture))\n')
                    refused=call([compiler,'-c',leak.name],expected=2)
                    assert 'nonportable' in refused['stderr'] or 'contended' in refused['stderr']
            # A renamed manifest with directory-fsync failure cannot become an
            # authoritative archive hint. Test-only native shim, never production.
            call([compiler,'-c','record_fault_stubs.c'])
            call([compiler,'-ccopt','-Dfsync=unison_record_control_fsync','-c','semanticFile_stubs.c'])
            fault=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
            fault += ['archive_reference_fault.ml','semanticHash_stubs.o','semanticFile_stubs.o',
                      'record_fault_stubs.o','-o','archive-reference-fault']
            call(fault);call([str(work/'archive-reference-fault')])
            result.setdefault('archive_reference_fault_builds',{})[label]={
                'production_fault_switch':False,'macro':'fsync=unison_record_control_fsync',
                'executable_sha256':hashlib.sha256((work/'archive-reference-fault').read_bytes()).hexdigest()}
            save(root,result)
            # Original guard-removal control in an isolated filtered copy only.
            implementation=work/'dngComponents.ml';original=implementation.read_text()
            guard='  (match record with None -> () | Some pair -> check record_name (ComponentHash.max_checkpoint_size+80) pair);\n'
            assert original.count(guard)==1
            ablated=original.replace(guard,'')
            try:
                implementation.write_text(ablated)
                call(command[:-1]+['dng-component-ablation'])
                negative=call([str(work/'dng-component-ablation')],expected=2)
                assert 'changed named record escaped lookup before reader retirement' in negative['stderr']
                result.setdefault('lookup_guard_ablations',{})[label]={
                    'production_source_modified':False,'removed_guard':guard.strip(),
                    'filtered_original_sha256':hashlib.sha256(original.encode()).hexdigest(),
                    'ablated_sha256':hashlib.sha256(ablated.encode()).hexdigest(),
                    'expected_failure':'changed named record escaped lookup before reader retirement'}
                save(root,result)
            finally:implementation.write_text(original)
        finally:os.chdir(previous)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in result['source_pins'].items())
    result['complete']=True;save(root,result);print(root,flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
