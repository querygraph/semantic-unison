#!/usr/bin/env python3
"""Test production Copy.copyClonedRange from a compiler-matched private Make build.

Only the Fs.copy_file call is hooked in a private copy of the complete source.
The native lease, channels, fallback and range function are production code.
Positive step results model ordinary native copying; no block sharing is claimed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
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
module BoundNativeTest = struct
  let calls = ref []
  let hook = ref Fs.copy_file
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
external native : Unix.file_descr -> Unix.file_descr -> int64 -> int -> int = "bound_copy_native"
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
        else raise(Unix.Unix_error(Unix.ENOSYS,"injected native","fixture")));
      invoke lease;inspect length;
      check(List.length(calls())=(if prefix=0 then 1 else 2)) "Unsupported was retried instead of exact fallback";
      check(LargeFile.pos_in input=Int64.of_int(so+length) && LargeFile.pos_out output=Int64.of_int(doff+length))
        "fallback channel positions incorrect")) [0;3]);
  test "quiet bounded fallback EOF after in-step source truncation fails"(fun()->
    fixture directory(fun owner s d writer _ _ _ _ _ so _ _ _ inspect calls invoke->
      let lease=enroll owner s d in
      N.hook:=(fun _ _ _ _->Unix.LargeFile.ftruncate writer(Int64.of_int(so+3));
        raise(Unix.Unix_error(Unix.ENOSYS,"injected native","fixture")));
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
      let lease=enroll owner s d in N.hook:=(fun _ _ _ _->if result=99 then length else result);
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
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = args.build.resolve() / 'src'
    for name in ['copy.ml', 'copyRange.ml', 'cloneRange.ml', 'cloneLease.ml', 'fileObservation.ml', 'fileObservation_stubs.c', 'uutil.ml']:
        data = (root / 'src' / name).read_bytes()
        assert (build / name).read_bytes() == data, name + ' differs from current frozen source; refresh the Make snapshot'
        print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
    source = (root / 'src/copy.ml').read_text()
    needle = 'Fs.copy_file src dst source_offset length'
    assert source.count(needle) == 1, 'native seam no longer unambiguous'
    instrumented = HOOK + source.replace(needle, 'BoundNativeTest.step src dst source_offset length')
    if args.negative_control:
        repair = 'LargeFile.seek_out output ending;'
        assert instrumented.count(repair) == 1
        instrumented = instrumented.replace(repair, '(); (* negative control: cached offset not reconciled *)')
    makefile = (build / 'Makefile.OCaml').read_text()
    modules = objects(makefile, 'OCAMLOBJS')
    modules = modules[:modules.index('copy.cmx')]
    includes = [build, build / 'lwt', build / 'ubase', build / 'system', build / 'system/generic', build / 'lwt/generic']
    flags = [flag for path in includes for flag in ['-I', str(path)]] + ['-I', '+unix', '-I', '+str']
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    with tempfile.TemporaryDirectory(prefix='unison-bound-copy-', dir='/private/tmp') as tmp:
        work = Path(tmp)
        (work / 'copyForTest.ml').write_text(instrumented)
        (work / 'boundTest.ml').write_text(HARNESS)
        (work / 'nativeStep.c').write_text(NATIVE)
        state = work / 'state'
        state.mkdir()
        environment['UNISON'] = str(state)
        print('Compiler', subprocess.check_output([args.ocamlopt, '-version'], env=environment, text=True).strip(), flush=True)
        with (work / 'build.log').open('w+') as log:
            try:
                for name in ['nativeStep.c', 'copyForTest.ml']:
                    subprocess.run([args.ocamlopt, *flags, '-c', name], cwd=work, env=environment,
                                   stdout=log, stderr=log, check=True)
                subprocess.run([args.ocamlopt, *flags, 'unix.cmxa', 'str.cmxa',
                                *[str(build / name) for name in modules], 'copyForTest.cmx', 'boundTest.ml',
                                *[str(build / name) for name in objects(makefile, 'COBJS')],
                                'nativeStep.o', '-o', 'bound-copy-test'], cwd=work, env=environment,
                               stdout=log, stderr=log, check=True)
            except subprocess.CalledProcessError:
                log.seek(0)
                print(log.read())
                raise
        result = subprocess.run([str(work / 'bound-copy-test'), str(work)], cwd=work,
                                env=environment, text=True, capture_output=True, timeout=90)
        print(result.stdout, end='')
        print(result.stderr, end='')
        if args.negative_control:
            assert result.returncode != 0 and 'cached offset disagrees' in result.stderr, 'negative control did not detect missing reconciliation'
            print('PASS negative control: removing channel reconciliation is detected')
        else:
            result.check_returncode()


if __name__ == '__main__':
    main()
