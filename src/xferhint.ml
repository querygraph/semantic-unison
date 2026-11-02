(* Unison file synchronizer: src/xferhint.ml *)
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


let debug = Trace.debug "xferhint"

let xferbycopying =
  Prefs.createBool "xferbycopying" true
    ~category:(`Advanced `Remote)
    "optimize transfers using local copies"
    ("When this preference is set, Unison will try to avoid transferring "
   ^ "file contents across the network by recognizing when a file with the "
   ^ "required contents already exists in the target replica.  This usually "
   ^ "allows file moves to be propagated very quickly.  The default value is "
   ^ "\\texttt{true}.  ")

module FPMap =
  Hashtbl.Make
    (struct
       type t = Os.fullfingerprint
       let hash = Os.fullfingerprintHash
       let equal = Os.fullfingerprintEqual
     end)

type handle = Os.fullfingerprint

(* map(fingerprint, path) *)
let fingerprint2pathMap = FPMap.create 10000

let deleteEntry fp =
  debug (fun () ->
    Util.msg "deleteEntry: fp=%s\n" (Os.fullfingerprint_to_string fp));
  FPMap.remove fingerprint2pathMap fp

let lookup fp =
  assert (Prefs.read xferbycopying);
  debug (fun () ->
    Util.msg "lookup: fp = %s\n" (Os.fullfingerprint_to_string fp));
  try
    let (fspath, path) = FPMap.find fingerprint2pathMap fp in
    Some (fspath, path, fp)
  with Not_found ->
    None

(* Clone preservation keeps a few receiver paths per fingerprint, independent
   of xferbycopying (which local syncs turn off). Entries are hints only: the
   source confirms clone identity and the receiver rechecks the fingerprint. *)
let clonePairsFeature =
  Features.register "clone-pairs-v0" ~arcFormatChange:false None

(* Sent only to a peer that offers clone-pairs-v0, so an older peer never
   sees the preference and behaves as before. *)
let clones =
  Prefs.createBool "clones" false
    ~send:(fun () -> Features.enabled clonePairsFeature)
    ~category:(`Advanced `General)
    "recreate APFS clones as clones on the target"
    ("When this preference is set and both hosts support it, a new file that \
      is an exact APFS clone of another file on the source is recreated on \
      the target as a clone of the corresponding file there, after checking \
      its contents, instead of being transferred.  Identical files that are \
      not clones stay independent.  The default value is \\texttt{false}.")

let clonesEnabled () = Prefs.read clones && Features.enabled clonePairsFeature

let cloneHintLimit = 16
let cloneHints = FPMap.create 1000

let cloneCandidates fp =
  if not (Prefs.read clones) then [] else
  try FPMap.find cloneHints fp with Not_found -> []

let insertCloneHint fspath path fp =
  if Prefs.read clones && not (Os.isPseudoFingerprint fp) then begin
    let known = try FPMap.find cloneHints fp with Not_found -> [] in
    let same (fspath', path') =
      Fspath.toString fspath' = Fspath.toString fspath && Path.toString path' = Path.toString path in
    if not (List.exists same known) then
      FPMap.replace cloneHints fp
        ((fspath, path) :: List.filteri (fun i _ -> i < cloneHintLimit - 1) known)
  end

let insertEntry fspath path fp =
  insertCloneHint fspath path fp;
  if Prefs.read xferbycopying && not (Os.isPseudoFingerprint fp) then begin
    debug (fun () ->
      Util.msg "insertEntry: fspath=%s, path=%s, fp=%s\n"
        (Fspath.toDebugString fspath)
        (Path.toString path) (Os.fullfingerprint_to_string fp));
    FPMap.replace fingerprint2pathMap fp (fspath, path)
  end
