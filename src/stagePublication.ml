type t

external available : unit -> bool = "unison_stage_publication_available"
external prepare_raw : string -> string -> string -> t = "unison_stage_publication_prepare"
external adopt_raw : t -> Unix.file_descr -> Unix.file_descr -> unit = "unison_stage_publication_adopt"
external publish : t -> unit = "unison_stage_publication_publish"
external disarm : t -> unit = "unison_stage_publication_disarm"
external abort_and_close : t -> unit = "unison_stage_publication_abort"
external errno_unavailable : Unix.error -> bool = "unison_stage_publication_errno_unavailable"

let preparation_unavailable = function
  | Unix.Unix_error (error,
      ("stage_publication.prepare.working_identity" |
       "stage_publication.prepare.stage_identity" |
       "stage_publication.prepare.temporary_identity"), _) ->
      errno_unavailable error
  | _ -> false

let valid_relative path =
  path <> "" && path.[0] <> '/' && not (String.contains path '\000') &&
  List.for_all (fun component ->
    component <> "" && component <> "." && component <> "..")
    (String.split_on_char '/' path)

let prepare ~working_dir ~stage ~temporary =
  if working_dir = "" || working_dir.[0] <> '/' || String.contains working_dir '\000' then
    invalid_arg "StagePublication.prepare: invalid absolute working directory";
  if not (valid_relative stage) || not (valid_relative temporary) || stage = temporary then
    invalid_arg "StagePublication.prepare: invalid or identical relative names";
  prepare_raw working_dir stage temporary

let adopt t ~parent ~stage = adopt_raw t parent stage
let close_noerr t = try abort_and_close t with _ -> ()

(* Versioned explicit owner API. Legacy callers retain their existing semantics
   until their outer transaction and error cleanup are migrated together. *)
type owned = t
exception Ownership_uncertain of owned option
let () = Callback.register_exception "unison.stage-publication.ownership-uncertain"
  (Ownership_uncertain None)
external prepare_owned_raw : string -> string -> string -> owned = "unison_stage_publication_prepare_owned"
external owned_evidence : owned -> string * (int * string) *
  (int * int * string * int64 option * int64 option) array * int array =
  "unison_stage_publication_owned_evidence"
let prepare_owned ~working_dir ~stage ~temporary =
  if working_dir = "" || working_dir.[0] <> '/' || String.contains working_dir '\000' then
    invalid_arg "StagePublication.prepare_owned: invalid absolute working directory";
  if not (valid_relative stage) || not (valid_relative temporary) || stage = temporary then
    invalid_arg "StagePublication.prepare_owned: invalid or identical relative names";
  prepare_owned_raw working_dir stage temporary
type parent_handoff = { acknowledged:bool ref; mutable attempted:bool }
let prepare_parent_handoff () = {acknowledged=ref false;attempted=false}
let parent_consumed handoff = !(handoff.acknowledged)
external adopt_tracked_raw : owned -> Unix.file_descr -> Unix.file_descr -> bool ref -> unit
  = "unison_stage_publication_adopt_tracked_v1"
let adopt_owned_tracked owner handoff ~parent ~stage =
  if handoff.attempted then invalid_arg "StagePublication parent handoff already attempted";
  handoff.attempted<-true;
  adopt_tracked_raw owner parent stage handoff.acknowledged
let adopt_owned owner ~parent ~stage = adopt_raw owner parent stage
let publish_owned = publish
let disarm_owned = disarm
let abort_owned = abort_and_close
