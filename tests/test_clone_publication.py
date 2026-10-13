#!/usr/bin/env python3
"""Qualify actual Copy receiver publication and reference-FD handoffs.

Requires a compiler-matched isolated Make snapshot. The entire frozen Copy.ml
is compiled privately, with fault hooks at existing ownership handoffs and an
in-process transport delivering production rsync tokens. Native clone creation,
publication, leases, channels and EOF handling remain production code. Private
native syscall wrappers are reused from the independently qualified native
fixtures. All data and generated objects are disposable; no sharing/performance
or final live-file commit claim is made.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


HOOK = r'''
module PublicationFault = struct
  exception Injected
  let target = ref ""
  let error : exn ref = ref Injected
  let action = ref (fun (_ : string) -> ())
  let events = ref []
  let captured : Unix.file_descr list ref = ref []
  let names : (string * string * string) option ref = ref None
  let creates = ref 0
  let packets = ref 0
  let hit phase =
    events := phase :: !events;
    (!action) phase;
    if phase = !target then raise !error
  let wrap phase f = hit phase; f ()
  let resource label resource =
    {resource with Remote.register = (fun value ->
      hit (label ^ "-before");
      let registered = resource.Remote.register value in
      hit (label ^ "-after"); registered)}
  let reset () =
    target := ""; error := Injected; action := (fun _ -> ());
    events := []; captured := []; names := None; creates := 0; packets := 0
  let compress_local receive _ ((bi, directory, path, kind), (length, _, file_id)) =
    if kind <> `DATA then failwith "fixture only transmits regular DATA";
    let input = Fs.open_in_bin (Fspath.concat directory path) in
    Lwt.catch
      (fun () ->
        let compress = match bi with
          | Some signatures -> Transfer.Rsync.rsyncCompress signatures input length (fun _ -> ())
          | None -> Transfer.send input length (fun _ -> ()) in
        Lwt.bind (compress (fun instruction ->
          incr packets; receive (file_id, instruction); Lwt.return ()))
          (fun () -> close_in input; Lwt.return ()))
      (fun error -> close_in_noerr input; Lwt.fail error)
end
module Fs = struct
  include Fs
  let clone_stage_handles source destination =
    incr PublicationFault.creates;
    PublicationFault.hit "create-before";
    let result = Fs.clone_stage_handles source destination in
    (match result with
     | Shared_stage_handles (basis, output, parent) ->
         PublicationFault.captured := basis :: output :: parent :: !PublicationFault.captured
     | Declined_stage_handles _ -> ());
    result
  let openfile path flags mode =
    let fd = Fs.openfile path flags mode in
    PublicationFault.captured := fd :: !PublicationFault.captured;
    fd
end
module StagePublication = struct
  include StagePublication
  let prepare ~working_dir ~stage ~temporary =
    PublicationFault.names := Some (working_dir, stage, temporary);
    PublicationFault.hit "prepare-before";
    StagePublication.prepare ~working_dir ~stage ~temporary
  let adopt context ~parent ~stage =
    PublicationFault.hit "adopt-before";
    StagePublication.adopt context ~parent ~stage;
    PublicationFault.hit "adopt-after"
  let publish context =
    PublicationFault.hit "publish-before";
    StagePublication.publish context;
    PublicationFault.hit "publish-after"
  let disarm context =
    PublicationFault.hit "disarm-before";
    StagePublication.disarm context;
    PublicationFault.hit "disarm-after"
end
'''


NATIVE = r'''
#include <caml/mlvalues.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <fcntl.h>
CAMLprim value publication_reference_flags(value descriptor)
{
  int fd = Int_val(descriptor), flags = fcntl(fd, F_GETFL), exec = fcntl(fd, F_GETFD);
  if (flags == -1 || exec == -1) unix_error(errno, "fixture reference flags", Nothing);
  return Val_int(((exec & FD_CLOEXEC) ? 1 : 0) |
                 ((flags & O_NONBLOCK) ? 2 : 0) |
                 (((flags & O_ACCMODE) == O_RDONLY) ? 4 : 0));
}
'''


HARNESS = r'''
module Copy = CopyForPublication
module H = Copy.PublicationFault
external attribute_fault : int -> int -> unit = "stage_publication_fixture_attribute_fault"
external rename_fault : int -> unit = "stage_publication_fixture_rename_fault"
external handles_mode : int -> unit = "handles_fixture_mode"
external handles_paths : string -> string -> unit = "handles_fixture_paths"
external fd_count : unit -> int = "stage_publication_fixture_fd_count" [@@noalloc]
external reference_flags : Unix.file_descr -> int = "publication_reference_flags"
let check condition message = if not condition then failwith message
let serial = ref 0 and cases = ref 0
let write path text =
  let fd = Unix.openfile path [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    let rec loop offset = if offset < String.length text then begin
      let n = Unix.write_substring fd text offset (String.length text-offset) in
      check (n > 0) "fixture write stopped"; loop (offset+n)
    end in loop 0)
let read path =
  let channel = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in channel)
    (fun () -> really_input_string channel (in_channel_length channel))
let exists path = try ignore (Unix.lstat path); true with Unix.Unix_error (Unix.ENOENT,_,_) -> false
let closed fd = try ignore (Unix.fstat fd); false with Unix.Unix_error (Unix.EBADF,_,_) -> true
let rec remove path = match (Unix.lstat path).Unix.st_kind with
  | Unix.S_DIR -> Array.iter (fun name -> remove (Filename.concat path name)) (Sys.readdir path); Unix.rmdir path
  | _ -> Unix.unlink path
  | exception Unix.Unix_error (Unix.ENOENT,_,_) -> ()
let transient = function Util.Transient _ -> true | _ -> false
let contains text fragment =
  let rec loop n = n + String.length fragment <= String.length text &&
    (String.sub text n (String.length fragment) = fragment || loop (n+1)) in loop 0
let fail_expected expected body =
  match body () with
  | () -> failwith "injected rejection reported success"
  | exception error -> if not (expected error) then raise error
let no_native_creation () = check (!(H.creates)=0) "decline/error reached native stage creation"
let names () = match !(H.names) with
  | Some (root, stage, temporary) -> Filename.concat root stage, Filename.concat root temporary
  | None -> failwith "publication preparation was not attempted"
let identity_failure phase error =
  match error with
  | Util.Transient message -> contains message phase
  | Unix.Unix_error (_, actual, _) -> contains actual phase
  | _ -> false
let reset () = H.reset (); attribute_fault 0 0; rename_fault 0; handles_mode 0; Abort.reset ()
let negative = Array.length Sys.argv > 2 && Sys.argv.(2)="negative"
let test name body = if negative && name<>"post-adoption clone-out-channel failure=exception" then () else begin
  reset ();
  (try body () with error ->
    Printf.eprintf "FAIL %s\nevents: %s\n%!" name (String.concat "," (List.rev !(H.events)));
    raise error);
  incr cases; Printf.printf "PASS %s\n%!" name
end
let reuse_cleanup directory sentinel =
  List.iter (fun fd -> check (closed fd) "caller handoff retained a real descriptor") !(H.captured);
  if !(H.captured) <> [] then begin
    let descriptors = List.init 32 (fun _ -> Unix.openfile sentinel [Unix.O_RDONLY;Unix.O_CLOEXEC] 0) in
    Fun.protect ~finally:(fun () -> List.iter Unix.close descriptors) (fun () ->
      check (List.exists (fun fd -> List.mem fd !(H.captured)) descriptors)
        "reuse negative control did not reuse a captured FD integer";
      Remote.clientCloseRootConnection (Common.Local, directory);
      List.iter (fun fd -> check (not (closed fd)) "later connection cleanup closed a reused descriptor") descriptors)
  end else Remote.clientCloseRootConnection (Common.Local, directory)
let basis = String.init 65_573 (fun i -> Char.chr (((i*73) lxor (i lsr 8) lxor (i lsr 12)) land 255))
let incoming = String.sub basis 8192 (String.length basis-8192) ^ String.sub basis 0 8192
let sentinel = "unrelated namespace sentinel\000\255"
let fixture top ?(followed=false) body =
  incr serial;
  let root = Filename.concat top ("case-" ^ string_of_int !serial) in
  Unix.mkdir root 0o700;
  let path name = Filename.concat root name in
  List.iter (fun name -> Unix.mkdir (path name) 0o700) ["basis";"receiving"];
  write (path "basis/live") basis; write (path "source") incoming;
  write (path "sentinel") sentinel;
  let basis_name, temp_name = if followed then begin
    Unix.symlink "basis" (path "basis-link"); Unix.symlink "receiving" (path "receiving-link");
    "basis-link/live", "receiving-link/normal"
  end else "basis/live", "receiving/normal" in
  let directory = Fspath.canonize (Some root) in
  let normal = path temp_name in
  let source_size = Uutil.Filesize.ofInt (String.length incoming)
  and basis_size = Uutil.Filesize.ofInt (String.length basis) in
  let run () =
    (* This opaque value is never inspected: the sole replaced transport seam
       routes tokens locally and processTransferInstruction ignores conn. *)
    let unused_connection : Remote.connection = Obj.magic 0 in
    Lwt_unix.run (Copy.transferFileContents unused_connection directory (Path.fromString "source")
      directory (Path.fromString temp_name) (Path.fromString basis_name)
      (`Update (basis_size,Uutil.Filesize.zero)) `DATA source_size Uutil.File.dummy) in
  let verify_source () =
    let live = if exists (path "basis-moved/live") then path "basis-moved/live" else path "basis/live" in
    check (read live = basis) "old live basis was modified";
    check (read (path "source") = incoming) "immutable transmitted source was modified";
    check (read (path "sentinel") = sentinel) "unrelated sentinel was modified" in
  let verify_no_stage () =
    match !(H.names) with None -> () | Some (_, stage, _) ->
      check (not (exists (path stage))) "owned clone stage name survived failure/completion";
      let moved = path ("basis-moved/" ^ Filename.basename stage) in
      check (not (exists moved)) "owned stage survived in its captured moved parent" in
  let before = fd_count () in
  Fun.protect ~finally:(fun () ->
    attribute_fault 0 0; rename_fault 0; handles_mode 0; H.target := ""; H.action := (fun _ -> ());
    Remote.clientCloseRootConnection (Common.Local,directory); remove root)
    (fun () ->
      body directory path normal run verify_source verify_no_stage;
      verify_source ();
      reuse_cleanup directory (path "sentinel");
      check (fd_count () = before) "receiver fixture leaked native/channel descriptors")
let successful normal run verify_no_stage =
  run (); check (read normal = incoming) "receiver EOF published incorrect rsync bytes";
  check (!(H.creates)=1 && !(H.packets)>0) "receiver did not exercise native clone and real rsync tokens";
  check (List.mem "publish-after" !(H.events) && List.mem "disarm-after" !(H.events))
    "caller did not publish then disarm";
  verify_no_stage ()
let () =
  let top = Sys.argv.(1) in
  if not (StagePublication.available ()) then exit 77;
  Features.setEnabled (Features.all ());
  Prefs.loadStrings ["clone = require";"rsync = true";"dontchmod = false"];
  Lwt_unix.run (Lwt.return ());
  test "receiver EOF publishes between distinct parents with followed directory ancestry" (fun () ->
    fixture top ~followed:true (fun _ _ normal run _ no_stage -> successful normal run no_stage));
  (* Native valid missing/zero UUID and unsupported identity syscalls at each
     preparation observation must decline before any stage exists, only auto. *)
  List.iter (fun mode -> List.iter (fun trigger -> List.iter (fun policy ->
    test (Printf.sprintf "preparation unavailable mode=%d observation=%d policy=%s" mode trigger policy) (fun () ->
      Prefs.loadStrings ["clone = " ^ policy];
      fixture top (fun _ _ normal run _ no_stage ->
        attribute_fault mode trigger;
        if policy = "auto" then begin
          run (); check (read normal = incoming) "auto decline did not complete ordinary rsync"
        end else begin
          fail_expected transient run; check (not (exists normal)) "require decline exposed ordinary candidate"
        end;
        no_native_creation (); no_stage ()))) ["auto";"require"]) [1;2;3]) [1;2;12;13;14];
  List.iter (fun mode ->
    test (Printf.sprintf "malformed or operational preparation mode=%d is an auto error" mode) (fun () ->
      Prefs.loadStrings ["clone = auto"];
      fixture top (fun _ _ normal run _ no_stage ->
        attribute_fault mode 1; fail_expected transient run;
        no_native_creation (); check (not (exists normal)) "preparation error fell back to normal output";
        no_stage ()))) [3;4;5;6;7];
  List.iter (fun mode ->
    test (Printf.sprintf "native creation operational failure mode=%d settles prepared context" mode) (fun () ->
      Prefs.loadStrings ["clone = auto"];
      fixture top (fun _ _ normal run _ no_stage ->
        handles_mode mode; fail_expected transient run;
        check (!(H.creates)=1) "native creation was retried";
        check (not (exists normal)) "native creation error fell back"; no_stage ()))) [4;6];
  List.iter (fun mode ->
    test (Printf.sprintf "adoption native identity/error mode=%d removes only its created stage" mode) (fun () ->
      Prefs.loadStrings ["clone = auto"];
      fixture top (fun _ _ normal run _ no_stage ->
        H.action := (fun phase -> if phase="adopt-before" then attribute_fault mode 1);
        fail_expected transient run;
        check (!(H.creates)=1 && not (exists normal)) "adoption failure retried or exposed output";
        no_stage ()))) [1;3;6;7;12;13];
  test "actual creation parent rebound during native cloning preserves replacement stage sentinel" (fun () ->
    Prefs.loadStrings ["clone = require"];
    fixture top (fun _ path normal run _ _ ->
      handles_paths (path "basis") (path "basis-moved"); handles_mode 7;
      fail_expected (identity_failure "stage_publication") run;
      let stage,_ = names () in
      check (read stage = "replacement sentinel") "rebound creation-parent sentinel was deleted/overwritten";
      check (not (exists (path ("basis-moved/" ^ Filename.basename stage)))) "created stage in original parent leaked";
      check (not (exists normal)) "rebound creation parent exposed normal candidate"));
  List.iter (fun phase -> List.iter (fun allocation ->
    test (Printf.sprintf "post-adoption %s failure=%s" phase (if allocation then "OOM" else "exception")) (fun () ->
      Prefs.loadStrings ["clone = require"];
      fixture top (fun _ _ normal run _ no_stage ->
        H.target := phase; H.error := (if allocation then Out_of_memory else H.Injected);
        fail_expected (fun error -> error == !(H.error)) run;
        check (List.mem "adopt-after" !(H.events)) "channel failure preceded witness adoption";
        check (not (exists normal)) "failed handoff exposed a normal candidate";
        no_stage ()))) [false;true])
    ["clone-out-channel";"clone-in-channel";"in-before";"in-after";"out-before";"out-after"];
  List.iter (fun phase -> List.iter (fun allocation ->
    test (Printf.sprintf "prepared-context %s failure=%s" phase (if allocation then "OOM" else "exception")) (fun () ->
      Prefs.loadStrings ["clone = require"];
      fixture top (fun _ _ normal run _ no_stage ->
        H.target := phase; H.error := (if allocation then Out_of_memory else H.Injected);
        fail_expected (fun error -> error == !(H.error)) run;
        no_native_creation (); check (not (exists normal)) "prepared handoff exposed output"; no_stage ()))) [false;true])
    ["prepare-some";"publication-before";"publication-after"];
  List.iter (fun allocation ->
    test ("native rename succeeds before injected " ^ (if allocation then "OOM" else "exception")) (fun () ->
      Prefs.loadStrings ["clone = require"];
      fixture top (fun _ _ normal run _ no_stage ->
        H.action := (fun phase -> if phase="publish-after" then begin
          let stage,temporary = names () in
          check (not (exists stage) && read temporary=incoming) "rename fault did not follow real publication"
        end);
        H.target := "publish-after"; H.error := (if allocation then Out_of_memory else H.Injected);
        fail_expected (fun error -> error == !(H.error)) run;
        check (not (List.mem "disarm-before" !(H.events))) "fault did not interrupt before disarm";
        check (not (exists normal)) "moved owned temporary survived aborted publication"; no_stage ()))) [false;true];
  test "exclusive native publication race preserves collision sentinel" (fun () ->
    Prefs.loadStrings ["clone = require"];
    fixture top (fun _ _ normal run _ no_stage ->
      rename_fault 2; fail_expected (identity_failure "stage_publication.publish.rename") run;
      check (read normal="exclusive native race sentinel") "exclusive collision sentinel was overwritten/removed";
      no_stage ()));
  List.iter (fun mode ->
    test (Printf.sprintf "publication identity/operational mode=%d remains an auto error" mode) (fun () ->
      Prefs.loadStrings ["clone = auto"];
      fixture top (fun _ _ normal run _ no_stage ->
        H.action := (fun phase -> if phase="publish-before" then attribute_fault mode 1);
        fail_expected (identity_failure "stage_publication") run;
        check (!(H.creates)=1 && !(H.packets)>0) "publication fault did not follow native stage and receiver tokens";
        check (not (exists normal)) "publication error fell back or exposed incomplete output";
        no_stage ()))) [1;3;6;12;13];
  test "native publication rename EIO is terminal and removes only owned stage" (fun () ->
    Prefs.loadStrings ["clone = auto"];
    fixture top (fun _ _ normal run _ no_stage ->
      rename_fault 1; fail_expected (identity_failure "stage_publication.publish.rename") run;
      check (not (exists normal)) "rename EIO exposed or retried output"; no_stage ()));
  List.iter (fun parent ->
    test ("publication detects rebound " ^ parent ^ " parent and preserves sentinels") (fun () ->
      Prefs.loadStrings ["clone = require"];
      fixture top (fun _ path normal run _ _ ->
        let replacement = ref "" in
        H.action := (fun phase -> if phase="publish-before" then begin
          let stage,temporary = names () in
          let owned = if parent="basis" then stage else temporary in
          Unix.rename (path parent) (path (parent ^ "-moved")); Unix.mkdir (path parent) 0o700;
          replacement := Filename.concat (path parent) (Filename.basename owned);
          write !replacement sentinel
        end);
        fail_expected (identity_failure "stage_publication") run;
        check (read !replacement=sentinel) "rebound parent sentinel was removed/overwritten";
        let stage,_ = names () in
        let old_stage = if parent="basis" then path ("basis-moved/" ^ Filename.basename stage) else stage in
        check (not (exists old_stage)) "owned stage in captured parent was not removed";
        if parent="basis" then check (not (exists normal)) "rebound stage parent exposed normal output"))) ["basis";"receiving"];
  test "publication rejects replaced stage entry without deleting the replacement" (fun () ->
    Prefs.loadStrings ["clone = require"];
    fixture top (fun _ path normal run _ _ ->
      let quarantined = path "quarantined-stage" in
      H.action := (fun phase -> if phase="publish-before" then begin
        let stage,_ = names () in Unix.rename stage quarantined; write stage sentinel
      end);
      fail_expected (identity_failure "stage_publication") run;
      let stage,_ = names () in
      check (read stage=sentinel) "replacement stage entry was deleted/overwritten";
      check (read quarantined=incoming) "private externally moved candidate bytes differ";
      check (not (exists normal)) "replaced stage was published"));
  List.iter (fun append ->
    test ("referenceFd promptly rejects FIFO then opens usable regular " ^ (if append then "APPEND" else "DATA")) (fun () ->
      fixture top (fun directory path _ _ _ _ ->
        Unix.mkfifo (path "fifo") 0o600;
        let infd = ref None and kind = if append then `DATA_APPEND (Uutil.Filesize.ofInt 13) else `DATA in
        let began = Unix.gettimeofday () in
        fail_expected transient (fun () -> ignore (Copy.referenceFd directory (Path.fromString "fifo") kind infd));
        check (Unix.gettimeofday () -. began < 2.) "FIFO rejection was not prompt";
        check (!infd=None) "FIFO rejection retained an input channel";
        let channel=Copy.referenceFd directory (Path.fromString "basis/live") kind infd in
        let fd=Unix.descr_of_in_channel channel in
        check (reference_flags fd=7) "ordinary reference is not readonly/nonblocking/CLOEXEC";
        let offset=if append then 13 else 0 in
        check (LargeFile.pos_in channel=Int64.of_int offset) "DATA_APPEND offset changed";
        check (input_char channel=basis.[offset]) "follow-up regular reference is unusable";
        Copy.close_all infd (ref None)))) [false;true];
  List.iter (fun phase -> List.iter (fun allocation ->
    test (Printf.sprintf "referenceFd %s failure=%s closes/reuses real FD" phase (if allocation then "OOM" else "exception")) (fun () ->
      fixture top (fun directory path _ _ _ _ ->
        let infd=ref None in
        H.target := phase; H.error := (if allocation then Out_of_memory else H.Injected);
        fail_expected (fun error -> error == !(H.error))
          (fun () -> ignore (Copy.referenceFd directory (Path.fromString "basis/live") `DATA infd));
        check (!infd=None) "failed reference handoff exposed a channel";
        reuse_cleanup directory (path "sentinel");
        H.target := "";
        let channel=Copy.referenceFd directory (Path.fromString "basis/live") `DATA infd in
        check (input_char channel=basis.[0]) "regular follow-up failed after handoff cleanup";
        Copy.close_all infd (ref None)))) [false;true])
    ["reference-channel";"in-before";"in-after";"reference-some"];
  test "successful receiver follows prior rejected publication without stale cleanup" (fun () ->
    Prefs.loadStrings ["clone = require"];
    fixture top (fun _ _ normal run _ no_stage -> successful normal run no_stage));
  Printf.printf "Copy publication/reference: %d production-caller cases passed; disposable native/rsync scope\n%!" !cases
'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError('production hook is no longer unique: ' + old[:90])
    return source.replace(old, new, 1)


def instrument(source):
    source = replace_once(source,
        'let inFdResource = Remote.resourceWithConnCleanup close_in close_in_noerr',
        'let inFdResource = PublicationFault.resource "in" (Remote.resourceWithConnCleanup close_in close_in_noerr)')
    source = replace_once(source,
        'let outFdResource = Remote.resourceWithConnCleanup close_out close_out_noerr',
        'let outFdResource = PublicationFault.resource "out" (Remote.resourceWithConnCleanup close_out close_out_noerr)')
    source = replace_once(source,
        'let clonePublicationResource = Remote.resourceWithConnCleanup\n  StagePublication.abort_and_close StagePublication.close_noerr',
        'let clonePublicationResource = PublicationFault.resource "publication" (Remote.resourceWithConnCleanup\n  StagePublication.abort_and_close StagePublication.close_noerr)')
    source = replace_once(source, 'try Unix.out_channel_of_descr outputFd with error ->',
        'try PublicationFault.wrap "clone-out-channel" (fun () -> Unix.out_channel_of_descr outputFd) with error ->')
    source = replace_once(source, 'try Unix.in_channel_of_descr basisFd with error ->',
        'try PublicationFault.wrap "clone-in-channel" (fun () -> Unix.in_channel_of_descr basisFd) with error ->')
    source = replace_once(source, 'begin try Some publication with error ->',
        'begin try PublicationFault.wrap "prepare-some" (fun () -> Some publication) with error ->')
    source = replace_once(source, 'Unix.in_channel_of_descr raw',
        'PublicationFault.wrap "reference-channel" (fun () -> Unix.in_channel_of_descr raw)')
    source = replace_once(source, 'begin try infd := Some fd; fd',
        'begin try infd := PublicationFault.wrap "reference-some" (fun () -> Some fd); fd')
    source = replace_once(source, 'compressRemotely connFrom\n           ((bi,',
        '(PublicationFault.compress_local (processTransferInstruction connFrom)) connFrom\n           ((bi,')
    return HOOK + source


def objects(makefile, name):
    match = re.search(r'^' + name + r' = (.*?)(?=\n\n)', makefile, re.M | re.S)
    if match is None:
        raise RuntimeError('missing Make object list: ' + name)
    body = match.group(1).replace('\\\n', ' ').replace('$(SYSTEM)', 'generic')
    return body.replace('$(WINOBJS)', '').replace('$(WINCOBJS)', '').replace('$(OBJ_EXT)', '.o').replace('.cmo', '.cmx').split()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path, help='fresh compiler-matched isolated Make snapshot')
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--keep-work', action='store_true', help='retain isolated generated sources and logs')
    parser.add_argument('--negative-control', action='store_true', help='prove missing publication cleanup is detected')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = args.build.resolve() / 'src'
    # Check the complete production inputs used by the harness, not just Copy.
    production = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root)
    for item in production.split(b'\0'):
        if not item:
            continue
        name = os.fsdecode(item)
        path = root / name
        if name.startswith('src/') and name != 'src/.depend' and path.is_file():
            if (args.build / name).read_bytes() != path.read_bytes():
                raise AssertionError(name + ' differs from frozen snapshot; rebuild before linking')
    for name in ['copy.ml', 'copy_stubs.c', 'stagePublication.ml', 'stagePublication_stubs.c', 'cloneLease.ml']:
        print('source', name, hashlib.sha256((build / name).read_bytes()).hexdigest(), flush=True)
    makefile = (build / 'Makefile.OCaml').read_text()
    modules = objects(makefile, 'OCAMLOBJS')
    modules = modules[:modules.index('copy.cmx')]
    cobjects = [name for name in objects(makefile, 'COBJS') if name not in ('copy_stubs.o', 'stagePublication_stubs.o')]
    includes = [build, build/'lwt', build/'ubase', build/'system', build/'system/generic', build/'lwt/generic']
    flags = [flag for path in includes for flag in ['-I', str(path)]] + ['-I', '+unix', '-I', '+str']
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    work = Path(tempfile.mkdtemp(prefix='unison-copy-publication-', dir='/private/tmp'))
    print('work', work, flush=True)
    try:
        private_copy = instrument((build/'copy.ml').read_text())
        if args.negative_control:
            private_copy = replace_once(private_copy,
                'let closeClonePublicationNoErr publication =\n  try clonePublicationResource.release_noerr publication with _ ->\n    StagePublication.close_noerr publication',
                'let closeClonePublicationNoErr _ = () (* negative control: ownership cleanup removed *)')
        (work/'copyForPublication.ml').write_text(private_copy)
        print('compiled CopyForPublication', hashlib.sha256(private_copy.encode()).hexdigest(), flush=True)
        (work/'publicationTest.ml').write_text(HARNESS)
        (work/'referenceFlags.c').write_text(NATIVE)
        for source, destination in [('tests/clone_handles/fixture.c','handlesFixture.c'),
                                    ('tests/stage_publication/fixture.c','publicationFixture.c')]:
            data = (root/source).read_bytes()
            (work/destination).write_bytes(data)
            print('fixture', source, hashlib.sha256(data).hexdigest(), flush=True)
        # The fixture includes byte-identical frozen production C, replacing
        # only native syscalls. Exclude the corresponding original C objects.
        for name in ['copy_stubs.c','stagePublication_stubs.c','nativeIdentity.h']:
            if (build/name).is_file():
                shutil.copy2(build/name, work/name)
        state = work/'state'; state.mkdir(); environment['UNISON'] = str(state)
        print('Compiler', subprocess.check_output([args.ocamlopt,'-version'], env=environment, text=True).strip(), flush=True)
        with (work/'build.log').open('w+') as log:
            try:
                for name in ['handlesFixture.c','publicationFixture.c','referenceFlags.c','copyForPublication.ml']:
                    subprocess.run([args.ocamlopt,*flags,'-c',name], cwd=work, env=environment, stdout=log, stderr=log, check=True)
                subprocess.run([args.ocamlopt,*flags,'unix.cmxa','str.cmxa',
                                *[str(build/name) for name in modules], 'copyForPublication.cmx','publicationTest.ml',
                                *[str(build/name) for name in cobjects], 'handlesFixture.o','publicationFixture.o','referenceFlags.o',
                                '-o','publication-copy-test'], cwd=work, env=environment, stdout=log, stderr=log, check=True)
            except subprocess.CalledProcessError:
                log.seek(0); print(log.read()); raise
        result = subprocess.run([str(work/'publication-copy-test'),str(work),
                                 'negative' if args.negative_control else 'normal'], cwd=work, env=environment,
                                text=True, capture_output=True, timeout=120)
        (work/'test.log').write_text(result.stdout + result.stderr)
        print(result.stdout,end=''); print(result.stderr,end='')
        if result.returncode == 77:
            print('SKIP: native clone publication requires macOS 10.12+')
        elif args.negative_control:
            if result.returncode == 0 or 'owned clone stage name survived' not in result.stderr:
                raise AssertionError('negative control did not detect missing publication ownership cleanup')
            print('PASS negative control: removing caller publication cleanup leaves the adopted stage and is detected')
        else:
            result.check_returncode()
    finally:
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
