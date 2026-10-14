#!/usr/bin/env python3
"""Test production Copy.copyClonedRange from a compiler-matched private Make build.

Only the Fs.copy_file_status call is hooked in a private copy of the complete source.
The native lease, channels, fallback and range function are production code.
Positive step results model ordinary native copying; no block sharing is claimed.
The legacy copy_file primitive is poisoned in the private Fs namespace so an
accidental production routing regression cannot silently pass.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

NATIVE = r'''
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/signals.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <unistd.h>
CAMLprim value bound_copy_native(value source, value destination, value offset, value length)
{
  CAMLparam4(source,destination,offset,length);
  int s=Int_val(source),d=Int_val(destination),saved=0;
  off_t position=Int64_val(offset);
  size_t wanted=Long_val(length),done=0;
  char bytes[65536];
  caml_enter_blocking_section_no_pending();
  while(done<wanted) {
    size_t n=wanted-done;
    if(n>sizeof(bytes)) n=sizeof(bytes);
    ssize_t got=pread(s,bytes,n,position+done);
    if(got<0 && errno==EINTR) continue;
    if(got<=0) {if(got<0) saved=errno;break;}
    size_t written=0;
    while(written<(size_t)got) {
      ssize_t count=write(d,bytes+written,got-written);
      if(count<0 && errno==EINTR) continue;
      if(count<=0) {saved=count<0?errno:EIO;break;}
      written+=count;
    }
    done+=written;
    if(saved) break;
  }
  caml_leave_blocking_section();
  if(saved) unix_error(saved,"fixture native step",Nothing);
  CAMLreturn(Val_long(done));
}
'''

HOOK = r'''
module LegacyRangePoison = struct let calls = ref 0 end
module Fs = struct
  include Fs
  let copy_file _ _ _ _ =
    incr LegacyRangePoison.calls;failwith "legacy copy_file route reached"
end
module BoundNativeTest = struct
  let calls = ref []
  let hook = ref Fs.copy_file_status
  let step source destination offset length =
    let output_position=Unix.LargeFile.lseek destination 0L Unix.SEEK_CUR in
    calls := (offset,length,output_position)::!calls;
    (!hook) source destination offset length
end
'''

HARNESS = r'''
module Copy = CopyForTest
module N = Copy.BoundNativeTest
module L = CloneLease
module F = FileObservation
external native_bytes : Unix.file_descr -> Unix.file_descr -> int64 -> int -> int = "bound_copy_native"
let native_progress n = (0,n,1,3,None,1,0,0L)
let native s d off n = native_progress (native_bytes s d off n)
let unavailable () = (1,0,0,0,None,0,1,0L)
let check yes why=if not yes then failwith why
let count=ref 0 and serial=ref 0
let test name body=(try body() with e->Printf.eprintf "FAIL %s\n%!" name;raise e);incr count;Printf.printf "PASS %s\n%!" name
let chunk=10_485_760
let fds()=Array.length(Sys.readdir "/dev/fd")
let bytes path=let c=open_in_bin path in Fun.protect ~finally:(fun()->close_in c)(fun()->really_input_string c(in_channel_length c))
let write_all fd text=let rec loop offset=if offset<String.length text then
  let n=Unix.write_substring fd text offset(String.length text-offset) in check(n>0) "fixture write stopped";loop(offset+n) in loop 0
let transient=function Util.Transient _->true|_->false
let failure expected body=try body();failwith "copy reported success despite injected failure"
  with e->if not(expected e) then raise e
let source_pattern length=String.init length(fun i->Char.chr((i*73+19) land 255))
let fixture directory ?(length=24) body=
  incr serial;
  let name stem=Filename.concat directory(stem^string_of_int !serial) in
  let sp=name "source-" and dp=name "stage-" and live=name "live-" in
  let source_offset=17 and destination_offset=11 in
  let basis=source_pattern(source_offset+length+37) in
  let writer=Unix.openfile sp[Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC]0o600 in
  write_all writer basis;
  let input=open_in_bin sp in
  let destination=Unix.openfile dp[Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC]0o600 in
  let target=destination_offset+length+31 in
  Unix.LargeFile.ftruncate destination(Int64.of_int target);
  write_all destination(String.make target '#');ignore(Unix.LargeFile.lseek destination 0L Unix.SEEK_SET);
  let output=Unix.out_channel_of_descr destination in
  output_string output(String.make destination_offset '#');
  let old=open_out_bin live in output_string old "OLD LIVE DESTINATION";close_out old;
  let source=Unix.descr_of_in_channel input in
  let owner=L.create_owner ~instance_id:("bound-copy-owner-"^string_of_int !serial) in
  N.calls:=[];N.hook:=native;
  let inspect completed=
    flush output;
    let actual=bytes dp in
    check(String.length actual=target) "private output EOF changed";
    for i=0 to target-1 do
      let expected=if i>=destination_offset && i<destination_offset+completed
        then basis.[source_offset+i-destination_offset] else '#' in
      check(actual.[i]=expected) "range bytes or immediate outer sentinels differ"
    done;
    check(bytes live="OLD LIVE DESTINATION") "old live destination changed" in
  let calls()=List.rev !N.calls in
  let invoke lease=Copy.copyClonedRange lease input output(Int64.of_int source_offset)(Int64.of_int length) in
  Fun.protect ~finally:(fun()->
    L.close_owner owner;close_in_noerr input;close_out_noerr output;Unix.close writer;
    List.iter(fun p->if Sys.file_exists p then Unix.unlink p)[sp;dp;live])
    (fun()->body owner source destination writer input output sp dp basis source_offset destination_offset length target inspect calls invoke)
let enroll ?observe owner source destination=match L.enroll ?observe owner ~backend_revision:"bound-native-step-fixture/1" ~source ~destination with
  | Ok x->x|Error e->raise e

let ()=
  let directory=Sys.argv.(1) in
  let initial=fds() in
  test "production caller copies shifted multi-10MiB chunks and reconciles cached channel offsets"(fun()->
    fixture directory ~length:(2*chunk+37)(fun owner s d _ input output sp _ basis so doff length _ inspect calls invoke->
      let lease=enroll owner s d in
      ignore(LargeFile.seek_in input 3L);invoke lease;
      inspect length;
      check(calls()=[Int64.of_int so,chunk,Int64.of_int doff;
                     Int64.of_int(so+chunk),chunk,Int64.of_int(doff+chunk);
                     Int64.of_int(so+2*chunk),37,Int64.of_int(doff+2*chunk)]) "bounded native offsets/counts differ";
      check(LargeFile.pos_out output=Int64.of_int(doff+length) &&
            Unix.LargeFile.lseek d 0L Unix.SEEK_CUR=Int64.of_int(doff+length)) "output cached offset disagrees with native fd";
      check(bytes sp=basis) "immutable source changed";
      L.invalidate lease));
  test "short native progress advances source and fd positions exactly once"(fun()->
    fixture directory(fun owner s d _ _ output _ _ _ so doff length _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun s d off n->native s d off(if List.length !N.calls=1 then 3 else n));
      invoke lease;inspect length;
      check(calls()=[Int64.of_int so,length,Int64.of_int doff;
                     Int64.of_int(so+3),length-3,Int64.of_int(doff+3)]) "short native prefix was repeated/skipped";
      check(LargeFile.pos_out output=Int64.of_int(doff+length)) "short native progress left cached offset stale"));
  test "Unsupported before/after native prefix copies only exact suffix"(fun()->
    List.iter(fun prefix->fixture directory(fun owner s d _ input output _ _ _ so doff length _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun s d off _->if prefix>0 && List.length !N.calls=1 then native s d off prefix
        else unavailable());
      invoke lease;inspect length;
      check(List.length(calls())=(if prefix=0 then 1 else 2)) "Unsupported was retried instead of exact fallback";
      check(LargeFile.pos_in input=Int64.of_int(so+length) && LargeFile.pos_out output=Int64.of_int(doff+length))
        "fallback channel positions incorrect")) [0;3]);
  test "quiet bounded fallback EOF after in-step source truncation fails"(fun()->
    fixture directory(fun owner s d writer _ _ _ _ _ so _ _ _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun _ _ _ _->Unix.LargeFile.ftruncate writer(Int64.of_int(so+3));
        unavailable());
      failure transient(fun()->invoke lease);inspect 3;
      check(List.length(calls())=1) "quiet EOF caused retry or successful full-copy claim"));
  test "EIO/ENOSPC before or after short prefix preserve errno/context and never fallback"(fun()->
    List.iter(fun errno->List.iter(fun prefix->fixture directory(fun owner s d _ _ _ _ _ _ _ _ _ _ inspect calls invoke->
      let lease=enroll owner s d in
      let thrown=Unix.Unix_error(errno,"injected native","fixture") in
      N.hook:=(fun s d off _->if prefix>0 && List.length !N.calls=1 then native s d off prefix else raise thrown);
      failure(fun e->e=thrown)(fun()->invoke lease);inspect prefix;
      check(List.length(calls())=(if prefix=0 then 1 else 2)) "operational failure retried as fallback")) [0;3]) [Unix.EIO;Unix.ENOSPC]);
  test "zero/negative/oversized native progress and unadvanced fd never report full copy"(fun()->
    List.iter(fun result->fixture directory(fun owner s d _ _ _ _ _ _ _ _ length _ inspect calls invoke->
      let lease=enroll owner s d in N.hook:=(fun _ _ _ _->native_progress (if result=99 then length else result));
      failure transient(fun()->invoke lease);inspect 0;
      check(List.length(calls())=1) "invalid progress was retried")) [0;-1;25;99]);
  test "missing identity, stale bounds and revoked epoch prevent all native effects"(fun()->
    List.iter(fun fault->fixture directory(fun owner s d writer _ _ _ _ _ _ _ _ _ inspect calls invoke->
      let missing=ref false in
      let observe fd=let o=F.observe fd in
        if !missing && fd=(if fault="destuuid" then d else s) && fault<>"destid" then {o with F.volume_uuid=None}
        else if !missing && fault="destid" && fd=d then {o with F.file_id="0000000000000000"} else o in
      let lease=enroll ~observe owner s d in
      (match fault with "uuid"|"destuuid"|"destid"->missing:=true|"size"->Unix.LargeFile.ftruncate writer 191L
       |"owner"->L.invalidate_owner owner|_->L.invalidate lease);
      failure transient(fun()->invoke lease);inspect 0;
      check(calls()=[]) "invalid binding reached native step/fallback")) ["uuid";"destuuid";"destid";"size";"owner";"lease"]);
  test "binding and epoch changes after one complete 10MiB operation stop before next step"(fun()->
    List.iter(fun fault->fixture directory ~length:(chunk+37)(fun owner s d writer _ _ _ _ _ _ _ _ _ inspect calls invoke->
      let missing=ref false in
      let observe fd=let o=F.observe fd in
        if !missing && fd=(if fault="destuuid" then d else s) && fault<>"destid" then {o with F.volume_uuid=None}
        else if !missing && fault="destid" && fd=d then {o with F.file_id="0000000000000000"} else o in
      let lease=enroll ~observe owner s d in
      N.hook:=(fun s d off n->let copied=native s d off n in
        (match fault with "uuid"|"destuuid"|"destid"->missing:=true|"size"->Unix.LargeFile.ftruncate writer(Int64.of_int(17+chunk))
         |"owner"->L.invalidate_owner owner|_->L.invalidate lease);copied);
      failure transient(fun()->invoke lease);inspect chunk;
      check(List.length(calls())=1) "changed binding/epoch was used for another operation")) ["uuid";"destuuid";"destid";"size";"owner";"lease"]);
  test "mismatched channel descriptors fail before native effects"(fun()->
    fixture directory(fun owner s d _ input output sp _ _ so _ length _ inspect calls _->
      let lease=enroll owner s d in let other=open_in_bin sp in
      Fun.protect ~finally:(fun()->close_in other)(fun()->
        failure transient(fun()->Copy.copyClonedRange lease other output(Int64.of_int so)(Int64.of_int length));
        inspect 0;check(calls()=[]) "different input channel fd reached native step");
      let other=Unix.out_channel_of_descr(Unix.dup d) in
      Fun.protect ~finally:(fun()->close_out_noerr other)(fun()->
        failure transient(fun()->Copy.copyClonedRange lease input other(Int64.of_int so)(Int64.of_int length));
        inspect 0;check(calls()=[]) "different output channel fd reached native step")));
  test "strict known in-call decline copies only its exact suffix"(fun()->
    fixture directory(fun owner s d _ input output _ _ _ so doff length _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun s d off _->ignore(native_bytes s d off 3);(1,3,1,3,Some Unix.EOPNOTSUPP,1,3,95L));
      invoke lease;inspect length;
      check(List.length(calls())=1) "known decline was probed again";
      check(LargeFile.pos_in input=Int64.of_int(so+length) &&
            LargeFile.pos_out output=Int64.of_int(doff+length)) "in-call prefix fallback skipped/repeated bytes"));
  test "strict errno-looking returned errors cannot authorize suffix copying"(fun()->
    List.iter(fun errno->List.iter(fun prefix->fixture directory(fun owner s d _ _ _ _ _ _ _ _ _ _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun s d off _->if prefix>0 then ignore(native_bytes s d off prefix);
        (2,prefix,1,3,Some errno,(if prefix=0 then 0 else 1),0,22L));
      failure(function Unix.Unix_error(actual,"copy_file_status",context)->
        actual=errno && String.length context>0|_->false)(fun()->invoke lease);
      inspect prefix;check(List.length(calls())=1) "operational result caused native retry/fallback")) [0;3])
      [Unix.EINVAL;Unix.ESPIPE;Unix.ENOTSOCK;Unix.EBADF;Unix.EIO;Unix.ENOSPC;
       Unix.EUNKNOWNERR(-50);Unix.EUNKNOWNERR(-1)]);
  test "strict indeterminate decline leaves its unknown extra byte without fallback"(fun()->
    fixture directory(fun owner s d _ _ _ _ _ _ _ _ _ _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun s d off _->ignore(native_bytes s d off 4);
        (1,3,1,3,Some Unix.EOPNOTSUPP,2,3,95L));
      failure(function Unix.Unix_error(Unix.EOPNOTSUPP,"copy_file_status",_)->true|_->false)(fun()->invoke lease);
      inspect 4;check(List.length(calls())=1) "indeterminate effects led to new work"));
  test "strict malformed raw statuses fail before fallback"(fun()->
    List.iter(fun raw->fixture directory(fun owner s d _ _ _ _ _ _ _ _ _ _ inspect calls invoke->
      let lease=enroll owner s d in N.hook:=(fun _ _ _ _->raw);
      failure transient(fun()->invoke lease);inspect 0;
      check(List.length(calls())=1) "malformed raw receipt retried"))
      [(9,0,1,3,None,0,0,0L);(1,0,1,3,Some Unix.EINVAL,0,3,22L);
       (0,3,1,3,None,0,0,0L);(0,3,1,3,None,2,0,0L)]);
  test "production copyFile bounds declined suffix despite extra source bytes"(fun()->
    List.iter(fun prefix->fixture directory(fun _ _ _ _ input output _ dp _ so doff length _ inspect calls _->
      let fallback_lengths=ref [] in
      N.hook:=(fun s d off _->if prefix>0 && List.length !N.calls=1 then native s d off prefix
        else unavailable());
      Copy.copyFile input output (`DATA_APPEND(Uutil.Filesize.ofInt so))
        (Uutil.Filesize.ofInt length)
        (fun remaining->fallback_lengths:=Uutil.Filesize.toInt64 remaining::!fallback_lengths;
          Uutil.readWriteBounded input output remaining(fun _->())) (fun _->());
      let cursors_correct=LargeFile.pos_out output=Int64.of_int(doff+length) &&
        Unix.LargeFile.lseek (Unix.descr_of_out_channel output) 0L Unix.SEEK_CUR=Int64.of_int(doff+length) in
      inspect length;
      check cursors_correct "copyFile returned with stale cached or native destination cursor";
      check(!fallback_lengths=[Int64.of_int(length-prefix)] && List.length(calls())=(if prefix=0 then 1 else 2))
        "production copyFile requested its original length after a prefix";
      check(LargeFile.pos_in input=Int64.of_int(so+length) &&
            LargeFile.pos_out output=Int64.of_int(doff+length)) "copyFile cursor reconciliation failed";
      output_string output "!";flush output;
      let chained=bytes dp in
      check(chained.[doff+length]='!' && chained.[doff+length+1]='#')
        "a following literal overwrote the completed suffix")) [0;3]);
  check(!(Copy.LegacyRangePoison.calls)=0) "production used the legacy native range API";
  Gc.full_major();check(fds()=initial) "bound caller fixture leaked descriptors";
  Printf.printf "Copy.copyClonedRange: %d production-caller cases passed; no physical-sharing claim\n%!" !count
'''


def objects(makefile, name):
    match = re.search(r'^' + name + r' = (.*?)(?=\n\n)', makefile, re.M | re.S)
    if match is None:
        raise RuntimeError('missing Make object list: ' + name)
    body = match.group(1).replace('\\\n', ' ').replace('$(SYSTEM)', 'generic')
    body = body.replace('$(WINOBJS)', '').replace('$(WINCOBJS)', '')
    return body.replace('$(OBJ_EXT)', '.o').replace('.cmo', '.cmx').split()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path, help='compiler-matched isolated Make snapshot')
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--negative-control', action='store_true', help='prove missing channel reconciliation fails the suite')
    parser.add_argument('--negative-suffix-control', action='store_true', help='prove original-length suffix copying fails independent sentinels')
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = args.build.resolve() / 'src'
    source_pins = {}
    for name in ['copy.ml', 'copyRange.ml', 'copyRange.mli', 'nativeCopyRange_stubs.c', 'fs.ml',
                 'cloneRange.ml', 'cloneLease.ml', 'fileObservation.ml', 'fileObservation_stubs.c', 'uutil.ml']:
        data = (root / 'src' / name).read_bytes()
        assert (build / name).read_bytes() == data, name + ' differs from current frozen source; refresh the Make snapshot'
        source_pins['src/' + name] = hashlib.sha256(data).hexdigest()
        print('source', name, source_pins['src/' + name], flush=True)
    source_pins['tests/test_clone_bound_range.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    source = (root / 'src/copy.ml').read_text()
    needle = 'Fs.copy_file_status src dst source_offset length'
    assert source.count(needle) == 1, 'native seam no longer unambiguous'
    instrumented = HOOK + source.replace(needle, 'BoundNativeTest.step src dst source_offset length')
    if args.negative_control:
        repair = 'LargeFile.seek_out output ending;'
        assert instrumented.count(repair) == 1
        instrumented = instrumented.replace(repair, '(); (* negative control: cached offset not reconciled *)')
    if args.negative_suffix_control:
        if args.negative_control:
            parser.error('choose only one private negative control')
        repair = ('fallback (Filesize.ofInt64\n'
                  '          (Int64.sub (Filesize.toInt64 len) (Filesize.toInt64 copied)))')
        assert instrumented.count(repair) == 1, 'bounded suffix seam no longer unique'
        instrumented = instrumented.replace(repair, 'fallback len (* negative control: original length repeats prefix *)')
    makefile = (build / 'Makefile.OCaml').read_text()
    modules = objects(makefile, 'OCAMLOBJS')
    modules = modules[:modules.index('copy.cmx')]
    includes = [build, build / 'lwt', build / 'ubase', build / 'system', build / 'system/generic', build / 'lwt/generic']
    flags = [flag for path in includes for flag in ['-I', str(path)]] + ['-I', '+unix', '-I', '+str']
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    work = Path(tempfile.mkdtemp(prefix='unison-bound-copy-', dir='/private/tmp'))
    records = []
    receipt = {'schema': 1, 'work': str(work), 'retained': args.keep_work,
               'production_build': str(build.parent), 'source_pins': source_pins,
               'commands': records, 'success': False, 'physical_sharing': False,
               'private_instrumentation': ['replace only Fs.copy_file_status call with BoundNativeTest.step',
                                           'poison legacy copy_file in private Fs namespace'],
               'Photo_or_Adobe_access': False}

    def run(command, name, *, allow_failure=False, timeout=90):
        result = subprocess.run(command, cwd=work, env=environment, text=True,
                                capture_output=True, timeout=timeout)
        log = work / (name + '.log')
        log.write_text(result.stdout + result.stderr)
        records.append({'command': command, 'cwd': str(work), 'exit': result.returncode,
                        'log': str(log), 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
        print(result.stdout, end='', flush=True)
        print(result.stderr, end='', flush=True)
        if not allow_failure:
            result.check_returncode()
        return result

    try:
        (work / 'copyForTest.ml').write_text(instrumented)
        (work / 'boundTest.ml').write_text(HARNESS)
        (work / 'nativeStep.c').write_text(NATIVE)
        state = work / 'state'
        state.mkdir()
        environment['UNISON'] = str(state)
        compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
        receipt['compiler'] = {'path': str(compiler),
                               'sha256': hashlib.sha256(compiler.read_bytes()).hexdigest(),
                               'version': run([args.ocamlopt, '-version'], 'compiler-version').stdout.strip()}
        for name in ['nativeStep.c', 'copyForTest.ml']:
            run([args.ocamlopt, *flags, '-c', name], 'compile-' + name)
        linked = [build / name for name in modules] + [build / name for name in objects(makefile, 'COBJS')]
        receipt['linked_objects'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in linked}
        run([args.ocamlopt, *flags, 'unix.cmxa', 'str.cmxa',
             *[str(build / name) for name in modules], 'copyForTest.cmx', 'boundTest.ml',
             *[str(build / name) for name in objects(makefile, 'COBJS')],
             'nativeStep.o', '-o', 'bound-copy-test'], 'link')
        result = run([str(work / 'bound-copy-test'), str(work)], 'test',
                     allow_failure=(args.negative_control or args.negative_suffix_control))
        if args.negative_control:
            assert result.returncode != 0 and 'cached offset disagrees' in result.stderr, 'negative control did not detect missing reconciliation'
            print('PASS negative control: removing channel reconciliation is detected')
            receipt['negative_control'] = {'kind': 'channel-reconciliation', 'detected': True}
        elif args.negative_suffix_control:
            assert result.returncode != 0 and 'range bytes or immediate outer sentinels differ' in result.stderr, 'negative control did not detect original-length suffix overcopy'
            print('PASS negative control: original-length suffix copying is detected')
            receipt['negative_control'] = {'kind': 'original-length-suffix', 'detected': True}
        else:
            result.check_returncode()
            receipt['named_groups'] = sum(line.startswith('PASS ') for line in result.stdout.splitlines())
        receipt['success'] = True
    finally:
        receipt['artifacts'] = {str(path.relative_to(work)): {'path': str(path), 'bytes': path.stat().st_size,
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work / 'receipt.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print('Receipt', target, flush=True)
        print('Artifacts', work, '(retained)' if args.keep_work else '(removed after receipt)', flush=True)
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
