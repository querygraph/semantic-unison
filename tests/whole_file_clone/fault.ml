(* Private fixture state. Production has no fault or observability API. *)
exception Primary
exception Cleanup
let primary = Primary
let cleanup = Cleanup
let () = Callback.register_exception "unison-whole-fixture-primary" primary
let phase = ref "normal"
let hits = ref 0
let source : Unix.file_descr option ref = ref None
let parent : Unix.file_descr option ref = ref None
let output : Unix.file_descr option ref = ref None
let before = ref (fun () -> ())
let configure label action =
  phase := label; hits := 0; source := None; parent := None; output := None;
  before := action
let checkpoint label =
  if label = !phase then begin incr hits; !before (); raise primary end
let checkpoint_no_raise label =
  if label = !phase then begin incr hits; !before () end
external queue_signal : unit -> unit = "whole_fixture_queue_signal"
external pending_dispatch : unit -> unit = "whole_fixture_pending_dispatch"
external fd_is_open : Unix.file_descr -> bool = "whole_fixture_fd_is_open"
let before_close () =
  if !phase="pending-source-close" && !hits=0 then incr hits
external probe_close_slot : Unix.file_descr ref -> bool ref -> unit =
  "whole_fixture_probe_close_slot"
external legacy_probe_close_slot : Unix.file_descr ref -> bool ref -> unit =
  "whole_fixture_legacy_probe_close_slot"
external native_mode : int -> unit = "whole_fixture_native_mode"
external fd_count : unit -> int = "resource_fixture_fd_count"
external prefetch : in_channel -> int = "caml_ml_input_scan_line"
external exact_copy : Unix.file_descr -> Unix.file_descr -> int64 -> unit =
  "whole_fixture_exact_copy"
external write_at : Unix.file_descr -> int64 -> string -> unit =
  "whole_fixture_write_at"
external set_xattr : string -> string -> string -> unit = "whole_fixture_set_xattr"
external get_xattr : string -> string -> string = "whole_fixture_get_xattr"
external nodump : Unix.file_descr -> bool -> unit = "whole_fixture_nodump"
external filesystem_type : string -> string = "whole_fixture_filesystem_type"
