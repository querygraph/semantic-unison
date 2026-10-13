(* Unison file synchronizer: src/copy.ml *)
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

let (>>=) = Lwt.bind

let debug = Trace.debug "copy"

let clonePolicy =
  Prefs.createString "clone" "auto" ~local:true
    ~category:(`Advanced `General)
    "receiver clone staging: auto, off, or require"
    "Use a private receiver-basis clone for eligible file updates. auto falls \
     back when cloning is unsupported; off disables this optimization; require \
     reports unsupported cloning for eligible updates. Data is still verified."

let receiverCloneEnabled () =
  match Prefs.read clonePolicy with
  | "auto" | "require" -> true
  | "off" -> false
  | _ -> raise (Util.Fatal "clone must be auto, off, or require")

(****)

let protect f g =
  try
    f ()
  with e ->
    begin try g () with Sys_error _  | Unix.Unix_error _ -> () end;
    raise e

let lwt_protect f g =
  Lwt.catch f
    (fun e ->
       begin try g () with Sys_error _  | Unix.Unix_error _ -> () end;
       Lwt.fail e)

(****)

(* If newFpOpt = Some newfp, check that the current source contents
   matches newfp.  Otherwise, check whether the source file has been
   modified during synchronization. *)
let checkForChangesToSourceLocal
      fspathFrom pathFrom archDesc archFp archStamp archRess newFpOpt paranoid =
  (* Retrieve attributes of current source file *)
  let sourceInfo = Fileinfo.getBasicWithRess true fspathFrom pathFrom in
  let sourceType = sourceInfo.Fileinfo.typ in
  match newFpOpt with
    None ->
      (* no newfp provided: so we need to compare the archive with the
         current source *)
      let clearlyChanged =
           sourceType <> `FILE
        || Props.length sourceInfo.Fileinfo.desc <> Props.length archDesc
        || Osx.ressLength sourceInfo.Fileinfo.osX.Osx.ressInfo <>
           Osx.ressLength archRess    in
      let dataClearlyUnchanged =
           not clearlyChanged
        && Props.same_time sourceInfo.Fileinfo.desc archDesc
        && not (Fpcache.excelFile pathFrom)
        && match archStamp with
             Some (Fileinfo.InodeStamp inode) -> sourceInfo.Fileinfo.inode = inode
           | Some (Fileinfo.NoStamp)          -> true
           | Some (Fileinfo.RescanStamp)      -> false
           | None                             -> false   in
      let ressClearlyUnchanged =
           not clearlyChanged
        && Osx.ressUnchanged archRess sourceInfo.Fileinfo.osX.Osx.ressInfo
                             None dataClearlyUnchanged   in
      if dataClearlyUnchanged && ressClearlyUnchanged then begin
        if paranoid && not (Os.isPseudoFingerprint archFp) then begin
          let newFp = Os.fingerprint fspathFrom pathFrom sourceType in
          if archFp <> newFp then begin
            Update.markPossiblyUpdated fspathFrom pathFrom;
            raise (Util.Transient (Printf.sprintf
              "The source file %s\n\
               has been modified but the fast update detection mechanism\n\
               failed to detect it.  Try running once with the fastcheck\n\
               option set to 'no'."
              (Fspath.toPrintString (Fspath.concat fspathFrom pathFrom))))
          end
        end
      end else if
           clearlyChanged
        || archFp <> Os.fingerprint fspathFrom pathFrom sourceType
      then
        raise (Util.Transient (Printf.sprintf
          "The source file %s\nhas been modified during synchronization.  \
           Transfer aborted."
          (Fspath.toPrintString (Fspath.concat fspathFrom pathFrom))))
  | Some newfp ->
      (* newfp provided means that the archive contains a pseudo-fingerprint... *)
      assert (Os.isPseudoFingerprint archFp);
      (* ... so we can't compare the archive with the source; instead we
         need to compare the current source to the new fingerprint: *)
      if newfp <> Os.fingerprint fspathFrom pathFrom sourceType then
        raise (Util.Transient (Printf.sprintf
          "Current source file %s\n not same as transferred file.  \
           Transfer aborted."
          (Fspath.toPrintString (Fspath.concat fspathFrom pathFrom))))

let mcheckForChangesToSource =
  Umarshal.(prod2
              (prod4 Path.mlocal Props.m Os.mfullfingerprint (option Fileinfo.mstamp) id id)
              (prod3 Osx.mressStamp (option Os.mfullfingerprint) bool id id)
              id id)

let checkForChangesToSourceOnRoot =
  Remote.registerRootCmd
    "checkForChangesToSource"
    mcheckForChangesToSource Umarshal.unit
    (fun (fspathFrom,
          ((pathFrom, archDesc, archFp, archStamp), (archRess, newFpOpt, paranoid))) ->
      checkForChangesToSourceLocal
        fspathFrom pathFrom archDesc archFp archStamp archRess newFpOpt paranoid;
      Lwt.return ())

let checkForChangesToSource
      root pathFrom archDesc archFp archStamp archRess newFpOpt paranoid =
  checkForChangesToSourceOnRoot
    root ((pathFrom, archDesc, archFp, archStamp), (archRess, newFpOpt, paranoid))

(****)

let fileIsTransferred fspathTo pathTo desc fp ress =
  let info = Fileinfo.getBasicWithRess false fspathTo pathTo in
  (Fileinfo.basic info,
   info.Fileinfo.typ = `FILE
     &&
   Props.length info.Fileinfo.desc = Props.length desc
     &&
   Osx.ressLength info.Fileinfo.osX.Osx.ressInfo =
   Osx.ressLength ress
     &&
   let fp' = Os.fingerprint fspathTo pathTo info.Fileinfo.typ in
   fp' = fp)

(* We slice the files in 1GB chunks because that's the limit for
   Fingerprint.subfile on 32 bit architectures *)
let fingerprintLimit = Uutil.Filesize.ofInt64 1072693248L

let rec fingerprintPrefix fspath path offset len accu =
  if len = Uutil.Filesize.zero then accu else begin
    let l = min len fingerprintLimit in
    let fp = Fingerprint.subfile (Fspath.concat fspath path) offset l in
    fingerprintPrefix fspath path
      (Int64.add offset (Uutil.Filesize.toInt64 l)) (Uutil.Filesize.sub len l)
      (fp :: accu)
  end

let fingerprintPrefixRemotely =
  Remote.registerServerCmd
    "fingerprintSubfile"
    Umarshal.(prod3 Fspath.m Path.mlocal Uutil.Filesize.m id id)
    Umarshal.(list Fingerprint.m)
    (fun _ (fspath, path, len) ->
       Lwt.return (fingerprintPrefix fspath path 0L len []))

let appendThreshold = Uutil.Filesize.ofInt (1024 * 1024)

let validFilePrefix connFrom fspathFrom pathFrom fspathTo pathTo info desc =
  let len = Props.length info.Fileinfo.desc in
  if
    info.Fileinfo.typ = `FILE &&
    len >= appendThreshold && len < Props.length desc
  then begin
    Lwt.try_bind
      (fun () ->
         fingerprintPrefixRemotely connFrom (fspathFrom, pathFrom, len))
      (fun fpFrom ->
         let fpTo = fingerprintPrefix fspathTo pathTo 0L len [] in
         Lwt.return (if fpFrom = fpTo then Some len else None))
      (fun _ ->
         Lwt.return None)
  end else
    Lwt.return None

type transferStatus =
    TransferSucceeded of Fileinfo.basic
  | TransferNeedsDoubleCheckAgainstCurrentSource of Fileinfo.basic * Os.fullfingerprint
  | TransferFailed of string

let mtransferStatus = Umarshal.(sum3
                                  Fileinfo.mbasic
                                  (prod2 Fileinfo.mbasic Os.mfullfingerprint id id)
                                  string
                                  (function
                                   | TransferSucceeded a -> I31 a
                                   | TransferNeedsDoubleCheckAgainstCurrentSource (a, b) -> I32 (a, b)
                                   | TransferFailed a -> I33 a)
                                  (function
                                   | I31 a -> TransferSucceeded a
                                   | I32 (a, b) -> TransferNeedsDoubleCheckAgainstCurrentSource (a, b)
                                   | I33 a -> TransferFailed a))

(* Paranoid check: recompute the transferred file's fingerprint to match it
   with the archive's.  If the old
   fingerprint was a pseudo-fingerprint, we can't tell just from looking at the
   new file and the archive information, so we return
   TransferProbablySucceeded in this case, along with the new fingerprint
   that we can check in checkForChangesToSource when we've
   calculated the current source fingerprint.
 *)
type producer = {
  binding : TargetBinding.t;
  mutable adopted : bool;
  mutable frozen : bool;
  mutable legacy : bool;
}

let checkProducer = function
  | None -> ()
  | Some producer when producer.legacy -> ()
  | Some producer ->
      TargetBinding.recheck_resolution producer.binding;
      if producer.adopted then
        let context = TargetBinding.native producer.binding in
        if producer.frozen then FinalPublication.check_candidate context
        else FinalPublication.check_producer context

let adoptProducer producer descriptor =
  match producer with
  | None -> ()
  | Some producer when producer.legacy -> ()
  | Some producer ->
      checkProducer (Some producer);
      let context = TargetBinding.native producer.binding in
      if producer.adopted then
        FinalPublication.check_producer_fd context ~candidate:descriptor
      else begin
        FinalPublication.adopt_mutable context ~candidate:descriptor;
        producer.adopted <- true
      end;
      checkProducer (Some producer)

let handoffProducer producer =
  match producer with
  | None -> ()
  | Some producer when producer.legacy -> ()
  | Some producer ->
      checkProducer (Some producer);
      TargetBinding.legacy_handoff producer.binding;
      producer.legacy <- true

let freezeProducer producer =
  match producer with
  | None -> ()
  | Some producer when producer.legacy -> ()
  | Some producer ->
      checkProducer (Some producer);
      if not producer.adopted then
        raise (Util.Transient "Receiving producer did not retain its output file");
      let context = TargetBinding.native producer.binding in
      if not (FinalPublication.auxiliary_absent context) then
        (* Planned resource finalization can create an AppleDouble family.
           That family keeps its existing complete rename behavior. *)
        handoffProducer (Some producer)
      else begin
        FinalPublication.freeze_producer context;
        producer.frozen <- true;
        checkProducer (Some producer)
      end

let paranoidCheck ?producer fspathTo pathTo realPathTo desc fp ress =
  freezeProducer producer;
  checkProducer producer;
  let info = Fileinfo.getBasic false fspathTo pathTo in
  let fp' = Os.fingerprint fspathTo pathTo info.Fileinfo.typ in
  checkProducer producer;
  (match producer with
   | Some producer when not producer.legacy ->
       TargetBinding.record_fingerprint producer.binding fp'
   | _ -> ());
  if Os.isPseudoFingerprint fp then begin
    Lwt.return (TransferNeedsDoubleCheckAgainstCurrentSource (info,fp'))
  end else if fp' <> fp then begin
    debug (fun() -> Util.msg "Fingerprints differ: %s vs %s\n"
      (Os.fullfingerprint_to_string fp)
      (Os.fullfingerprint_to_string fp'));
    Lwt.return (TransferFailed (Os.reasonForFingerprintMismatch fp fp'))
  end else
    Lwt.return (TransferSucceeded info)

let saveTempFileLocal (fspathTo, (pathTo, realPathTo, reason)) =
  debug (fun() -> Util.msg "Failed (%s): Saving old temp file %s\n"
         reason (Path.toString pathTo));
  let savepath =
    Os.tempPath ~fresh:true fspathTo
      (match Path.deconstructRev realPathTo with
         Some (nm, _) -> Path.addSuffixToFinalName
                           (Path.child Path.empty nm) "-bad"
       | None         -> Path.fromString "bad")
  in
  (* BCP: 12/17: Added a try around this call so that, if we're in the middle of failing
     when we do this, we don't fail again and confuse the user about the reason for the
     failure! *)
  begin try Os.rename "save temp" fspathTo pathTo fspathTo savepath with Util.Transient _ -> () end;
  Lwt.fail
    (Util.Transient
       (Printf.sprintf
        "The file %s was incorrectly transferred  (fingerprint mismatch in %s) \
         -- temp file saved as %s"
        (Path.toString pathTo)
        reason
        (Fspath.toDebugString (Fspath.concat fspathTo savepath))))

let saveTempFileOnRoot =
  Remote.registerRootCmd "saveTempFile"
    Umarshal.(prod3 Path.mlocal Path.mlocal string id id) Umarshal.unit
    saveTempFileLocal

(****)

let removeOldTempFile fspathTo pathTo =
  if Os.exists fspathTo pathTo then begin
    debug (fun() -> Util.msg "Removing old %s / %s\n"
           (Fspath.toDebugString fspathTo) (Path.toString pathTo));
    Os.delete fspathTo pathTo
  end

(* There is an issue that not all threads are immediately cancelled when there
   is a connection error. A waiting thread (in this case probably a thread in
   one of the Lwt regions) may have been started and could open an fd but may
   never be able to complete. [protect], [lwt_protect] and any other cleanup
   code may never be triggered in this scenario because the thread just stops
   (as eventually the connection cleanup kicks in and all threads are stopped).
   As a hacky(?) solution, keep track of all open fds and close them when the
   connection breaks. *)
let inFdResource = Remote.resourceWithConnCleanup close_in close_in_noerr
let outFdResource = Remote.resourceWithConnCleanup close_out close_out_noerr
(* Publication owns its directory handles and a separate stage witness. Clean
   its owned name before channels close; invalidate range leases first. *)
let clonePublicationResource = Remote.resourceWithConnCleanup
  StagePublication.abort_and_close StagePublication.close_noerr
(* Registered later, therefore invalidated before the channel registries on
   connection teardown. Leases borrow descriptors and never close them. *)
let cloneLeaseResource = Remote.resourceWithConnCleanup CloneLease.invalidate CloneLease.invalidate

let openFileIn' fspath path kind =
  match kind with
    `DATA ->
      Fs.open_in_bin (Fspath.concat fspath path)
  | `DATA_APPEND len ->
      let ch = Fs.open_in_bin (Fspath.concat fspath path) in
      LargeFile.seek_in ch (Uutil.Filesize.toInt64 len);
      ch
  | `RESS ->
      Osx.openRessIn fspath path

let openFileIn fspath path kind =
  inFdResource.register (openFileIn' fspath path kind)

let closeFileIn = inFdResource.release

let closeFileInNoErr = inFdResource.release_noerr

let openFileOut' fspath path kind len =
  match kind with
    `DATA ->
      let fullpath = Fspath.concat fspath path in
      let flags = [Unix.O_WRONLY; Unix.O_CREAT; Unix.O_CLOEXEC] in
      let perm = if Prefs.read Props.dontChmod then Props.perms Props.fileDefault else 0o600 in
      begin match Sys.win32 with
      | true ->
          Fs.open_out_gen
            [Open_wronly; Open_creat; Open_excl; Open_binary] perm fullpath
      | false ->
          let fd =
            try
              Fs.openfile fullpath (Unix.O_EXCL :: flags) perm
            with
              Unix.Unix_error
                ((Unix.EOPNOTSUPP | Unix.EUNKNOWNERR 524), _, _) ->
              (* O_EXCL not supported under a Netware NFS-mounted filesystem.
                 Solaris and Linux report different errors. *)
                Fs.openfile fullpath (Unix.O_TRUNC :: flags) perm
          in
          Unix.out_channel_of_descr fd
      end
  | `DATA_APPEND len ->
      let fullpath = Fspath.concat fspath path in
      let perm = if Prefs.read Props.dontChmod then Props.perms Props.fileDefault else 0o600 in
      let ch = Fs.open_out_gen [Open_wronly; Open_binary] perm fullpath in
      if not (Prefs.read Props.dontChmod) then Fs.chmod fullpath perm;
      LargeFile.seek_out ch (Uutil.Filesize.toInt64 len);
      ch
  | `RESS ->
      Osx.openRessOut fspath path len

let openFileOut fspath path kind len =
  outFdResource.register (openFileOut' fspath path kind len)

let closeFileOut = outFdResource.release

let closeFileOutNoErr = outFdResource.release_noerr

let openProducerOutput producer fspath path kind len =
  match producer with
  | None | Some { legacy = true; _ } -> openFileOut fspath path kind len
  | Some state ->
      checkProducer producer;
      let output = match kind with
        | `RESS -> openFileOut fspath path kind len
        | `DATA | `DATA_APPEND _ ->
            let perm = if Prefs.read Props.dontChmod then Props.perms Props.fileDefault else 0o600 in
            let flags = [Unix.O_WRONLY; Unix.O_CLOEXEC; Unix.O_NONBLOCK] in
            let flags = match kind with
              | `DATA -> Unix.O_CREAT :: Unix.O_EXCL :: flags
              | _ -> flags in
            let descriptor = Fs.openfile (Fspath.concat fspath path) flags perm in
            let output =
              try
                adoptProducer producer descriptor;
                Unix.out_channel_of_descr descriptor
              with error -> (try Unix.close descriptor with _ -> ()); raise error in
            (try outFdResource.register output with error ->
               close_out_noerr output; raise error) in
      try
        (match kind with
         | `RESS ->
             checkProducer producer;
             if not (FinalPublication.auxiliary_absent (TargetBinding.native state.binding)) then
               handoffProducer producer
             else adoptProducer producer (Unix.descr_of_out_channel output)
         | `DATA -> ()
         | `DATA_APPEND offset ->
             if not (Prefs.read Props.dontChmod) then
               Unix.fchmod (Unix.descr_of_out_channel output) 0o600;
             if offset = Uutil.Filesize.zero then
               Unix.LargeFile.ftruncate (Unix.descr_of_out_channel output) 0L;
             LargeFile.seek_out output (Uutil.Filesize.toInt64 offset));
        checkProducer producer;
        output
      with error ->
        (try closeFileOutNoErr output with _ -> close_out_noerr output);
        raise error

(* Before channels are handed to the normal lifecycle, allocation/registration
   failures must still settle both native clone descriptors. Error cleanup may
   itself fail to unregister; closing the channel then leaves no live fd in a
   retained registry entry. Never close its original integer again. *)
let closeCloneFdNoErr fd = try Unix.close fd with _ -> ()
let closeCloneInputNoErr channel =
  try closeFileInNoErr channel with _ ->
    (try close_in_noerr channel with _ -> ())
let closeCloneOutputNoErr channel =
  try closeFileOutNoErr channel with _ ->
    (try close_out_noerr channel with _ -> ())
let unlinkCloneNoErr path = try Fs.unlink path with _ -> ()
let cloneChannels basisFd outputFd =
  let output =
    try Unix.out_channel_of_descr outputFd with error ->
      closeCloneFdNoErr basisFd; closeCloneFdNoErr outputFd; raise error in
  let basis =
    try Unix.in_channel_of_descr basisFd with error ->
      (try close_out_noerr output with _ -> ());
      closeCloneFdNoErr basisFd; raise error in
  try
    ignore (inFdResource.register basis);
    ignore (outFdResource.register output);
    (basis, output)
  with error ->
    closeCloneInputNoErr basis; closeCloneOutputNoErr output; raise error

let cloneOwnerIdentity () =
  (* A controller identity cannot be inherited from a prior process or mount.
     Allocate the buffer before taking ownership of the temporary random fd. *)
  let bytes = Bytes.create 32 in
  let fd = Unix.openfile "/dev/urandom" [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  try
    let rec read position =
      if position < Bytes.length bytes then begin
        let rec read_once () =
          try Unix.read fd bytes position (Bytes.length bytes - position)
          with Unix.Unix_error (Unix.EINTR, _, _) -> read_once () in
        let count = read_once () in
        if count = 0 then raise End_of_file;
        read (position + count)
      end in
    read 0;
    let identity = "clone-owner:" ^ Bytes.to_string bytes in
    Unix.close fd;
    identity
  with error -> closeCloneFdNoErr fd; raise error

let enrollCloneLease basis output =
  let owner = CloneLease.create_owner ~instance_id:(cloneOwnerIdentity ()) in
  match CloneLease.enroll owner ~backend_revision:"apfs-stage-copy/1"
    ~source:basis ~destination:output with
  | Ok lease -> Some lease
  | Error (CloneLease.Invalidated (CloneLease.Identity_unavailable _)) ->
      CloneLease.close_owner owner;
      if Prefs.read clonePolicy = "require" then
        raise (Util.Transient "Clone volume identity is unavailable");
      None
  | Error error -> CloneLease.close_owner owner; raise error

let registerCloneLease lease =
  try cloneLeaseResource.register lease with error ->
    CloneLease.invalidate lease;
    (try cloneLeaseResource.release_noerr lease with _ -> ());
    raise error
let releaseCloneLease lease =
  CloneLease.invalidate lease;
  try cloneLeaseResource.release_noerr lease with _ -> ()

let closeClonePublicationNoErr publication =
  try clonePublicationResource.release_noerr publication with _ ->
    StagePublication.close_noerr publication

let registerClonePublication publication =
  try clonePublicationResource.register publication with error ->
    closeClonePublicationNoErr publication;
    raise error

let prepareClonePublication directory stage temporary =
  try
    let publication = StagePublication.prepare
      ~working_dir:(Fspath.toString directory)
      ~stage:(Path.toString stage) ~temporary:(Path.toString temporary) in
    (* The option allocation precedes registration; the finalizable owner is
       also explicitly closed if this synchronous handoff fails. *)
    begin try Some publication with error ->
      StagePublication.close_noerr publication; raise error end
  with error when StagePublication.preparation_unavailable error ->
    if Prefs.read clonePolicy = "require" then
      raise (Util.Transient "Clone publication identity is unavailable");
    None

let checkCloneLease lease =
  match CloneLease.observe lease with
  | Ok current when current = CloneLease.expected lease -> ()
  | Ok _ | Error (CloneLease.Invalidated _) ->
      raise (Util.Transient "Clone basis or stage binding changed")
  | Error error -> raise error

let setFileinfo fspathTo pathTo realPathTo update desc =
  match update with
    `Update _ -> Fileinfo.set fspathTo pathTo (`Copy realPathTo) desc
  | `Copy     -> Fileinfo.set fspathTo pathTo (`Set Props.fileDefault) desc

(****)

(* This unfortunate complexity is here to reduce network round-trips
   and calls to [Update.translatePath], primarily in [Files.setProp]. *)
let mxpath = Umarshal.(sum2 Path.mlocal Path.m)
               (function `Local p -> I21 p | `Global p -> I22 p)
               (function I21 p -> `Local p | I22 p -> `Global p)

let loadPropsExtDataLocal (fspath, path, desc) =
  let localPath = match path with
    | `Local p -> p
    | `Global p -> Update.translatePathLocal fspath p in
  (Some localPath, Props.loadExtData fspath localPath desc)

let loadPropsExtDataOnServer = Remote.registerServerCmd "propsExtData"
  Umarshal.(prod3 Fspath.m mxpath Props.m id id)
  Umarshal.(prod2 (option Path.mlocal) Props.mx id id)
  (fun connFrom args -> Lwt.return (loadPropsExtDataLocal args))

let propsWithExtDataLocal fspath path desc =
  try (None, Props.withExtData desc)
  with Not_found -> loadPropsExtDataLocal (fspath, path, desc)

let propsWithExtDataConn connFrom fspath path desc =
  try Lwt.return (None, Props.withExtData desc)
  with Not_found -> loadPropsExtDataOnServer connFrom (fspath, path, desc)

let propsExtDataOnRoot root path desc =
  match root with
  | (Common.Local, fspath) ->
      Lwt.return (propsWithExtDataLocal fspath path desc)
  | (Remote _, fspath) ->
      propsWithExtDataConn (Remote.connectionOfRoot root) fspath path desc

let propsWithExtData connFrom fspath path desc =
  propsWithExtDataConn connFrom fspath (`Local path) desc >>= fun x ->
  Lwt.return (snd x)

let readPropsExtData root path desc =
  propsExtDataOnRoot root (`Local path) desc >>= fun x ->
  Lwt.return (snd x)

let readPropsExtDataG root path desc =
  propsExtDataOnRoot root (`Global path) desc

(****)

let copyFileRange src dst src_offs len fallback notify =
  let open Uutil in
  match CopyRange.run ~max_chunk:10_485_760 (* 10 MiB; periodic progress *)
    ~source_offset:(Filesize.toInt64 src_offs) ~length:(Filesize.toInt64 len)
    ~step:(fun ~source_offset ~length -> Fs.copy_file src dst source_offset length)
    ~notify:(fun n -> notify (Filesize.ofInt n)) () with
  | CopyRange.Copied _ -> ()
  | CopyRange.Unsupported (progress, error) ->
      debug (fun () -> Util.msg
        "Falling back to regular copy: copyFileRange failed [%s]%s\n"
        (Unix.error_message error.errno)
        (if progress.completed = 0L then "" else
          " (copied " ^ Int64.to_string progress.completed ^ ")"));
      fallback (Filesize.ofInt64 progress.completed)
  | CopyRange.Failed (_, CopyRange.System_error error) ->
      raise (Unix.Unix_error (error.errno, error.operation, error.argument))
  | CopyRange.Failed (progress, CopyRange.No_progress) ->
      raise (Util.Transient (Printf.sprintf
        "Accelerated copy stopped after %Ld of %Ld bytes"
        progress.completed progress.requested))
  | CopyRange.Failed (_, CopyRange.Invalid_progress { returned; requested }) ->
      raise (Util.Transient (Printf.sprintf
        "Accelerated copy returned an invalid count (%d for %d requested bytes)"
        returned requested))

let copyClonedRange lease input output source_offset length =
  let destination_offset = LargeFile.pos_out output in
  let capabilities = { CloneRange.native_whole = true; composed_whole = false;
    range = None; max_copy_bytes = 10_485_760L } in
  let request = { CloneRange.source_offset; destination_offset; length } in
  let perform ~source ~destination (operation : CloneRange.operation) =
    let copied = ref 0L in
    let prefix () = { CloneRange.shared = 0L; copied = !copied } in
    try
      if Unix.descr_of_in_channel input <> source ||
         Unix.descr_of_out_channel output <> destination then
        raise (Util.Transient "Clone range channels do not match their held descriptors");
      (* APFS has whole-file cloning, not a qualified native range-share API.
         Ordinary reconstruction still uses bounded exact-offset operations. *)
      match operation.kind with
      | CloneRange.Share -> CloneRange.Unsupported { prefix = prefix ();
          reason = "APFS range sharing is unavailable"; mutation = CloneRange.Known_prefix }
      | CloneRange.Copy ->
          flush output;
          LargeFile.seek_out output operation.destination_offset;
          let fallback completed =
            let completed = Uutil.Filesize.toInt64 completed in
            LargeFile.seek_in input (Int64.add operation.source_offset completed);
            LargeFile.seek_out output (Int64.add operation.destination_offset completed);
            Uutil.readWriteBounded input output
              (Uutil.Filesize.ofInt64 (Int64.sub operation.length completed)) (fun _ -> ())
          in
          copyFileRange source destination (Uutil.Filesize.ofInt64 operation.source_offset)
            (Uutil.Filesize.ofInt64 operation.length) fallback
            (fun count -> copied := Int64.add !copied (Uutil.Filesize.toInt64 count));
          flush output;
          let ending = Int64.add operation.destination_offset operation.length in
          if Unix.LargeFile.lseek destination 0L Unix.SEEK_CUR <> ending then
            raise (Util.Transient "Clone range ended before its requested length");
          (* Native copying advances the fd, not the channel's cached offset. *)
          LargeFile.seek_out output ending;
          CloneRange.Copied operation.length
    with error ->
      (* A failed native call or buffered fallback can have an unreported
         effect. Preserve only reported progress and discard, never retry. *)
      CloneRange.Error { prefix = prefix (); error; mutation = CloneRange.Indeterminate }
  in
  match CloneLease.execute lease ~capabilities ~request ~perform
    ~check_cancel:Abort.checkAll ~notify:(fun _ _ -> ()) () with
  | CloneRange.Complete _ -> ()
  | CloneRange.Stopped { fault = CloneRange.Adapter_error error; _ }
  | CloneRange.Stopped { fault = CloneRange.Observation_failed error; _ } ->
      (match error with CloneLease.Invalidated _ ->
        raise (Util.Transient "Clone basis or stage binding changed") | _ -> raise error)
  | CloneRange.Stopped _ -> raise (Util.Transient "Clone range binding or progress is invalid")

let copyFile inCh outCh kind len fallback notify =
  (* Flush the buffered output channel just in case since we're going to
     manipulate the channel's underlying fd directly. *)
  flush outCh;
  let src = Unix.descr_of_in_channel inCh
  and dst = Unix.descr_of_out_channel outCh in
  if kind = `DATA && receiverCloneEnabled () && Fs.clone_file src dst then
    notify len
  else
    let tryCopyFileRange src dst src_offs len fallback notify =
      let fallback' copied =
        (* Fallback to read-write loop expects that seek positions in input
           and output fds have not changed. By invariant, if [copyFileRange]
           succeeded partially then the seek position of output fd was updated
           accordingly. To not break fallback, the seek position of input fd
           must be updated by the same amount. *)
        let open Uutil in
        if copied <> Filesize.zero then begin
          let pos =
            Int64.add (Filesize.toInt64 src_offs) (Filesize.toInt64 copied) in
          LargeFile.seek_in inCh pos
        end;
        fallback ()
      in
      copyFileRange src dst src_offs len fallback' notify
    in
    match kind with
    | `DATA -> tryCopyFileRange src dst Uutil.Filesize.zero len fallback notify
    | `DATA_APPEND offs -> tryCopyFileRange src dst offs len fallback notify
    | `RESS -> fallback ()

let copyBoundClone producer basisPath directory candidate suffix write =
  checkProducer producer;
  let stage = Os.tempPath ~fresh:true directory
    (Path.addSuffixToFinalName candidate suffix) in
  match prepareClonePublication directory stage candidate with
  | None -> false
  | Some prepared ->
      let publication = registerClonePublication prepared in
      try
        match Fs.clone_stage_handles basisPath (Fspath.concat directory stage) with
        | Fs.Declined_stage_handles Fs.Non_regular_source ->
            raise (Util.Transient "Clone producer basis is no longer a regular file")
        | Fs.Declined_stage_handles _ ->
            closeClonePublicationNoErr publication; false
        | Fs.Shared_stage_handles (basisFd, outputFd, parent) ->
            (try StagePublication.adopt publication ~parent ~stage:outputFd
             with error ->
               closeCloneFdNoErr basisFd; closeCloneFdNoErr outputFd; raise error);
            (* cloneChannels consumes both descriptors even on a failed
               handoff. From here cleanup uses channel objects, never their
               recycled original descriptor integers. *)
            let basis, output = cloneChannels basisFd outputFd in
            (try
               write basis output;
               flush output;
               StagePublication.publish publication;
               adoptProducer producer outputFd;
               StagePublication.disarm publication;
               closeFileIn basis; closeFileOut output;
               closeClonePublicationNoErr publication;
               true
             with error ->
               closeClonePublicationNoErr publication;
               closeCloneInputNoErr basis; closeCloneOutputNoErr output;
               raise error)
      with error -> closeClonePublicationNoErr publication; raise error

let copyByPath ?producer fspathFrom pathFrom fspathTo pathTo =
  if not (receiverCloneEnabled ()) then false else
  match producer with
  | None | Some { legacy = true; _ } ->
      Fs.clone_path (Fspath.concat fspathFrom pathFrom) (Fspath.concat fspathTo pathTo)
  | Some _ ->
      copyBoundClone producer (Fspath.concat fspathFrom pathFrom)
        fspathTo pathTo "-source-clone" (fun _ _ -> ())

(* The fds opened in this function normally shouldn't be tracked for extra
   cleanup at connection close because this is sequential non-Lwt code. Yet,
   there is a risk that code called by [Uutil.showProgress] may include Lwt
   code. For this reason only, it is better to include the fds in this
   function in the fd cleanup scheme (done automatically by [openFile*] and
   [closeFile*] functions). *)
let copyContents ?producer fspathFrom pathFrom fspathTo pathTo fileKind fileLength ido =
  let use_id f = match ido with Some id -> f id | None -> () in
  if fileKind = `DATA && copyByPath ?producer fspathFrom pathFrom fspathTo pathTo then
    use_id (fun id -> Uutil.showProgress id fileLength "l")
  else
  (* Open fds only if copying by path did not work *)
  let inFd = openFileIn fspathFrom pathFrom fileKind in
  protect
    (fun () ->
       let outFd = openProducerOutput producer fspathTo pathTo fileKind fileLength in
       protect
         (fun () ->
            let showProgress l =
                 use_id (fun id ->
(* (Util.msg "Copied file %s (%d bytes)\n" (Path.toString pathFrom) l); *)
                   if fileKind <> `RESS then Abort.checkAll ();
                   Uutil.showProgress id l "l")
            in
            let fallback () = Uutil.readWriteBounded inFd outFd fileLength
              (fun l -> showProgress (Uutil.Filesize.ofInt l)) in
            copyFile inFd outFd fileKind fileLength fallback showProgress;
            flush outFd;
            checkProducer producer;
            closeFileIn inFd;
            closeFileOut outFd;
(* ignore (Sys.command ("ls -l " ^ (Fspath.toString (Fspath.concat fspathTo pathTo)))) *)
         )
         (fun () -> closeFileOutNoErr outFd))
    (fun () -> closeFileInNoErr inFd)

(* A bounded local producer for cross-volume updates. Unlike remote rsync this
   must read both streams, but avoids rewriting identical inherited intervals.
   Snapshot reads stay separate from writes even when the source is shifted. *)
let copyLocalClonedLegacy source basisPath fspathTo pathTo fileLength ido =
  let clonedPath = Os.tempPath ~fresh:false fspathTo
    (Path.addSuffixToFinalName pathTo "-local-clone") in
  removeOldTempFile fspathTo clonedPath;
  let cloneFullPath = Fspath.concat fspathTo clonedPath in
  match Fs.clone_stage_status basisPath cloneFullPath with
  | Fs.Declined_stage Fs.Non_regular_source ->
      raise (Util.Transient "Clone basis is no longer a regular file")
  | Fs.Declined_stage reason ->
      let why = Fs.clone_stage_decline_reason reason in
      debug (fun () -> Util.msg "Local clone declined: %s\n" why);
      if Prefs.read clonePolicy = "require" then
        raise (Util.Transient ("Receiver filesystem cannot clone this basis: " ^ why));
      false
  | Fs.Shared_stage (basisFd, outputFd) ->
      let basis, output =
        try cloneChannels basisFd outputFd with error ->
          unlinkCloneNoErr cloneFullPath; raise error in
      try
        let source = Fs.open_in_bin source in
        let source =
          try inFdResource.register source with error ->
            closeCloneInputNoErr source; raise error in
        try
          let a = Bytes.create 131072 and b = Bytes.create 131072 in
          let read ch buf len =
            let rec loop pos =
              if pos = len then pos else
              let n = Stdlib.input ch buf pos (len - pos) in
              if n = 0 then pos else loop (pos + n)
            in loop 0
          in
          let remaining = ref (Uutil.Filesize.toInt64 fileLength)
          and skipped = ref 0L in
          while !remaining > 0L do
            Abort.checkAll ();
            let n = Int64.to_int (min !remaining 131072L) in
            if read source a n <> n then raise End_of_file;
            let m = read basis b n in
            if m = n && Bytes.sub a 0 n = Bytes.sub b 0 n then begin
              LargeFile.seek_out output (Int64.add (LargeFile.pos_out output) (Int64.of_int n));
              skipped := Int64.add !skipped (Int64.of_int n)
            end else Stdlib.output output a 0 n;
            remaining := Int64.sub !remaining (Int64.of_int n);
            (match ido with None -> () | Some id ->
               Uutil.showProgress id (Uutil.Filesize.ofInt n) "l")
          done;
          flush output;
          Unix.LargeFile.ftruncate outputFd (Uutil.Filesize.toInt64 fileLength);
          closeFileIn source;
          closeFileIn basis; closeFileOut output;
          Fs.rename (Fspath.concat fspathTo clonedPath) (Fspath.concat fspathTo pathTo);
          debug (fun () -> Util.msg "Local receiver clone preserved %Ld logical bytes\n" !skipped);
          true
        with error -> closeCloneInputNoErr source; raise error
      with e ->
        closeCloneInputNoErr basis; closeCloneOutputNoErr output;
        unlinkCloneNoErr cloneFullPath;
        raise e

let copyLocalCloned ?producer source basisPath fspathTo pathTo fileLength ido =
  match producer with
  | None | Some { legacy = true; _ } ->
      copyLocalClonedLegacy source basisPath fspathTo pathTo fileLength ido
  | Some _ ->
      let copied = copyBoundClone producer basisPath fspathTo pathTo "-local-clone"
        (fun basis output ->
          let input = openFileIn (Fspath.canonize (Some (Fspath.toString source))) Path.empty `DATA in
          protect (fun () ->
            let incoming = Bytes.create 131072 and previous = Bytes.create 131072 in
            let read channel buffer length =
              let rec loop offset = if offset = length then offset else
                let count = Stdlib.input channel buffer offset (length - offset) in
                if count = 0 then offset else loop (offset + count) in loop 0 in
            let remaining = ref (Uutil.Filesize.toInt64 fileLength) in
            while !remaining > 0L do
              Abort.checkAll ();
              let count = Int64.to_int (min !remaining 131072L) in
              if read input incoming count <> count then raise End_of_file;
              if read basis previous count = count &&
                 Bytes.sub incoming 0 count = Bytes.sub previous 0 count then
                LargeFile.seek_out output (Int64.add (LargeFile.pos_out output) (Int64.of_int count))
              else Stdlib.output output incoming 0 count;
              remaining := Int64.sub !remaining (Int64.of_int count);
              (match ido with None -> () | Some id ->
                Uutil.showProgress id (Uutil.Filesize.ofInt count) "l")
            done;
            flush output;
            Unix.LargeFile.ftruncate (Unix.descr_of_out_channel output) (Uutil.Filesize.toInt64 fileLength);
            closeFileIn input)
            (fun () -> closeFileInNoErr input)) in
      if not copied && Prefs.read clonePolicy = "require" then
        raise (Util.Transient "Receiver filesystem cannot create a bound clone producer");
      copied

let localFileContents ?producer ?basis fspathFrom pathFrom fspathTo pathTo desc ressLength ido =
  Util.convertUnixErrorsToTransient
    "copying locally"
    (fun () ->
      debug (fun () ->
        Util.msg "Copy.localFile %s / %s to %s / %s\n"
          (Fspath.toDebugString fspathFrom) (Path.toString pathFrom)
          (Fspath.toDebugString fspathTo) (Path.toString pathTo));
      checkProducer producer;
      removeOldTempFile fspathTo pathTo;
      checkProducer producer;
      let cloned = match basis with
        | Some previous when receiverCloneEnabled () ->
            (* Prefer cloning the actual source when it is on this volume. *)
            let completed = copyByPath ?producer fspathFrom pathFrom fspathTo pathTo in
            if completed then begin
              (match ido with None -> () | Some id ->
                Uutil.showProgress id (Props.length desc) "l");
              true
            end else if Prefs.read Props.dontChmod then false else
              copyLocalCloned ?producer (Fspath.concat fspathFrom pathFrom)
                (Fspath.concat fspathTo previous) fspathTo pathTo (Props.length desc) ido
        | _ -> false in
      if not cloned then copyContents ?producer
        fspathFrom pathFrom fspathTo pathTo `DATA (Props.length desc) ido;
      if ressLength > Uutil.Filesize.zero then
        copyContents ?producer
          fspathFrom pathFrom fspathTo pathTo `RESS ressLength ido)

let localFileWithProducer ?producer
     fspathFrom pathFrom fspathTo pathTo realPathTo update desc ressLength ido =
  Util.convertUnixErrorsToTransient "copying locally" (fun () ->
    let basis = match update with `Copy -> None | `Update _ -> Some realPathTo in
    localFileContents ?producer ?basis fspathFrom pathFrom fspathTo pathTo desc ressLength ido;
    checkProducer producer;
    let (_, desc) = propsWithExtDataLocal fspathFrom (`Local pathFrom) desc in
    checkProducer producer;
    setFileinfo fspathTo pathTo realPathTo update desc;
    checkProducer producer)

let localFile fspathFrom pathFrom fspathTo pathTo realPathTo update desc ressLength ido =
  localFileWithProducer fspathFrom pathFrom fspathTo pathTo realPathTo update desc ressLength ido

(* The main local-local path may suspend for typed semantic workers. Auxiliary
   localFile callers (recursive copies, moved-file reuse, merge work) retain
   the synchronous ordinary copier and never run semantic proofs on the owner. *)
let localFileAsync ?producer
     fspathFrom pathFrom fspathTo pathTo realPathTo update desc ressLength ido =
  let ordinary () =
    localFileWithProducer ?producer fspathFrom pathFrom fspathTo pathTo realPathTo update desc ressLength ido;
    Lwt.return () in
  match update with
  | `Update _ when receiverCloneEnabled () && not (Prefs.read Props.dontChmod) &&
                   SemanticSync.is_enabled () ->
    Util.convertUnixErrorsToTransient "copying locally" (fun () ->
      checkProducer producer;
      removeOldTempFile fspathTo pathTo;
      checkProducer producer;
      let copied =
        if copyByPath ?producer fspathFrom pathFrom fspathTo pathTo then begin
          debug (fun () -> Util.msg "Local source clone completed before semantic planning\n");
          Lwt.return true
        end
        else let transfer = match producer with
          | None -> SemanticSync.try_local_async
          | Some state ->
              match TargetBinding.reservation state.binding with
              | Some reservation -> SemanticSync.try_local_async_reserved ~reservation
                  ~producer:(if state.legacy then None else Some (adoptProducer producer))
              | None -> if state.legacy then SemanticSync.try_local_async
                  else SemanticSync.try_local_async_with_producer ~producer:(adoptProducer producer) in
          transfer ~source:(Fspath.concat fspathFrom pathFrom)
            ~basis:(Fspath.concat fspathTo realPathTo) ~directory:fspathTo ~staging:pathTo in
      copied >>= fun copied ->
      if not copied then ordinary () else
      Util.convertUnixErrorsToTransient "finishing local copy" (fun () ->
        (match ido with None -> () | Some id ->
          Uutil.showProgress id (Props.length desc) "l");
        if ressLength > Uutil.Filesize.zero then
          copyContents ?producer fspathFrom pathFrom fspathTo pathTo `RESS ressLength ido;
        checkProducer producer;
        let (_, desc) = propsWithExtDataLocal fspathFrom (`Local pathFrom) desc in
        checkProducer producer;
        setFileinfo fspathTo pathTo realPathTo update desc;
        checkProducer producer;
        Lwt.return ()))
  | _ -> ordinary ()

(****)

let tryCopyMovedFile connFrom fspathFrom pathFrom fspathTo pathTo realPathTo
      update desc fp ress id =
  if not (Prefs.read Xferhint.xferbycopying) then Lwt.return None else
  Util.convertUnixErrorsToTransient "tryCopyMovedFile" (fun() ->
    debug (fun () -> Util.msg "tryCopyMovedFile: -> %s /%s/\n"
      (Path.toString pathTo) (Os.fullfingerprint_to_string fp));
    match Xferhint.lookup fp with
      None ->
        Lwt.return None
    | Some (candidateFspath, candidatePath, hintHandle) ->
        debug (fun () ->
          Util.msg
            "tryCopyMovedFile: found match at %s,%s. Try local copying\n"
            (Fspath.toDebugString candidateFspath)
            (Path.toString candidatePath));
        try
          (* If candidateFspath is the replica root, the argument
             [true] is correct.  Otherwise, we don't expect to point
             to a symlink, and therefore we still get the correct
             result. *)
          let info = Fileinfo.getBasic true candidateFspath candidatePath in
          if
            info.Fileinfo.typ <> `ABSENT &&
            Props.length info.Fileinfo.desc = Props.length desc
          then begin
            localFileContents candidateFspath candidatePath fspathTo pathTo desc
              (Osx.ressLength ress) (Some id);
            propsWithExtData connFrom fspathFrom pathFrom desc >>= fun desc ->
            setFileinfo fspathTo pathTo realPathTo update desc;
            let (info, isTransferred) =
              fileIsTransferred fspathTo pathTo desc fp ress in
            if isTransferred then begin
              debug (fun () -> Util.msg "tryCopyMoveFile: success.\n");
              let msg =
                Printf.sprintf
                 "Shortcut: copied %s/%s from local file %s/%s\n"
                 (Fspath.toPrintString fspathTo)
                 (Path.toString realPathTo)
                 (Fspath.toPrintString candidateFspath)
                 (Path.toString candidatePath)
              in
              Lwt.return (Some (info, msg))
            end else begin
              debug (fun () ->
                Util.msg "tryCopyMoveFile: candidate file %s modified!\n"
                  (Path.toString candidatePath));
              Xferhint.deleteEntry hintHandle;
              Lwt.return None
            end
          end else begin
            debug (fun () ->
              Util.msg "tryCopyMoveFile: candidate file %s disappeared!\n"
                (Path.toString candidatePath));
            Xferhint.deleteEntry hintHandle;
            Lwt.return None
          end
        with
          Util.Transient s ->
            debug (fun () ->
              Util.msg
                "tryCopyMovedFile: local copy from %s didn't work [%s]\n"
                (Path.toString candidatePath) s);
            Xferhint.deleteEntry hintHandle;
            Lwt.return None)

(* Qualify a reuse hint before creating the bound output. A stale hint can be
   skipped then; after actual production starts, failures must retain their
   identity error rather than retry against a different candidate object. *)
let tryCopyMovedFileBound producer connFrom fspathFrom pathFrom fspathTo pathTo
      realPathTo update desc fp ress id =
  if not (Prefs.read Xferhint.xferbycopying) then Lwt.return None else
  match Xferhint.lookup fp with
  | None -> Lwt.return None
  | Some (candidateFspath, candidatePath, hintHandle) ->
      let qualified =
        try
          let info = Fileinfo.getBasic true candidateFspath candidatePath in
          info.Fileinfo.typ = `FILE &&
          Props.length info.Fileinfo.desc = Props.length desc &&
          Os.fingerprint candidateFspath candidatePath info.Fileinfo.typ = fp
        with Util.Transient _ | Unix.Unix_error _ -> false in
      if not qualified then begin
        Xferhint.deleteEntry hintHandle;
        Lwt.return None
      end else begin
        checkProducer producer;
        localFileContents ?producer candidateFspath candidatePath fspathTo pathTo
          desc (Osx.ressLength ress) (Some id);
        propsWithExtData connFrom fspathFrom pathFrom desc >>= fun desc ->
        checkProducer producer;
        setFileinfo fspathTo pathTo realPathTo update desc;
        checkProducer producer;
        paranoidCheck ?producer fspathTo pathTo realPathTo desc fp ress
          >>= fun status ->
        let msg = Printf.sprintf "Shortcut: copied %s/%s from local file %s/%s\n"
          (Fspath.toPrintString fspathTo) (Path.toString realPathTo)
          (Fspath.toPrintString candidateFspath) (Path.toString candidatePath) in
        Lwt.return (Some (status, msg))
      end

(****)

(* The file transfer functions here depend on an external module
   'transfer' that implements a generic transmission and the rsync
   algorithm for optimizing the file transfer in the case where a
   similar file already exists on the target. *)

let rsyncActivated =
  Prefs.createBool "rsync" true
    ~category:(`Advanced `Remote)
    "activate the rsync transfer mode"
    ("Unison uses the 'rsync algorithm' for 'diffs-only' transfer "
     ^ "of updates to large files.  Setting this flag to false makes Unison "
     ^ "use whole-file transfers instead.  Under normal circumstances, "
     ^ "there is no reason to do this, but if you are having trouble with "
     ^ "repeated 'rsync failure' errors, setting it to "
     ^ "false should permit you to synchronize the offending files.")

let decompressor = ref Remote.MsgIdMap.empty

let resetDecompressorState () =
  decompressor := Remote.MsgIdMap.empty
let () = Remote.at_conn_close resetDecompressorState

let processTransferInstruction conn (file_id, ti) =
  Util.convertUnixErrorsToTransient
    "processing a transfer instruction"
    (fun () ->
       ignore ((fst (Remote.MsgIdMap.find file_id !decompressor)) ti))

let marshalTransferInstruction =
  (fun _ (file_id, (data, pos, len)) rem ->
     (Remote.encodeInt file_id :: (data, pos, len) :: rem,
      len + Remote.intSize)),
  (fun _ buf pos ->
     let len = Bytearray.length buf - pos - Remote.intSize in
     (Remote.decodeInt buf pos, (buf, pos + Remote.intSize, len)))

let streamTransferInstruction =
  Remote.registerStreamCmd
    "processTransferInstruction" marshalTransferInstruction
    processTransferInstruction

let showPrefixProgress id kind =
  match kind with
    `DATA_APPEND len -> Uutil.showProgress id len "r"
  | _                -> ()

let compress conn
     ((biOpt, fspathFrom, pathFrom, fileKind), (sizeFrom, id, file_id)) =
  Lwt.catch
    (fun () ->
       streamTransferInstruction conn
         (fun processTransferInstructionRemotely ->
            (* We abort the file transfer on error if it has not
               already started *)
            if fileKind <> `RESS then Abort.check id;
            let infd = openFileIn fspathFrom pathFrom fileKind in
            lwt_protect
              (fun () ->
                 showPrefixProgress id fileKind;
                 let showProgress count =
                   if fileKind <> `RESS then Abort.checkAll ();
                   Uutil.showProgress id (Uutil.Filesize.ofInt count) "r" in
                 let compr =
                   match biOpt with
                     None ->
                       Transfer.send infd sizeFrom showProgress
                   | Some bi ->
                       Transfer.Rsync.rsyncCompress
                         bi infd sizeFrom showProgress
                 in
                 compr
                   (fun ti -> processTransferInstructionRemotely (file_id, ti))
                       >>= fun () ->
                 closeFileIn infd;
                 Lwt.return ())
              (fun () ->
                 closeFileInNoErr infd)))
    (fun e ->
       (* We cannot wrap the code above with the handler below,
          as the code is executed asynchronously. *)
       Util.convertUnixErrorsToTransient "transferring file contents"
         (fun () -> raise e))

let mdata = Umarshal.(sum3 unit Uutil.Filesize.m unit
                        (function
                         | `DATA -> I31 ()
                         | `DATA_APPEND a -> I32 a
                         | `RESS -> I33 ())
                        (function
                         | I31 () -> `DATA
                         | I32 a -> `DATA_APPEND a
                         | I33 () -> `RESS))

let mcompress = Umarshal.(prod2
                            (prod4 (option Transfer.Rsync.mrsync_block_info) Fspath.m Path.mlocal mdata id id)
                            (prod3 Uutil.Filesize.m Uutil.File.m int id id)
                            id id)

let compressRemotely =
  Remote.registerServerCmd "compress" mcompress Umarshal.unit compress

let close_all infd outfd =
  Util.convertUnixErrorsToTransient
    "closing files"
    (fun () ->
       begin match !infd with
         Some fd -> closeFileIn fd; infd := None
       | None    -> ()
       end;
       begin match !outfd with
         Some fd -> closeFileOut fd; outfd := None
       | None    -> ()
       end)

let close_all_no_error infd outfd =
  begin match !infd with
    Some fd -> closeFileInNoErr fd
  | None    -> ()
  end;
  begin match !outfd with
    Some fd -> closeFileOutNoErr fd
  | None    -> ()
  end

(* Lazy creation of the destination file *)
let destinationFd ?producer fspath path kind len outfd id =
  match !outfd with
    None    ->
      (* We abort the file transfer on error if it has not
         already started *)
      if kind <> `RESS then Abort.check id;
      let fd = openProducerOutput producer fspath path kind len in
      showPrefixProgress id kind;
      outfd := Some fd;
      fd
  | Some fd ->
      fd

(* Lazy opening of the reference file (for rsync algorithm) *)
let referenceFd fspath path kind infd =
  match !infd with
    None ->
      let fd = match kind with
        | `RESS -> openFileIn fspath path kind
        | `DATA | `DATA_APPEND _ ->
            (* An optional clone/publication probe can decline before opening
               the basis. Ordinary rsync still must reject a replaced FIFO
               without blocking and must retain only regular data inputs. *)
            let raw = Fs.openfile (Fspath.concat fspath path)
              [Unix.O_RDONLY; Unix.O_NONBLOCK; Unix.O_CLOEXEC] 0 in
            let channel =
              try
                if (Unix.LargeFile.fstat raw).Unix.LargeFile.st_kind <> Unix.S_REG then
                  raise (Util.Transient "Rsync basis is no longer a regular file");
                Unix.in_channel_of_descr raw
              with error -> closeCloneFdNoErr raw; raise error in
            begin try
              (match kind with
               | `DATA_APPEND length -> LargeFile.seek_in channel (Uutil.Filesize.toInt64 length)
               | _ -> ());
              inFdResource.register channel
            with error -> closeCloneInputNoErr channel; raise error end in
      begin try infd := Some fd; fd
      with error -> closeCloneInputNoErr fd; raise error end
  | Some fd ->
      fd

let rsyncReg = Remote.lwtRegionWithConnCleanup (40 * 1024)

let rsyncThrottle useRsync srcFileSize destFileSize f =
  if not useRsync then f () else
  let l = Transfer.Rsync.memoryFootprint srcFileSize destFileSize in
  Lwt_util.run_in_region !rsyncReg l f

let transferFileContents ?producer
      connFrom fspathFrom pathFrom fspathTo pathTo realPathTo update
      fileKind srcFileSize id =
  (* We delay the opening of the files so that there are not too many
     temporary files remaining after a crash, and that they are not
     too many files simultaneously opened. *)
  let outfd = ref None in
  let infd = ref None in
  (* Never expose a partially patched clone as an ordinary resumable prefix.
     Only after EOF is the complete candidate renamed to the normal temp path. *)
  let clonedPath = ref None in
  let clonedLease = ref None in
  let clonedPublication = ref None in
  let inheritedLength = ref 0L in
  let skippedBytes = ref 0L in
  let releaseLease () = match !clonedLease with
    | None -> ()
    | Some lease -> clonedLease := None; releaseCloneLease lease in
  let releasePublication () = match !clonedPublication with
    | None -> ()
    | Some publication ->
        clonedPublication := None;
        closeClonePublicationNoErr publication in
  let discardClone () =
    releaseLease ();
    releasePublication ();
    clonedPath := None
  in
  let showProgress count =
    if fileKind <> `RESS then Abort.checkAll ();
    Uutil.showProgress id (Uutil.Filesize.ofInt count) "r" in

  let destFileSize =
    match update with
      `Copy ->
        Uutil.Filesize.zero
    | `Update (destFileDataSize, destFileRessSize) ->
        match fileKind with
            `DATA | `DATA_APPEND _ -> destFileDataSize
          | `RESS -> destFileRessSize
  in
  let useRsync =
    Prefs.read rsyncActivated
      &&
    Transfer.Rsync.aboveRsyncThreshold destFileSize
      &&
    Transfer.Rsync.aboveRsyncThreshold srcFileSize
  in
  rsyncThrottle useRsync srcFileSize destFileSize (fun () ->
    let (bi, decompr) =
      if useRsync then
        Util.convertUnixErrorsToTransient
          "preprocessing file"
          (fun () ->
             let (bi, blockSize) =
               protect
                 (fun () ->
                    if fileKind = `DATA && receiverCloneEnabled () &&
                       not (Prefs.read Props.dontChmod) then begin
                      if not (StagePublication.available ()) then begin
                        if Prefs.read clonePolicy = "require" then
                          raise (Util.Transient "Clone publication API is unavailable")
                      end else begin
                        let p = Os.tempPath ~fresh:false fspathTo
                          (Path.addSuffixToFinalName realPathTo "-clone") in
                        removeOldTempFile fspathTo p;
                        match prepareClonePublication fspathTo p pathTo with
                        | None -> ()
                        | Some prepared ->
                          let publication = registerClonePublication prepared in
                          begin try
                            clonedPublication := Some publication;
                            match Fs.clone_stage_handles (Fspath.concat fspathTo realPathTo)
                                    (Fspath.concat fspathTo p) with
                            | Fs.Declined_stage_handles Fs.Non_regular_source ->
                                raise (Util.Transient "Clone basis is no longer a regular file")
                            | Fs.Declined_stage_handles reason ->
                                releasePublication ();
                                let why = Fs.clone_stage_decline_reason reason in
                                debug (fun () -> Util.msg "Receiver clone declined: %s\n" why);
                                if Prefs.read clonePolicy = "require" then
                                  raise (Util.Transient ("Receiver filesystem cannot clone this basis: " ^ why))
                            | Fs.Shared_stage_handles (basis, output, parent) ->
                                (* Adoption consumes the actual creation parent and
                                   retains its own stage witness before channels can
                                   fail or close the original output descriptor. *)
                                begin try StagePublication.adopt publication ~parent ~stage:output
                                with error ->
                                  releasePublication ();
                                  closeCloneFdNoErr basis; closeCloneFdNoErr output;
                                  raise error end;
                                let basisChannel, outputChannel =
                                  try cloneChannels basis output with error ->
                                    releasePublication (); raise error in
                                let previousInput = !infd and previousOutput = !outfd
                                and previousClone = !clonedPath and previousLease = !clonedLease in
                                begin try
                                  Unix.LargeFile.ftruncate output (Uutil.Filesize.toInt64 srcFileSize);
                                  match enrollCloneLease basis output with
                                  | None ->
                                      releasePublication ();
                                      closeCloneInputNoErr basisChannel;
                                      closeCloneOutputNoErr outputChannel
                                  | Some lease ->
                                      let lease = registerCloneLease lease in
                                      begin try
                                        clonedLease := Some lease;
                                        clonedPath := Some p;
                                        infd := Some basisChannel;
                                        outfd := Some outputChannel;
                                        inheritedLength := (CloneLease.expected lease).source.size;
                                        debug (fun () -> Util.msg "Using immutable receiver clone basis\n")
                                      with error -> releaseCloneLease lease; raise error end
                                with error ->
                                  releaseLease (); releasePublication ();
                                  infd := previousInput; outfd := previousOutput;
                                  clonedPath := previousClone; clonedLease := previousLease;
                                  closeCloneInputNoErr basisChannel;
                                  closeCloneOutputNoErr outputChannel;
                                  raise error
                                end
                          with error ->
                            releasePublication ();
                            closeClonePublicationNoErr publication;
                            raise error
                          end
                      end
                    end;
                    let ifd = referenceFd fspathTo realPathTo fileKind infd in
                    Transfer.Rsync.rsyncPreprocess ifd srcFileSize destFileSize)
                 (fun () -> discardClone (); close_all_no_error infd outfd)
             in
             if !clonedPath = None then close_all infd outfd;
             (Some bi,
              (* Rsync decompressor *)
              fun ti ->
              let ifd = referenceFd fspathTo realPathTo fileKind infd in
              let fd =
                destinationFd ?producer
                  fspathTo pathTo fileKind srcFileSize outfd id in
              checkProducer producer;
              (match !clonedLease with Some lease -> checkCloneLease lease | None -> ());
              let eof =
                Transfer.Rsync.rsyncDecompress blockSize ifd fd showProgress ti
                  ~copyFn:(fun in_offs len ~fallback ->
                    (* Flush the buffered output channel just in case since
                       we manipulate the channel's underlying fd directly. *)
                    flush fd;
                    let start = Uutil.Filesize.toInt64 in_offs
                    and length = Uutil.Filesize.toInt64 len in
                    let pos = LargeFile.pos_out fd in
                    if !clonedPath <> None && start = pos && length >= 0L &&
                       start <= !inheritedLength &&
                       length <= Int64.sub !inheritedLength start then begin
                      LargeFile.seek_out fd (Int64.add pos length);
                      skippedBytes := Int64.add !skippedBytes length
                    end else
                      match !clonedLease with
                      | Some lease -> copyClonedRange lease ifd fd start length
                      | None -> copyFileRange
                          (Unix.descr_of_in_channel ifd)
                          (Unix.descr_of_out_channel fd)
                          in_offs len fallback (fun _ -> ()))
              in
              if eof then begin
                begin match !clonedPath with
                | None -> ()
                | Some _ ->
                    flush fd;
                    let expected = Uutil.Filesize.toInt64 srcFileSize in
                    if LargeFile.pos_out fd <> expected then
                      raise (Util.Transient "Cloned transfer ended at an unexpected length");
                    Unix.LargeFile.ftruncate (Unix.descr_of_out_channel fd) expected;
                    (match !clonedLease with Some lease -> checkCloneLease lease | None -> ());
                    Abort.checkAll ();
                    let publication = match !clonedPublication with
                      | Some publication -> publication
                      | None -> raise (Util.Transient "Clone publication ownership is unavailable") in
                    StagePublication.publish publication;
                    adoptProducer producer (Unix.descr_of_out_channel fd);
                    StagePublication.disarm publication;
                    releaseLease ();
                    releasePublication ();
                    close_all infd outfd;
                    clonedPath := None;
                    debug (fun () -> Util.msg "Receiver clone preserved %Ld logical bytes\n" !skippedBytes)
                end;
                close_all infd outfd
              end))
      else
        (None,
         (* Simple generic decompressor *)
         fun ti ->
         let fd =
           destinationFd ?producer fspathTo pathTo fileKind srcFileSize outfd id in
         checkProducer producer;
         let eof = Transfer.receive fd showProgress ti in
         checkProducer producer;
         if eof then close_all infd outfd)
    in
    let file_id = Remote.newMsgId () in
    Lwt.catch
      (fun () ->
         debug (fun () -> Util.msg "Starting the actual transfer\n");
         decompressor := Remote.MsgIdMap.add file_id (decompr, (infd, outfd)) !decompressor;
         compressRemotely connFrom
           ((bi, fspathFrom, pathFrom, fileKind), (srcFileSize, id, file_id))
           >>= fun () ->
         decompressor :=
           Remote.MsgIdMap.remove file_id !decompressor; (* For GC *)
         close_all infd outfd;
           (* JV: FIX: the file descriptors are already closed... *)
         Lwt.return ())
      (fun e ->
         decompressor :=
           Remote.MsgIdMap.remove file_id !decompressor; (* For GC *)
         discardClone ();
         close_all_no_error infd outfd;
         Lwt.fail e))

(****)

let transferResourceForkAndSetFileinfo ?producer
      connFrom fspathFrom pathFrom fspathTo pathTo realPathTo
      update desc fp ress id =
  (* Resource fork *)
  debug (fun() -> Util.msg "transferResourceForkAndSetFileinfo %s\n"
    (Path.toString pathTo));
  let ressLength = Osx.ressLength ress in
  begin if ressLength > Uutil.Filesize.zero then begin
    debug (fun() -> Util.msg "starting resource fork transfer for %s\n"
      (Path.toString pathTo));
    transferFileContents ?producer
      connFrom fspathFrom pathFrom fspathTo pathTo realPathTo update
      `RESS ressLength id
  end else
    Lwt.return ()
  end >>= fun () ->
  checkProducer producer;
  propsWithExtData connFrom fspathFrom pathFrom desc >>= fun desc ->
  checkProducer producer;
  setFileinfo fspathTo pathTo realPathTo update desc;
  checkProducer producer;
  debug (fun() -> Util.msg "Resource fork transferred for %s; doing last paranoid check\n"
    (Path.toString realPathTo));
  paranoidCheck ?producer fspathTo pathTo realPathTo desc fp ress

let reallyTransferFile ?producer
      connFrom fspathFrom pathFrom fspathTo pathTo realPathTo
      update desc fp ress id tempInfo =
  debug (fun() -> Util.msg "reallyTransferFile(%s,%s) -> (%s,%s,%s,%s)\n"
      (Fspath.toDebugString fspathFrom) (Path.toString pathFrom)
      (Fspath.toDebugString fspathTo) (Path.toString pathTo)
      (Path.toString realPathTo) (Props.toString desc));
  checkProducer producer;
  let retained = match producer with Some p -> p.adopted && not p.legacy | None -> false in
  let semantic = match update with
    | `Update _ when not retained && receiverCloneEnabled () && not (Prefs.read Props.dontChmod) ->
        let transfer = match producer with
          | None -> SemanticRemote.try_transfer
          | Some state ->
              match TargetBinding.reservation state.binding with
              | Some reservation -> SemanticRemote.try_transfer_reserved ~reservation
                  ~producer:(if state.legacy then None else Some (adoptProducer producer))
              | None -> if state.legacy then SemanticRemote.try_transfer
                  else SemanticRemote.try_transfer_with_producer ~producer:(adoptProducer producer) in
        transfer ~connection:connFrom
          ~source:(Fspath.concat fspathFrom pathFrom)
          ~basis:(Fspath.concat fspathTo realPathTo) ~directory:fspathTo ~staging:pathTo
          ~expected_size:(Uutil.Filesize.toInt64 (Props.length desc))
    | _ -> Lwt.return false in
  semantic >>= fun transferred ->
  (if transferred then begin
    Uutil.showProgress id (Props.length desc) "sde";
    Lwt.return ()
  end else
  validFilePrefix connFrom fspathFrom pathFrom fspathTo pathTo tempInfo desc
    >>= fun prefixLen ->
  checkProducer producer;
  begin match prefixLen with
    None when not retained ->
      removeOldTempFile fspathTo pathTo
  | None -> ()
  | Some len ->
      debug
        (fun() ->
           Util.msg "Keeping %s bytes previously transferred for file %s\n"
             (Uutil.Filesize.toString len) (Path.toString pathFrom))
  end;
  (* Data fork *)
  transferFileContents ?producer
    connFrom fspathFrom pathFrom fspathTo pathTo realPathTo update
    (match prefixLen with
     | None when retained -> `DATA_APPEND Uutil.Filesize.zero
     | None -> `DATA | Some l -> `DATA_APPEND l)
    (Props.length desc) id) >>= fun () ->
  transferResourceForkAndSetFileinfo ?producer
    connFrom fspathFrom pathFrom fspathTo pathTo realPathTo
    update desc fp ress id

(****)

let filesBeingTransferred = Hashtbl.create 17

let resetFileTransferState () =
  (* The waiting threads should be collected by GC *)
  Hashtbl.clear filesBeingTransferred
let () = Remote.at_conn_close resetFileTransferState

let wakeupNextTransfer fp =
  match
    try
      Some (Queue.take (Hashtbl.find filesBeingTransferred fp))
    with Queue.Empty ->
      None
  with
    None ->
      Hashtbl.remove filesBeingTransferred fp
  | Some next ->
      Lwt.wakeup next ()

let executeTransfer fp f =
  Lwt.try_bind f
    (fun res -> wakeupNextTransfer fp; Lwt.return res)
    (fun e -> wakeupNextTransfer fp; Lwt.fail e)

(* Keep track of which file contents are being transferred, and delay
   the transfer of a file with the same contents as another file being
   currently transferred.  This way, the second transfer can be
   skipped and replaced by a local copy. *)
let rec registerFileTransfer pathTo fp f =
  if not (Prefs.read Xferhint.xferbycopying) then f () else
  match
    try Some (Hashtbl.find filesBeingTransferred fp) with Not_found -> None
  with
    None ->
      let q = Queue.create () in
      Hashtbl.add filesBeingTransferred fp q;
      executeTransfer fp f
  | Some q ->
      debug (fun () -> Util.msg "delaying transfer of file %s\n"
               (Path.toString pathTo));
      let res = Lwt.wait () in
      Queue.push res q;
      res >>= fun () ->
      executeTransfer fp f

(****)

let copyprog =
  Prefs.createString "copyprog" "rsync --partial --inplace --compress"
    ~category:(`Advanced `General)
    ~deprecated:true
    "external program for copying large files"
    ("A string giving the name of an "
     ^ "external program that can be used to copy large files efficiently  "
     ^ "(plus command-line switches telling it to copy files in-place).  "
     ^ "The default setting invokes {\\tt rsync} with appropriate "
     ^ "options---most users should not need to change it.")

let copyprogrest =
  Prefs.createString
    "copyprogrest" "rsync --partial --append-verify --compress"
    ~category:(`Advanced `General)
    ~deprecated:true
    "variant of copyprog for resuming partial transfers"
    ("A variant of {\\tt copyprog} that names an external program "
     ^ "that should be used to continue the transfer of a large file "
     ^ "that has already been partially transferred.  Typically, "
     ^ "{\\tt copyprogrest} will just be {\\tt copyprog} "
     ^ "with one extra option (e.g., {\\tt --partial}, for rsync).  "
     ^ "The default setting invokes {\\tt rsync} with appropriate "
     ^ "options---most users should not need to change it.")

let copythreshold =
  Prefs.createInt "copythreshold" (-1)
    ~category:(`Advanced `General)
    ~deprecated:true
    "use copyprog on files bigger than this (if >=0, in Kb)"
    ("A number indicating above what filesize (in kilobytes) Unison should "
     ^ "use the external "
     ^ "copying utility specified by {\\tt copyprog}. Specifying 0 will cause "
     ^ "{\\em all} copies to use the external program; "
     ^ "a negative number will prevent any files from using it.  "
     ^ "The default is -1.")

(* Pref copyquoterem removed since 2.53.3 *)
let () = Prefs.markRemoved "copyquoterem"

let copymax =
  Prefs.createInt "copymax" 1
    ~category:(`Advanced `General)
    ~deprecated:true
    "maximum number of simultaneous copyprog transfers"
    ("A number indicating how many instances of the external copying utility \
      Unison is allowed to run simultaneously (default to 1).")

let formatConnectionInfo root =
  match root with
    Common.Local, _ -> ""
  | Common.Remote h, _ ->
      (* Find the (unique) nonlocal root *)
      match
         Safelist.find (function Clroot.ConnectLocal _ -> false | _ -> true)
           (Globals.parsedClRawRoots ())
      with
        Clroot.ConnectByShell (_,rawhost,uo,_,_) ->
          let rawhost = if String.contains rawhost ':' then "[" ^ rawhost ^ "]" else rawhost in
            (match uo with None -> "" | Some u -> u ^ "@")
          ^ rawhost ^ ":"
          (* Note that we don't do anything with the port -- hopefully
             this will not affect many people.  If we did want to include it,
             we'd have to fiddle with the rsync parameters in a slightly
             deeper way. *)
      | Clroot.ConnectBySocket (h',_,_) ->
          h ^ ":"
      | Clroot.ConnectLocal _ -> assert false

let shouldUseExternalCopyprog update desc =
     Prefs.read copyprog <> ""
  && Prefs.read copythreshold >= 0
  && Props.length desc >= Uutil.Filesize.ofInt64 (Int64.of_int 1)
  && Props.length desc >=
       Uutil.Filesize.ofInt64
         (Int64.mul (Int64.of_int 1000)
            (Int64.of_int (Prefs.read copythreshold)))
  && update = `Copy

let prepareExternalTransfer fspathTo pathTo =
  let info = Fileinfo.getBasic false fspathTo pathTo in
  match info.Fileinfo.typ with
    `FILE when Props.length info.Fileinfo.desc > Uutil.Filesize.zero ->
      let perms = Props.perms info.Fileinfo.desc in
      let perms' = perms lor 0o600 in
      begin try
        Fs.chmod (Fspath.concat fspathTo pathTo) perms'
      with Unix.Unix_error _ -> () end;
      true
  | `ABSENT ->
      false
  | t ->
      debug (fun() -> Util.msg "Removing existing %s / %s\n"
               (Fspath.toDebugString fspathTo) (Path.toString pathTo));
      Os.delete fspathTo pathTo;
      false

let finishExternalTransferLocal connFrom
      ((fspathFrom, pathFrom, fspathTo, pathTo, realPathTo),
       (update, desc, fp, ress, id)) =
  let info = Fileinfo.getBasic false fspathTo pathTo in
  if
    info.Fileinfo.typ <> `FILE ||
    Props.length info.Fileinfo.desc <> Props.length desc
  then
    raise (Util.Transient (Printf.sprintf
      "External copy program did not create target file (or bad length): %s"
          (Path.toString pathTo)));
  transferResourceForkAndSetFileinfo
    connFrom fspathFrom pathFrom fspathTo pathTo realPathTo
    update desc fp ress id >>= fun res ->
  Xferhint.insertEntry fspathTo pathTo fp;
  Lwt.return res

let mcopyOrUpdate = Umarshal.(sum2 unit (prod2 Uutil.Filesize.m Uutil.Filesize.m id id)
                                (function
                                 | `Copy -> I21 ()
                                 | `Update (a, b) -> I22 (a, b))
                                (function
                                 | I21 () -> `Copy
                                 | I22 (a, b) -> `Update (a, b)))

let mfinishExternalTransfer = Umarshal.(prod2
                                          (prod5 Fspath.m Path.mlocal Fspath.m Path.mlocal Path.mlocal id id)
                                          (prod5 mcopyOrUpdate Props.m Os.mfullfingerprint Osx.mressStamp Uutil.File.m id id)
                                          id id)

let finishExternalTransferOnRoot =
  Remote.registerRootCmdWithConnection
    "finishExternalTransfer"
    mfinishExternalTransfer mtransferStatus finishExternalTransferLocal

let copyprogReg = Remote.lwtRegionWithConnCleanup 1

let transferFileUsingExternalCopyprog
             rootFrom pathFrom rootTo fspathTo pathTo realPathTo
             update desc fp ress id useExistingTarget =
  Uutil.showProgress id Uutil.Filesize.zero "ext";
  let progWithArgs =
    if useExistingTarget then
      Prefs.read copyprogrest
    else
      Prefs.read copyprog
  in
  let fromSpec =
      (formatConnectionInfo rootFrom)
    ^ (Fspath.toString (Fspath.concat (snd rootFrom) pathFrom)) in
  let toSpec =
      (formatConnectionInfo rootTo)
    ^ (Fspath.toString (Fspath.concat fspathTo pathTo)) in
  Trace.log (progWithArgs ^ " " ^ fromSpec ^ " " ^ toSpec ^ "\n");
  Lwt_util.resize_region !copyprogReg (Prefs.read copymax);
  let args = Str.split (Str.regexp "[ \t]+") progWithArgs in
  let prog = match args with [] -> assert false | h :: _ -> h in
  Lwt_util.run_in_region !copyprogReg 1
    (fun () -> External.runExternalProgramArgs prog
                 (Array.of_list (args @ [fromSpec; toSpec]))) >>= fun (_, log) ->
  debug (fun() ->
           let l = Util.trimWhitespace log in
           Util.msg "transferFileUsingExternalCopyprog %s: returned...\n%s%s"
             (Path.toString pathFrom)
             l (if l="" then "" else "\n"));
  Uutil.showProgress id (Props.length desc) "ext";
  finishExternalTransferOnRoot rootTo rootFrom
    ((snd rootFrom, pathFrom, fspathTo, pathTo, realPathTo),
     (update, desc, fp, ress, id))

(****)

let transferFileLocalWithProducer ?producer connFrom
      ((fspathFrom, pathFrom, fspathTo, pathTo, realPathTo),
       (update, desc, fp, ress, id)) =
  checkProducer producer;
  (match producer with
   | Some state when not state.legacy ->
       let info = Fileinfo.getBasic false fspathTo pathTo in
       if info.Fileinfo.typ = `FILE then begin
         FinalPublication.adopt_resume (TargetBinding.native state.binding);
         state.adopted <- true;
         checkProducer producer
       end else if info.Fileinfo.typ <> `ABSENT then
         handoffProducer producer
   | _ -> ());
  let (tempInfo, isTransferred) =
    fileIsTransferred fspathTo pathTo desc fp ress in
  checkProducer producer;
  if isTransferred then begin
    (* File is already fully transferred (from some interrupted
       previous transfer).  So just make sure permissions are right. *)
    let msg =
      Printf.sprintf
        "%s/%s has already been transferred\n"
        (Fspath.toDebugString fspathTo) (Path.toString realPathTo) in
    let len = Uutil.Filesize.add (Props.length desc) (Osx.ressLength ress) in
    Uutil.showProgress id len "alr";
    propsWithExtData connFrom fspathFrom pathFrom desc >>= fun desc ->
    checkProducer producer;
    setFileinfo fspathTo pathTo realPathTo update desc;
    checkProducer producer;
    let status = match producer with
      | None | Some { legacy = true; _ } -> Lwt.return (TransferSucceeded tempInfo)
      | Some _ -> paranoidCheck ?producer fspathTo pathTo realPathTo desc fp ress in
    status >>= fun status ->
    Xferhint.insertEntry fspathTo pathTo fp;
    Lwt.return (`DONE (status, Some msg))
  end else
    registerFileTransfer pathTo fp
      (fun () ->
         checkProducer producer;
         let reuse = match producer with
           | Some state when state.adopted && not state.legacy -> Lwt.return None
           | Some { legacy = false; _ } ->
               tryCopyMovedFileBound producer connFrom fspathFrom pathFrom
                 fspathTo pathTo realPathTo update desc fp ress id
           | _ -> tryCopyMovedFile connFrom fspathFrom pathFrom
               fspathTo pathTo realPathTo update desc fp ress id
               >>= fun result -> Lwt.return (match result with
                 | None -> None | Some (info, msg) -> Some (TransferSucceeded info, msg)) in
         reuse >>= function
         | Some (status, msg) ->
             (* Transfer was performed by copying *)
             Xferhint.insertEntry fspathTo pathTo fp;
             Lwt.return (`DONE (status, Some msg))
         | None ->
             debug (fun() -> Util.msg "tryCopyMovedFile didn't work, so now we actually transfer\n");
             if shouldUseExternalCopyprog update desc then begin
               handoffProducer producer;
               Lwt.return (`EXTERNAL (prepareExternalTransfer fspathTo pathTo))
             end
             else begin
               reallyTransferFile ?producer
                 connFrom fspathFrom pathFrom fspathTo pathTo realPathTo
                 update desc fp ress id tempInfo >>= fun status ->
               Xferhint.insertEntry fspathTo pathTo fp;
               Lwt.return (`DONE (status, None))
             end)

let transferFileLocal connFrom args = transferFileLocalWithProducer connFrom args

let mtransferFile = Umarshal.(sum2 (prod2 mtransferStatus (option string) id id) bool
                                (function
                                 | `DONE (a, b) -> I21 (a, b)
                                 | `EXTERNAL a -> I22 a)
                                (function
                                 | I21 (a, b) -> `DONE (a, b)
                                 | I22 a -> `EXTERNAL a))

let transferFileOnRoot =
  Remote.registerRootCmdWithConnection "transferFile"
    mfinishExternalTransfer mtransferFile transferFileLocal

let withProducer connection root localPath workingDir candidate target token f =
  Lwt.catch
    (fun () -> TargetBinding.with_producer ?connection ~token ~logical_root:root
      ~local_path:localPath ~working_dir:workingDir ~candidate ~target
      (fun binding ->
        let producer = { binding; adopted = false; frozen = false; legacy = false } in
        checkProducer (Some producer);
        if not (FinalPublication.auxiliary_absent (TargetBinding.native binding)) ||
           Fileinfo.getType false workingDir target = `DIRECTORY then
          handoffProducer (Some producer);
        f producer))
    (function
      | Unix.Unix_error (error, phase, path) ->
          Lwt.fail (Util.Transient (Printf.sprintf
            "Receiving producer (%s, %s): %s" phase path (Unix.error_message error)))
      | error -> Lwt.fail error)

(* A distinct command carries the bounded token. The original transferFile
   schema stays unchanged for older peers and legacy materializers. *)
let transferBoundLocal connection connFrom
      (root, localPath, token, (((_, _, workingDir, candidate, target), _) as args)) =
  withProducer connection root localPath workingDir candidate target token
    (fun producer -> transferFileLocalWithProducer ~producer connFrom args)
    >>= fun (result, completion) ->
  Lwt.return (result, completion = TargetBinding.Guarded_producer)

let transferBoundOnHost = Remote.registerServerCmd "transferFileBoundV0"
  Umarshal.(prod4 Fspath.m Path.mlocal (bounded_string 64) mfinishExternalTransfer id id)
  Umarshal.(prod2 mtransferFile bool id id)
  (fun connection args -> transferBoundLocal (Some connection) connection args)

(* We limit the size of the output buffers to about 512 KB
   (we cannot go above the limit below plus 64) *)
let transferFileReg = Remote.lwtRegionWithConnCleanup 440

let bufferSize sz =
    (* Token queue *)
    min 64 ((truncate (Uutil.Filesize.toFloat sz) + 1023) / 1024)
  +
   (* Read buffer *)
   8

let transferFile
      rootFrom pathFrom rootTo fspathTo pathTo realPathTo
      update desc fp ress id =
  let f () =
    Abort.check id;
    transferFileOnRoot rootTo rootFrom
      ((snd rootFrom, pathFrom, fspathTo, pathTo, realPathTo),
       (update, desc, fp, ress, id)) >>= fun status ->
    match status with
      `DONE (status, msg) ->
         begin match msg with
           Some msg ->
             (* If the file was already present or transferred by copying
                on the server, we need to update the amount of data
                transferred so far here. *)
             if fst rootTo <> Common.Local then begin
               let len =
                 Uutil.Filesize.add (Props.length desc) (Osx.ressLength ress)
               in
               Uutil.showProgress id len "rem"
             end;
             Trace.log msg
         | None ->
             ()
         end;
         Lwt.return status
    | `EXTERNAL useExistingTarget ->
         transferFileUsingExternalCopyprog
           rootFrom pathFrom rootTo fspathTo pathTo realPathTo
           update desc fp ress id useExistingTarget
  in
  (* When streaming, we only transfer one file at a time, so we don't
     need to limit the number of concurrent transfers *)
  if Prefs.read Remote.streamingActivated then
    f ()
  else
    let bufSz = bufferSize (max (Props.length desc) (Osx.ressLength ress)) in
    Lwt_util.run_in_region !transferFileReg bufSz f

let transferFileBound ~token ~local_path
      rootFrom pathFrom rootTo fspathTo pathTo realPathTo update desc fp ress id =
  let f () =
    Abort.check id;
    let args = (snd rootTo, local_path, token,
      ((snd rootFrom, pathFrom, fspathTo, pathTo, realPathTo),
       (update, desc, fp, ress, id))) in
    let request = match fst rootTo with
      | Common.Local -> transferBoundLocal None (Remote.connectionOfRoot rootFrom) args
      | Common.Remote _ -> transferBoundOnHost (Remote.connectionOfRoot rootTo) args in
    request >>= fun (result, guarded) ->
    let completion = if guarded then TargetBinding.Guarded_producer else TargetBinding.Legacy_backend in
    match result with
    | `DONE (status, message) ->
        (match message with
         | None -> ()
         | Some message ->
             if fst rootTo <> Common.Local then
               Uutil.showProgress id (Uutil.Filesize.add (Props.length desc) (Osx.ressLength ress)) "rem";
             Trace.log message);
        Lwt.return (status, completion)
    | `EXTERNAL useExistingTarget ->
        if guarded then
          Lwt.fail (Util.Transient "External producer did not relinquish descriptor ownership")
        else transferFileUsingExternalCopyprog
          rootFrom pathFrom rootTo fspathTo pathTo realPathTo update desc fp ress id useExistingTarget
          >>= fun status -> Lwt.return (status, completion) in
  if Prefs.read Remote.streamingActivated then f () else
  let bufSz = bufferSize (max (Props.length desc) (Osx.ressLength ress)) in
  Lwt_util.run_in_region !transferFileReg bufSz f

(****)

let finishFileTransfer ~guarded rootFrom pathFrom rootTo pathTo realPathTo desc fp stamp ress status =
  match status with
    TransferSucceeded info ->
      checkForChangesToSource rootFrom pathFrom desc fp stamp ress None false
        >>= fun () -> Lwt.return info
  | TransferNeedsDoubleCheckAgainstCurrentSource (info, newfp) ->
      checkForChangesToSource rootFrom pathFrom desc fp stamp ress (Some newfp) false
        >>= fun () -> Lwt.return info
  | TransferFailed reason ->
      checkForChangesToSource rootFrom pathFrom desc fp stamp ress None true
        >>= fun () ->
      if guarded then
        Lwt.fail (Util.Transient (Printf.sprintf "Receiving producer failed for %s: %s"
          (Path.toString realPathTo) reason))
      else saveTempFileOnRoot rootTo (pathTo, realPathTo, reason) >>= fun () -> assert false

let file rootFrom pathFrom rootTo fspathTo pathTo realPathTo update desc fp stamp ress id =
  debug (fun() -> Util.msg "copyRegFile(%s,%s) -> (%s,%s,%s,%s,%s)\n"
      (Common.root2string rootFrom) (Path.toString pathFrom)
      (Common.root2string rootTo) (Path.toString realPathTo)
      (Fspath.toDebugString fspathTo) (Path.toString pathTo)
      (Props.toString desc));
  let timer = Trace.startTimer "Transmitting file" in
  begin match rootFrom, rootTo with
    (Common.Local, fspathFrom), (Common.Local, realFspathTo) ->
      localFileAsync
        fspathFrom pathFrom fspathTo pathTo realPathTo
        update desc (Osx.ressLength ress) (Some id) >>= fun () ->
        paranoidCheck fspathTo pathTo realPathTo desc fp ress
  | _ ->
      transferFile
        rootFrom pathFrom rootTo fspathTo pathTo realPathTo
        update desc fp ress id
  end >>= fun status ->
  Trace.showTimer timer;
  finishFileTransfer ~guarded:false rootFrom pathFrom rootTo pathTo realPathTo desc fp stamp ress status

let fileBound ~token ~local_path rootFrom pathFrom rootTo fspathTo pathTo realPathTo
      update desc fp stamp ress id =
  let timer = Trace.startTimer "Transmitting bound file" in
  let transfer = match rootFrom, rootTo with
    | (Common.Local, fspathFrom), (Common.Local, root) ->
        withProducer None root local_path fspathTo pathTo realPathTo token
          (fun producer ->
            localFileAsync ~producer fspathFrom pathFrom fspathTo pathTo realPathTo
              update desc (Osx.ressLength ress) (Some id) >>= fun () ->
            paranoidCheck ~producer fspathTo pathTo realPathTo desc fp ress)
    | _ -> transferFileBound ~token ~local_path rootFrom pathFrom rootTo
        fspathTo pathTo realPathTo update desc fp ress id in
  transfer >>= fun (status, completion) ->
  Trace.showTimer timer;
  finishFileTransfer ~guarded:(completion = TargetBinding.Guarded_producer)
    rootFrom pathFrom rootTo pathTo realPathTo desc fp stamp ress status
    >>= fun info -> Lwt.return (info, completion)

(****)

let recursively fspathFrom pathFrom fspathTo pathTo =
  let rec copy pFrom pTo =
    let info = Fileinfo.get true fspathFrom pFrom in
    match info.Fileinfo.typ with
    | `SYMLINK ->
        debug (fun () -> Util.msg "  Copying link %s / %s to %s / %s\n"
          (Fspath.toDebugString fspathFrom) (Path.toString pFrom)
          (Fspath.toDebugString fspathTo) (Path.toString pTo));
        Os.symlink fspathTo pTo (Os.readLink fspathFrom pFrom)
    | `FILE ->
        debug (fun () -> Util.msg "  Copying file %s / %s to %s / %s\n"
          (Fspath.toDebugString fspathFrom) (Path.toString pFrom)
          (Fspath.toDebugString fspathTo) (Path.toString pTo));
        localFile fspathFrom pFrom fspathTo pTo pTo
          `Copy info.Fileinfo.desc
          (Osx.ressLength info.Fileinfo.osX.Osx.ressInfo)  None
    | `DIRECTORY ->
        debug (fun () -> Util.msg "  Copying directory %s / %s to %s / %s\n"
          (Fspath.toDebugString fspathFrom) (Path.toString pFrom)
          (Fspath.toDebugString fspathTo) (Path.toString pTo));
        Os.createDir fspathTo pTo (Props.perms info.Fileinfo.desc);
        let ch = Os.childrenOf fspathFrom pFrom in
        Safelist.iter
          (fun n -> copy (Path.child pFrom n) (Path.child pTo n)) ch
    | `ABSENT ->
        (* BCP 4/16: Was "assert false", but this causes unison to
           crash when (1) the copyonconflict preference is used, (2) 
           there is a conflict between a deletion and a change, and
           (3) the change is propagated on top of the deletion.  Seems
           better to silently ignore the copy request. *)
        ()
    in
  debug (fun () -> Util.msg "  Copying recursively %s / %s\n"
    (Fspath.toDebugString fspathFrom) (Path.toString pathFrom));
  copy pathFrom pathTo;
  debug (fun () -> Util.msg "  Finished copying %s / %s\n"
    (Fspath.toDebugString fspathFrom) (Path.toString pathTo))
