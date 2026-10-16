"""Build/run original fake-only mixed workload controls, never a native SDK entry."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tests'), str(ROOT/'tests/sdk_host_matrix'),
               str(ROOT/'tests/supervised_external'), str(ROOT/'tests/camera_sdk_receiving')]
from shared_child import invoke
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
import external_records
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit import audit as audit_mixed


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(value, reason):
    if not value: raise ValueError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-result', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.build_result.read_text())
    require(build['complete'] and build['build_exit']==build['selftest_exit']==0, 'qualified build required')
    require(sha(build['compiler'])==build['compiler_sha256'], 'compiler pin differs')
    src = Path(build['workspace'])/'src'
    for name,digest in build['source_sha256'].items():
        if name.startswith('src/'): require(sha(ROOT/name)==digest, 'current production differs: '+name)
    spec=importlib.util.spec_from_file_location('bridge_builder', ROOT/'tests/supervised_external/run.py')
    builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
    text=(src/'Makefile.OCaml').read_text()
    modules=builder.objects(text, 'OCAMLOBJS'); modules=modules[:modules.index('supervisedExternal.cmx')+1]
    native=builder.objects(text, 'COBJS')
    work=Path(tempfile.mkdtemp(prefix='unison-mixed-validation-', dir='/private/tmp'))
    shutil.copyfile(ROOT/'tests/mixed_validation/probe.ml', work/'probe.ml')
    commands=[]
    def run(argv, cwd, seconds=20):
        previous=os.getcwd()
        try:
            os.chdir(cwd)
            out=invoke([str(x) for x in argv], dict(os.environ,UNISON=str(cwd/'state')),
                       time.monotonic()+seconds)
        finally:os.chdir(previous)
        proof=out['client_cleanup']
        require(proof['reaped'] and proof['other_group_members_absent_before_reap'], 'direct owner group unresolved')
        commands.append(out)
        return out
    includes=[src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic']
    flags=[str(v) for p in includes for v in ('-I',p)]+['-I','+unix','-I','+str']
    compiled=run([build['compiler'],*flags,'unix.cmxa','str.cmxa',*[src/m for m in modules],
                  *[src/n for n in native],'probe.ml','-o','probe'],work)
    require(compiled['returncode']==0, compiled['stderr'])
    cases=[]
    for mode in ('pass','sdk-error','metadata-error','both-error'):
        directory=work/mode; directory.mkdir(mode=0o700)
        candidate=directory/'private.dng'; candidate.write_bytes(b'original mixed protocol control\0'*128)
        before=tuple(getattr(os.lstat(candidate),n) for n in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink','st_uid'))
        expected=sha(candidate)
        sdk=directory/'validator.py'; metadata=directory/'metadata.py'
        sdk.write_text('#!'+sys.executable+'\n'+'''import hashlib,json,os,pathlib,sys
here=pathlib.Path(__file__)
here.with_suffix('.calls').write_text(str(os.getpid()))
data=pathlib.Path(sys.argv[-1]).read_bytes()
errors=1 if here.parent.name in ('sdk-error','both-error') else 0
print('UNISON-DNG-VALIDATION 1\\ncandidate-sha256 '+hashlib.sha256(data).hexdigest()+'\\ncandidate-size '+str(len(data))+'\\ndriver-build synthetic-mixed-v1\\nstructure valid\\ndecode success\\nraw-digest valid\\nerrors '+str(errors)+'\\nwarnings 0\\nEND')
''')
        metadata.write_text('#!'+sys.executable+'\n'+'''import json,os,pathlib,sys
here=pathlib.Path(__file__)
here.with_suffix('.calls').write_text(str(os.getpid()))
assert sys.argv[1:]==['-config','','-j','-s','-XMP:Rating','-XMP:Label','-ExifToolVersion','--',sys.argv[-1]]
if here.parent.name in ('metadata-error','both-error'):sys.exit(7)
print(json.dumps([{'SourceFile':sys.argv[-1],'Rating':3,'Label':'Blue','ExifToolVersion':'synthetic-only'}]))
''')
        sdk.chmod(0o700); metadata.chmod(0o700)
        out=run([work/'probe',sdk,metadata,candidate,sha(sdk),'synthetic-mixed-v1',expected,str(candidate.stat().st_size)],directory)
        try:
            require(out['returncode']==0 and not out['capture_truncated'], 'mixed owner did not close normally')
            log=out['stdout']+out['stderr']
            raw=re.findall(r'^SDK_RESULT pid=([1-9][0-9]*) status=exit:0 outcome=completed other-members=0 truncated=false stdout-hex=([0-9a-f]+) stderr-hex=$',log,re.M)
            require(len(raw)==1, 'exact SDK process/group diagnostic absent')
            sdk_pid=int((sdk.with_suffix('.calls')).read_text())
            require(int(raw[0][0])==sdk_pid, 'SDK diagnostic PID differs from original helper ledger')
            protocol=bytes.fromhex(raw[0][1]).decode('ascii').splitlines()
            errors=1 if mode in ('sdk-error','both-error') else 0
            expected_protocol=['UNISON-DNG-VALIDATION 1','candidate-sha256 '+expected,
              'candidate-size '+str(candidate.stat().st_size),'driver-build synthetic-mixed-v1',
              'structure valid','decode success','raw-digest valid','errors '+str(errors),'warnings 0','END']
            require(protocol==expected_protocol, 'fake verdict bytes differ')
            ext=external_records.parse(log); require(len(ext)==1, 'one metadata helper expected')
            metadata_pid=int(metadata.with_suffix('.calls').read_text())
            meta_ok=mode not in ('metadata-error','both-error')
            require(ext[0].pid==metadata_pid and ext[0].status==('exit',0 if meta_ok else 7)
                    and ext[0].outcome=='completed' and ext[0].other_members==0, 'metadata helper binding/settlement differs')
            expected_closed=f'MIXED_CLOSED owner={out["client_cleanup"]["pid"]} sdk-ok={str(errors==0).lower()} metadata-ok={str(meta_ok).lower()} hashes-ok=true hashes=16 cpu=0 children=0 pending=0 running=0 fd-baseline=true'
            require(log.count(expected_closed)==1, 'exact mixed closed accounting absent')
            independent=audit_mixed(out,command=out['command'],metadata_version='synthetic-only',expected_helpers=dict(sdk=sdk_pid,metadata=metadata_pid),require_admission=True)
            require(independent['functional_status']==('PASSED' if mode=='pass' else 'FAILED'),'independent verdict differs')
            after=tuple(getattr(os.lstat(candidate),n) for n in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink','st_uid'))
            require(before==after and sha(candidate)==expected, 'original private candidate changed')
            cases.append(dict(mode=mode,owner_pid=out['client_cleanup']['pid'],sdk_pid=sdk_pid,
                              metadata_pid=metadata_pid,sdk_accepted=errors==0,metadata_accepted=meta_ok,
                              worker_hashes=16,closed_record=expected_closed,outcome=out,independent_audit=independent,
                              fake_driver_sha256=sha(sdk),fake_metadata_sha256=sha(metadata)))
        except BaseException as error:
            raise UnresolvedOwnership('mixed child evidence unresolved: '+repr(error)) from error
        print('PASS mixed fake-only '+mode,flush=True)
    # Same production graph/private harness with ONLY the configured budget
    # lowered below the envelope: no candidate open/helper may follow refusal.
    original=(ROOT/'tests/mixed_validation/probe.ml').read_text()
    require(original.count('"semanticpayloadbudget=6144"')==1,'exact refusal participant anchor required')
    (work/'refused.ml').write_text(original.replace('"semanticpayloadbudget=6144"','"semanticpayloadbudget=512"'))
    rejected_build=run([build['compiler'],*flags,'unix.cmxa','str.cmxa',*[src/m for m in modules],
                       *[src/n for n in native],'refused.ml','-o','refused'],work)
    require(rejected_build['returncode']==0,rejected_build['stderr'])
    directory=work/'admission-refused';directory.mkdir(mode=0o700)
    candidate=directory/'private.dng';candidate.write_bytes(b'original pre-admission control')
    sdk=directory/'validator.py';metadata=directory/'metadata.py'
    shutil.copyfile(work/'pass/validator.py',sdk);shutil.copyfile(work/'pass/metadata.py',metadata)
    sdk.chmod(0o700);metadata.chmod(0o700)
    refused=run([work/'refused',sdk,metadata,candidate,sha(sdk),'synthetic-mixed-v1',sha(candidate),str(candidate.stat().st_size)],directory)
    expected_refusal=f'MIXED_ADMISSION_REFUSED owner={refused["client_cleanup"]["pid"]} transactions=0 pending=0 payload=0 descriptors=0 fd-baseline=true before-candidate-open=true'
    require(refused['returncode']==2 and refused['stdout'].strip()==expected_refusal
            and not refused['stderr'] and not sdk.with_suffix('.calls').exists()
            and not metadata.with_suffix('.calls').exists(),'pre-helper memory refusal evidence differs')
    print('PASS declared-memory refusal before helpers',flush=True)
    receipt=dict(schema='unison-mixed-validation-controls/1',workspace=str(work),cases=cases,commands=commands,admission_refusal=dict(outcome=refused,participant_source_sha256=sha(work/'refused.ml'),expected=expected_refusal),
      sources={str(p):sha(p) for p in [ROOT/'tests/mixed_validation/probe.ml',Path(__file__),ROOT/'tests/mixed_validation/audit.py',ROOT/'tests/supervised_external/external_records.py']},
      objects={str(src/p):sha(src/p) for p in modules+native},build_result_sha256=sha(args.build_result),
      scope='Eight original fake helpers/64worker hashes; no SDK/ExifTool/Photo/EXIO/native-admission route. Accounting and settlement only, no compute overlap or throughput claim.')
    with args.report.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')


if __name__=='__main__':
    try: main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print('MIXED_OWNERSHIP_RETAINED '+repr(error),flush=True))
