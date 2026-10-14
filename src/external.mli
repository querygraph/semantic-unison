(* Unison file synchronizer: src/external.mli *)
(* Copyright 1999-2020, Benjamin C. Pierce (see COPYING for details) *)

val runExternalProgram : string -> (Unix.process_status * string) Lwt.t
val runExternalProgramArgs : string -> string array -> (Unix.process_status * string) Lwt.t
val readChannelTillEof : in_channel -> string
val resolve_program : string -> string
(** Existing startup PATH lookup, returned as an absolute path for supervised
    invocation. Preserves followed executable aliases. Raises [Not_found] for
    an unresolved PATH name. This does not pin executable contents or attest
    its internal thread count. *)
