"""Small endpoint seams for the production ticket registry's isolated tests.

These do not implement a registry. FinalPublication owns real close-on-exec
descriptors and exposes fault/call observations; native namespace correctness
is qualified by tests/final_publication separately.
"""

MODULES = {
    'util': r'''
exception Transient of string
''',
    'features': r'''
type t = bool ref
let negotiated = ref false
let producer_negotiated = ref false
let registered : (string * t) list ref = ref []
let register name ?(arcFormatChange=false) _ =
  ignore arcFormatChange;
  let feature = match name with
    | "target-binding-v0" -> negotiated
    | "target-binding-producer-v0" -> producer_negotiated
    | _ -> ref false in
  registered := (name, feature) :: !registered;
  feature
let enabled feature = !feature
''',
    'prefs': r'''
type 'a t = 'a ref
let read preference = !preference
''',
    'osx': r'''
let rsrc = ref false
''',
    'case': r'''
type mode = Sensitive | Insensitive | UnicodeSensitive | UnicodeInsensitive
let current = ref Sensitive
let ops () = object method mode = !current end
''',
    'name': r'''
type t = string
let calls = ref 0
let normalize name = incr calls; if name = "decomposed" then "composed" else name
''',
    'path': r'''
type 'a path = string
type t = [`Global] path
type local = [`Local] path
let empty = ""
let toString path = path
let fromString path = path
let follow = ref false
let followLink _ = !follow
let deconstructRev path =
  if path = "" then None else
  let parent = Filename.dirname path in
  Some (Filename.basename path, if parent = "." then "" else parent)
let child parent name = if parent = "" then name else Filename.concat parent name
''',
    'fspath': r'''
type t = string
let toString path = path
let compare = String.compare
let default_resolution root path =
  let absolute = Filename.concat root path in
  Filename.dirname absolute, Filename.basename absolute
let resolver = ref default_resolution
let findWorkingDir root path = !resolver root path
''',
    'fileinfo': r'''
let fault : exn option ref = ref None
let getType _ root path =
  match !fault with
  | Some error -> raise error
  | None ->
      try match (Unix.stat (if path = "" then root else Filename.concat root path)).Unix.st_kind with
      | Unix.S_REG -> `FILE
      | Unix.S_DIR -> `DIRECTORY
      | _ -> `SYMLINK
      with Unix.Unix_error (Unix.ENOENT, _, _) -> `ABSENT
''',
    'remote': r'''
type connection = int ref
let handlers : (unit -> unit) list ref = ref []
let at_conn_close ?(only_server=false) handler =
  ignore only_server; handlers := handler :: !handlers
let disconnect () = List.iter (fun handler -> handler ()) !handlers
''',
    'os': r'''
type fullfingerprint = Actual of string | Pseudo of string
let isPseudoFingerprint = function Pseudo _ -> true | Actual _ -> false
let fullfingerprintEqual left right = left = right
''',
    'finalPublication': r'''
type t = {
  fd : Unix.file_descr;
  working : string;
  target : string;
  auxiliary : bool;
  mutable closed : bool;
  mutable attached : bool;
  mutable published : bool;
  mutable aborts : int;
  mutable releases : int;
  mutable quarantines : string list;
  mutable producer : bool;
  mutable frozen : bool;
  mutable producer_fd : Unix.file_descr option;
  mutable frozen_size : int64 option;
  mutable adoptions : int;
  mutable producer_checks : int;
  mutable freezes : int;
  mutable candidate_checks : int;
}
let enabled = ref true
let calls = ref 0
let contexts : t list ref = ref []
let prepare_fault : exn option ref = ref None
let resolution_fault : exn option ref = ref None
let abort_fault : exn option ref = ref None
let handoff_fault : exn option ref = ref None
let adopt_fault : exn option ref = ref None
let producer_check_fault : exn option ref = ref None
let freeze_fault : exn option ref = ref None
let finalized_fault : exn option ref = ref None
let candidate_fault : (int * exn) option ref = ref None
let on_prepare = ref (fun () -> ())
let on_adopt = ref (fun () -> ())
let on_producer_check = ref (fun () -> ())
let on_freeze = ref (fun () -> ())
let on_candidate_check = ref (fun () -> ())
let available () = !enabled
let preparation_unavailable = function
  | Unix.Unix_error ((Unix.ENOSYS | Unix.EOPNOTSUPP),
      ("final_publication.prepare.root_identity" |
       "final_publication.prepare.working_identity" |
       "final_publication.prepare.candidate_identity" |
       "final_publication.prepare.target_identity"), _) -> true
  | _ -> false
let prepare ~logical_root ~working_dir ~candidate ~target ~check_apple_double =
  ignore logical_root; ignore candidate; incr calls;
  (match !prepare_fault with Some error -> raise error | None -> ());
  let context = {
    fd = Unix.openfile "/dev/null" [Unix.O_RDONLY; Unix.O_CLOEXEC] 0;
    working = working_dir; target; auxiliary = check_apple_double;
    closed = false; attached = false; published = false;
    aborts = 0; releases = 0; quarantines = [];
    producer = false; frozen = false; producer_fd = None; frozen_size = None;
    adoptions = 0; producer_checks = 0; freezes = 0; candidate_checks = 0 } in
  contexts := context :: !contexts;
  !on_prepare ();
  context
let require_open context = if context.closed then failwith "native owner already closed"
let recheck_resolution context ~working_dir ~target =
  require_open context;
  (match !resolution_fault with Some error -> raise error | None -> ());
  if context.working <> working_dir || context.target <> target then
    raise (Unix.Unix_error (Unix.EBUSY, "native_resolution", target))
let published context = context.published
let attach context =
  require_open context;
  if context.attached || context.producer then
    raise (Unix.Unix_error (Unix.EBUSY, "native_attach_state", ""));
  context.attached <- true
let publish context = require_open context; context.published <- true
let witness context =
  match context.producer_fd with
  | Some fd ->
      let stat = Unix.LargeFile.fstat fd in
      if stat.Unix.LargeFile.st_kind <> Unix.S_REG then
        raise (Unix.Unix_error (Unix.EINVAL, "producer_witness", ""));
      fd
  | None -> raise (Unix.Unix_error (Unix.EBUSY, "producer_witness", ""))
let adopt_mutable context ~candidate =
  require_open context;
  (match !adopt_fault with Some error -> raise error | None -> ());
  if context.attached || context.producer then
    raise (Unix.Unix_error (Unix.EBUSY, "producer_adopt_state", ""));
  let stat = Unix.LargeFile.fstat candidate in
  if stat.Unix.LargeFile.st_kind <> Unix.S_REG || stat.Unix.LargeFile.st_nlink <> 1 then
    raise (Unix.Unix_error (Unix.EINVAL, "producer_adopt_kind", ""));
  let fd = Unix.dup ~cloexec:true candidate in
  context.producer_fd <- Some fd;
  context.producer <- true;
  context.adoptions <- context.adoptions + 1;
  !on_adopt ()
let check_producer context =
  require_open context;
  (match !producer_check_fault with Some error -> raise error | None -> ());
  if not context.producer || context.frozen then
    raise (Unix.Unix_error (Unix.EBUSY, "producer_check_state", ""));
  ignore (witness context);
  context.producer_checks <- context.producer_checks + 1;
  !on_producer_check ()
let freeze_producer context =
  check_producer context;
  (match !freeze_fault with Some error -> raise error | None -> ());
  let fd = witness context in
  context.frozen_size <- Some (Unix.LargeFile.fstat fd).Unix.LargeFile.st_size;
  context.frozen <- true;
  context.attached <- true;
  context.freezes <- context.freezes + 1;
  !on_freeze ()
let producer_finalized context =
  (match !finalized_fault with Some error -> raise error | None -> ());
  context.producer && context.frozen
let check_candidate context =
  require_open context;
  context.candidate_checks <- context.candidate_checks + 1;
  (match !candidate_fault with
   | Some (ordinal, error) when ordinal = context.candidate_checks -> raise error
   | _ -> ());
  if not context.frozen then
    raise (Unix.Unix_error (Unix.EBUSY, "producer_candidate_unfrozen", ""));
  let fd = witness context in
  if Some (Unix.LargeFile.fstat fd).Unix.LargeFile.st_size <> context.frozen_size then
    raise (Unix.Unix_error (Unix.EBUSY, "producer_candidate_changed", ""));
  !on_candidate_check ()
let check_handoff context =
  require_open context;
  (match !handoff_fault with Some error -> raise error | None -> ());
  if context.producer then
    if context.frozen then check_candidate context else check_producer context
let drop_witness context =
  match context.producer_fd with
  | None -> ()
  | Some fd -> context.producer_fd <- None; Unix.close fd
let close context =
  if not context.closed then begin
    context.closed <- true;
    drop_witness context;
    Unix.close context.fd
  end
let release context = context.releases <- context.releases + 1; close context
let abort_and_close context =
  context.aborts <- context.aborts + 1; close context;
  match !abort_fault with Some error -> raise error | None -> ()
let close_noerr context = try abort_and_close context with _ -> ()
let quarantine_and_close context ~name =
  require_open context;
  context.quarantines <- name :: context.quarantines;
  close context
let alive context =
  try ignore (Unix.fstat context.fd); not context.closed
  with Unix.Unix_error (Unix.EBADF, _, _) -> false
let open_count () = List.fold_left (fun count context ->
  count + if context.closed then 0 else 1) 0 !contexts
''',
}
