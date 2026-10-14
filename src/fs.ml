(* Unison file synchronizer: src/fs.ml *)
(* Copyright 1999-2020, Benjamin C. Pierce

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*)

type fspath = Fspath.t
let mfspath = Fspath.m
type dir_handle = System.dir_handle
                = { readdir : unit -> string; closedir : unit -> unit }

let path p = Fspath.toString p |> System.extendedPath

(****)

let symlink l f = System.symlink l (path f)

let readlink f = System.readlink (path f)

let chown f usr grp = System.chown (path f) usr grp

let chmod f mode = System.chmod (path f) mode

let utimes f t1 t2 = System.utimes (path f) t1 t2

let unlink f = System.unlink (path f)

let rmdir f = System.rmdir (path f)

let mkdir f mode = System.mkdir (path f) mode

let rename f f' = System.rename (path f) (path f')

let stat f = System.stat (path f)

let lstat f = System.lstat (path f)

let openfile f flags perms = System.openfile (path f) flags perms

let opendir f = System.opendir (path f)

let open_in_gen flags mode f =
  System.open_in_gen flags mode (path f)

let open_out_gen flags mode f =
  System.open_out_gen flags mode (path f)

(****)

let open_in_bin f = System.open_in_bin (path f)

let file_exists f =
  try
    ignore (stat f); true
  with Unix.Unix_error ((Unix.ENOENT | Unix.ENOTDIR), _, _) ->
    false

(****)

let clone_path f1 f2 = System.clone_path (path f1) (path f2)
let clone_file = System.clone_file
let copy_file = System.copy_file
let copy_file_status = System.copy_file_status

let clone_file_status ~expected_length source destination =
  if expected_length < 0L then invalid_arg "Fs.clone_file_status: negative expected length";
  WholeFileClone.decode_native ~expected_length
    (System.clone_file_status_raw source destination expected_length)

type clone_path_result =
  | Created_path of (WholeFileClone.receipt * Unix.file_descr * Unix.file_descr)
  | Declined_path of (WholeFileClone.decline_scope * WholeFileClone.receipt)
type clone_path_residual = Absent | Removed_owned_entry | Unqualified_entry_may_remain
type clone_path_cleanup_failure = {
  primary : exn;
  cleanup_error : exn option;
  residual : clone_path_residual;
}
exception Clone_path_cleanup_failed of clone_path_cleanup_failure

let clone_path_status ~expected_length source destination =
  if expected_length < 0L then invalid_arg "Fs.clone_path_status: negative expected length";
  let source_path = path source and destination_path = path destination in
  if source_path = "" || String.contains source_path '\000' ||
     destination_path = "" || String.contains destination_path '\000' then
    invalid_arg "Fs.clone_path_status: invalid path";
  let leaf = Filename.basename destination_path
  and directory = Filename.dirname destination_path in
  if leaf = "" || leaf = "." || leaf = ".." then
    invalid_arg "Fs.clone_path_status: invalid destination leaf";
  if not (System.whole_clone_named_available ()) then
    match WholeFileClone.platform_decline ~expected_length with
    | WholeFileClone.Declined (scope, receipt) -> Declined_path (scope, receipt)
    | _ -> assert false
  else
    (* Every returned FD goes immediately into preallocated owner slots, with
       no Some/record allocation between native open and publication of its
       ownership. Native-created output uses the custom C carrier throughout. *)
    let source_fd = ref Unix.stdin and source_owned = ref false
    and parent_fd = ref Unix.stdin and parent_owned = ref false
    and output_fd = ref Unix.stdin and output_owned = ref false
    and cleanup_error = ref (Failure "unset whole-clone cleanup error")
    and cleanup_failed = ref false
    and residual = ref Absent and residual_known = ref false in
    let owner = System.whole_clone_prepare_named leaf in
    let note_cleanup error =
      if not !cleanup_failed then begin
        cleanup_error := error; cleanup_failed := true
      end in
    let close_slot descriptor owned =
      System.whole_clone_close_slot descriptor owned in
    let close_cleanup descriptor owned =
      try close_slot descriptor owned with error -> note_cleanup error in
    let decode_cleanup (error, native_code, raw_residual) =
      residual := (match raw_residual with
        | 0 -> Absent | 1 -> Removed_owned_entry | 2 -> Unqualified_entry_may_remain
        | _ -> raise (WholeFileClone.Invalid_native_status
            "unknown named whole-clone cleanup residue"));
      if native_code < 0L || native_code > 2147483647L ||
         (error = None && native_code <> 0L) ||
         (error <> None && native_code = 0L) then
        raise (WholeFileClone.Invalid_native_status
          "invalid named whole-clone cleanup native error");
      residual_known := true;
      match error with
      | None -> ()
      | Some errno -> raise (Unix.Unix_error (errno,
          Printf.sprintf "whole-clone/named/cleanup [native code %Ld]" native_code,
          destination_path)) in
    let abort () =
      if !parent_owned then begin
        (* This primitive settles every C-owned FD and records its result
           BEFORE result allocation or pending delivery. Repeated calls only
           retrieve that stored outcome; they never retry unlink or close. *)
        residual_known := false;
        try decode_cleanup (System.whole_clone_abort_named owner !parent_fd)
        with error ->
          if not !residual_known then residual := Unqualified_entry_may_remain;
          note_cleanup error
      end in
    let fail primary =
      abort ();
      (* After transfer C may use output_fd as a borrowed identity witness.
         Keep it live through abort, then settle all facade slots exactly once. *)
      close_cleanup output_fd output_owned;
      close_cleanup source_fd source_owned;
      close_cleanup parent_fd parent_owned;
      if !cleanup_failed || !residual = Unqualified_entry_may_remain then
        raise (Clone_path_cleanup_failed {
          primary; cleanup_error = (if !cleanup_failed then Some !cleanup_error else None);
          residual = !residual })
      else raise primary in
    try
      let source = System.openfile source_path
        [Unix.O_RDONLY; Unix.O_CLOEXEC; Unix.O_NONBLOCK] 0 in
      source_fd := source; source_owned := true;
      let source_before = Unix.LargeFile.fstat source in
      let check_source_path () =
        let held = Unix.LargeFile.fstat source
        and named = System.stat source_path in
        let same status =
          status.Unix.LargeFile.st_kind = Unix.S_REG &&
          status.Unix.LargeFile.st_dev = source_before.Unix.LargeFile.st_dev &&
          status.Unix.LargeFile.st_ino = source_before.Unix.LargeFile.st_ino &&
          status.Unix.LargeFile.st_size = expected_length &&
          status.Unix.LargeFile.st_perm = source_before.Unix.LargeFile.st_perm &&
          status.Unix.LargeFile.st_uid = source_before.Unix.LargeFile.st_uid &&
          status.Unix.LargeFile.st_gid = source_before.Unix.LargeFile.st_gid &&
          status.Unix.LargeFile.st_nlink = source_before.Unix.LargeFile.st_nlink &&
          status.Unix.LargeFile.st_mtime = source_before.Unix.LargeFile.st_mtime &&
          status.Unix.LargeFile.st_ctime = source_before.Unix.LargeFile.st_ctime in
        if not (same held && same named) then
          raise (Unix.Unix_error (Unix.EBUSY, "whole-clone/source-path-verification", source_path)) in
      (* Follow the same source resolution as ordinary DATA copying, but bind
         the resolved name to the admitted FD before and after the clone. The
         native adapter additionally uses nanosecond held-source witnesses. *)
      check_source_path ();
      let parent = System.openfile directory
        [Unix.O_RDONLY; Unix.O_CLOEXEC; Unix.O_NONBLOCK] 0 in
      parent_fd := parent; parent_owned := true;
      match WholeFileClone.decode_native ~expected_length
        (System.whole_clone_run_named source parent expected_length owner) with
      | WholeFileClone.Declined (scope, receipt) ->
          (* Allocate the return while guard/carrier still retain all handles.
             A successful decline must also complete transient cleanup. *)
          let result = Declined_path (scope, receipt) in
          check_source_path ();
          decode_cleanup (System.whole_clone_abort_named owner parent);
          if !residual = Unqualified_entry_may_remain then
            raise (WholeFileClone.Invalid_native_status "declined named clone left residue");
          close_slot source_fd source_owned;
          close_slot parent_fd parent_owned;
          result
      | WholeFileClone.Failed receipt ->
          WholeFileClone.raise_failed ~argument:destination_path receipt
      | WholeFileClone.No_work _ ->
          raise (WholeFileClone.Invalid_native_status
            "named clone cannot complete without creating its output")
      | WholeFileClone.Native_shared receipt ->
          check_source_path ();
          let output = System.whole_clone_peek_named_output owner in
          let result = Created_path (receipt, output, parent) in
          close_slot source_fd source_owned;
          (* Finish settles the backup witness only. Main output remains
             C-owned until final atomic handoff, so finish/allocation errors
             still have discoverable cleanup authority. Its residue is linked
             by design; consume only the validated error status on success. *)
          decode_cleanup (System.whole_clone_finish_named owner);
          System.whole_clone_transfer_named_output owner output_fd output_owned;
          (* Do not clear parent_owned inside the guarded region: an exception
             after transfer but before return still belongs to this facade.
             Return the already allocated result without another allocation. *)
          result
    with error -> fail error

type clone_stage_decline =
  | Platform_unavailable
  | Non_regular_source
  | Source_flags
  | Cross_device
  | Operation_unsupported

type clone_stage_result =
  | Shared_stage of (Unix.file_descr * Unix.file_descr)
  | Declined_stage of clone_stage_decline

external clone_stage_status_raw : string -> string -> clone_stage_result =
  "unison_clone_stage_status"

let clone_stage_status source destination =
  clone_stage_status_raw (path source) (path destination)

type clone_stage_handles_result =
  | Shared_stage_handles of (Unix.file_descr * Unix.file_descr * Unix.file_descr)
  | Declined_stage_handles of clone_stage_decline

external clone_stage_handles_raw : string -> string -> clone_stage_handles_result =
  "unison_clone_stage_handles"

let clone_stage_handles source destination =
  clone_stage_handles_raw (path source) (path destination)

external clone_stage_handles_sized_raw : string -> string -> int64 -> clone_stage_handles_result =
  "unison_clone_stage_sized_handles"

let clone_stage_handles_sized ~expected_length source destination =
  if expected_length < 0L then invalid_arg "Fs.clone_stage_handles_sized: negative expected length";
  clone_stage_handles_sized_raw (path source) (path destination) expected_length

let clone_stage_decline_reason = function
  | Platform_unavailable -> "clone-stage API unavailable on this platform"
  | Non_regular_source -> "clone-stage basis is not a regular file"
  | Source_flags -> "clone-stage source flags require ordinary copying"
  | Cross_device -> "clone-stage source and destination are on different devices"
  | Operation_unsupported -> "clone-stage operation unsupported for this file pair"

external clone_stage_raw : string -> string ->
  (Unix.file_descr * Unix.file_descr) option = "unison_clone_stage"

let clone_stage source destination =
  clone_stage_raw (path source) (path destination)

(****)

exception XattrNotSupported = System.XattrNotSupported

let xattr_list f = System.xattr_list (path f)
let xattr_get f n = System.xattr_get (path f) n
let xattr_set f n v = System.xattr_set (path f) n v
let xattr_remove f n = System.xattr_remove (path f) n

let xattrUpdatesCTime = System.xattrUpdatesCTime

(****)

let acl_get_text f = System.acl_get_text (path f)
let acl_set_text f acl = System.acl_set_text (path f) acl

(****)

let hasInodeNumbers () = System.hasInodeNumbers ()
let hasSymlink () = System.hasSymlink ()
let hasCorrectCTime = System.hasCorrectCTime
