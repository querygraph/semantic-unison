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
