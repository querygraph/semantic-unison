type t
type origin = No_origin | Producer_descriptor | Admitted_resume

external available : unit -> bool = "unison_final_publication_available"
external prepare_raw : string -> string -> string -> string -> bool -> t
  = "unison_final_publication_prepare"
external auxiliary_absent : t -> bool = "unison_final_publication_auxiliary_absent"
external recheck_resolution_raw : t -> string -> string -> unit
  = "unison_final_publication_resolution"
external clear_obsolete_raw : t -> string -> string -> unit
  = "unison_final_publication_clear_obsolete"
external attach : t -> unit = "unison_final_publication_attach"
external adopt_mutable_raw : t -> Unix.file_descr -> unit
  = "unison_final_publication_adopt_mutable"
external adopt_resume : t -> unit = "unison_final_publication_adopt_resume"
external producer_origin : t -> origin = "unison_final_publication_producer_origin"
external check_handoff : t -> unit = "unison_final_publication_check_handoff"
external check_producer : t -> unit = "unison_final_publication_check_producer"
external check_producer_fd_raw : t -> Unix.file_descr -> unit
  = "unison_final_publication_check_producer_fd"
external freeze_producer : t -> unit = "unison_final_publication_freeze_producer"
external producer_finalized : t -> bool = "unison_final_publication_producer_finalized"
external check_candidate : t -> unit = "unison_final_publication_check_candidate"
external observe_target : t -> unit = "unison_final_publication_observe_target"
external check : t -> unit = "unison_final_publication_check"
external publish : t -> unit = "unison_final_publication_publish"
external check_published : t -> unit = "unison_final_publication_check_published"
external published : t -> bool = "unison_final_publication_published"
external release : t -> unit = "unison_final_publication_release"
external abort_and_close : t -> unit = "unison_final_publication_abort"
external quarantine_and_close_raw : t -> string -> unit
  = "unison_final_publication_quarantine"
external errno_unavailable : Unix.error -> bool
  = "unison_final_publication_errno_unavailable"

let preparation_unavailable = function
  | Unix.Unix_error (error,
      ("final_publication.prepare.root_identity" |
       "final_publication.prepare.working_identity" |
       "final_publication.prepare.candidate_identity" |
       "final_publication.prepare.target_identity"), _) ->
      errno_unavailable error
  | _ -> false

let valid_absolute path =
  path <> "" && path.[0] = '/' && not (String.contains path '\000')

let valid_relative path =
  path <> "" && path.[0] <> '/' && not (String.contains path '\000') &&
  List.for_all (fun part -> part <> "" && part <> "." && part <> "..")
    (String.split_on_char '/' path)

let prepare ~logical_root ~working_dir ~candidate ~target ~check_apple_double =
  if not (valid_absolute logical_root) || not (valid_absolute working_dir) then
    invalid_arg "FinalPublication.prepare: invalid absolute directory";
  if not (valid_relative candidate) || not (valid_relative target) || candidate = target then
    invalid_arg "FinalPublication.prepare: invalid or identical relative names";
  prepare_raw logical_root working_dir candidate target check_apple_double

let recheck_resolution t ~working_dir ~target =
  if not (valid_absolute working_dir) || not (valid_relative target) then
    invalid_arg "FinalPublication.recheck_resolution: invalid path";
  recheck_resolution_raw t working_dir target

let clear_obsolete t ~working_dir ~path =
  if not (valid_absolute working_dir) || not (valid_relative path) then
    invalid_arg "FinalPublication.clear_obsolete: invalid path";
  clear_obsolete_raw t working_dir path

let close_noerr t = try abort_and_close t with _ -> ()

let adopt_mutable t ~candidate = adopt_mutable_raw t candidate
let check_producer_fd t ~candidate = check_producer_fd_raw t candidate

let quarantine_and_close t ~name =
  if not (valid_relative name) || String.contains name '/' then
    invalid_arg "FinalPublication.quarantine_and_close: invalid basename";
  quarantine_and_close_raw t name
