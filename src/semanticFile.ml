exception Invalid of string
external prepare_reader_raw : Unix.file_descr -> bool (* ox-portable-ffi *)
  = "unison_semantic_prepare_reader"
external pread_raw : Unix.file_descr -> int -> int64 -> string (* ox-portable-ffi *)
  = "unison_semantic_pread"
type writer = { output : Unix.file_descr; positional : bool }
external prepare_writer_raw : Unix.file_descr -> bool (* ox-portable-ffi *) = "unison_semantic_prepare_writer"
external pwrite_raw : Unix.file_descr -> string -> int -> int -> int64 -> int (* ox-portable-ffi *)
  = "unison_semantic_pwrite"
let prepare_writer ?(check_cancel = fun () -> ()) output =
  let rec prepare () =
    check_cancel ();
    try prepare_writer_raw output
    with Unix.Unix_error (Unix.EINTR,_,_) -> prepare () in
  let positional = prepare () in
  if not positional then begin
    let stat = Unix.LargeFile.fstat output in
    if stat.Unix.LargeFile.st_kind <> Unix.S_REG || stat.Unix.LargeFile.st_size < 0L then
      raise (Invalid "not a regular staging file");
    if stat.Unix.LargeFile.st_nlink <> 1 then
      raise (Invalid "staging file has multiple links")
  end;
  {output;positional}
let write_at writer data start length position =
  if writer.positional then pwrite_raw writer.output data start length position
  else begin
    if start < 0 || length < 0 || length > 65536 ||
       start > String.length data || length > String.length data - start then
      invalid_arg "SemanticFile.write_at slice";
    if position < 0L || position > Int64.sub Int64.max_int (Int64.of_int length) then
      invalid_arg "SemanticFile.write_at offset";
    ignore (Unix.LargeFile.lseek writer.output position Unix.SEEK_SET);
    Unix.write_substring writer.output data start length
  end
type stage = Hash | Parse | Verify | Write
type stage_sample = { stage : stage; calls : int; inclusive_seconds : float }
type read_stats = { logical_bytes : int64; chunks : int64; saturated : bool;
                    stages : stage_sample list option }
type stage_counter = { durations : float array; calls : int array; mutable valid : bool }
external monotonic_now : unit -> float (* ox-portable-ffi *)
  = "unison_semantic_monotonic_now"
type read_counter = { mutable bytes : int64; mutable chunks_read : int64;
                      mutable overflow : bool }
type input = Buffered of in_channel | Positional of Unix.file_descr
type t = { input : input; mutable active : bool; initial : Unix.LargeFile.stats;
           check_cancel : unit -> unit; reads : read_counter option; stages : stage_counter option }
let account_read t length = match t.reads with
  | None -> ()
  | Some counter when length > 0 ->
      let bytes = Int64.of_int length in
      if counter.bytes > Int64.sub Int64.max_int bytes then begin
        counter.bytes <- Int64.max_int; counter.overflow <- true
      end else counter.bytes <- Int64.add counter.bytes bytes;
      if counter.chunks_read = Int64.max_int then counter.overflow <- true
      else counter.chunks_read <- Int64.succ counter.chunks_read
  | Some _ -> ()
let require_active t = if not t.active then raise (Invalid "reader callback expired")
let stage_index = function Hash -> 0 | Parse -> 1 | Verify -> 2 | Write -> 3
let measure t stage f =
  require_active t;
  match t.stages with
  | None -> f ()
  | Some counter ->
      let started = monotonic_now () in
      let result = f () in
      let stopped = monotonic_now () in
      let index = stage_index stage in
      let elapsed = stopped -. started in
      let total = counter.durations.(index) +. elapsed in
      if not (Float.is_finite started && Float.is_finite stopped &&
              elapsed >= 0. && Float.is_finite total) || counter.calls.(index) = max_int
      then counter.valid <- false
      else begin
        counter.durations.(index) <- total;
        counter.calls.(index) <- counter.calls.(index) + 1
      end;
      result
let stage_samples = function
  | None -> None
  | Some counter when not counter.valid -> None
  | Some counter -> Some (List.filter_map (fun stage ->
      let index = stage_index stage in
      if counter.calls.(index) = 0 then None else
      Some {stage;calls=counter.calls.(index);inclusive_seconds=counter.durations.(index)})
      [Hash;Parse;Verify;Write])
let descriptor t = require_active t; match t.input with
  | Buffered channel -> Unix.descr_of_in_channel channel | Positional fd -> fd
let size t = require_active t; t.initial.Unix.LargeFile.st_size
let same_inode t fd =
  require_active t;
  let b = Unix.LargeFile.fstat fd in
  t.initial.Unix.LargeFile.st_dev = b.Unix.LargeFile.st_dev &&
  t.initial.Unix.LargeFile.st_ino = b.Unix.LargeFile.st_ino
let check t =
  require_active t; t.check_cancel ();
  let a = t.initial and b = Unix.LargeFile.fstat (descriptor t) in
  if a.Unix.LargeFile.st_dev <> b.Unix.LargeFile.st_dev || a.Unix.LargeFile.st_ino <> b.Unix.LargeFile.st_ino ||
     a.Unix.LargeFile.st_size <> b.Unix.LargeFile.st_size || a.Unix.LargeFile.st_mtime <> b.Unix.LargeFile.st_mtime ||
     a.Unix.LargeFile.st_ctime <> b.Unix.LargeFile.st_ctime then
    raise (Invalid "file changed while inspecting")
let with_fd_internal ~measure_reads ~measure_stages ~check_cancel fd f =
  check_cancel ();
  let initial = Unix.LargeFile.fstat fd in
  if initial.Unix.LargeFile.st_kind <> Unix.S_REG || initial.Unix.LargeFile.st_size < 0L then
    raise (Invalid "not a regular file");
  (* Prepare ownership bookkeeping before acquiring the duplicate. A channel
     or record allocation failure must not leave its descriptor untracked. *)
  let descriptor = ref fd and owns_descriptor = ref false
  and owned_channel = ref None in
  let close () = match !owned_channel with
    | Some channel ->
        owned_channel := None;
        close_in channel
    | None when !owns_descriptor ->
        owns_descriptor := false;
        Unix.close !descriptor
    | None -> () in
  let close_noerr () = try close () with _ -> () in
  descriptor := Unix.dup ~cloexec:true fd;
  owns_descriptor := true;
  try
    let channel = Unix.in_channel_of_descr !descriptor in
    owns_descriptor := false;
    (* Installing [Some channel] can itself allocate. Until that succeeds,
       close the new channel locally rather than retrying its raw FD. *)
    (try owned_channel := Some channel
     with error -> (try close_in_noerr channel with _ -> ()); raise error);
    let reads = if measure_reads then Some {bytes=0L;chunks_read=0L;overflow=false} else None in
    let stages = if measure_stages then
      Some {durations=Array.make 4 0.;calls=Array.make 4 0;valid=true} else None in
    let t = {input=Buffered channel;active=true;initial;check_cancel;reads;stages} in
    Fun.protect ~finally:(fun () -> t.active <- false) (fun () ->
      let result = f t in
      check t;
      close ();
      result)
  with error -> close_noerr (); raise error
let with_fd ?(check_cancel = fun () -> ()) fd f =
  with_fd_internal ~measure_reads:false ~measure_stages:false ~check_cancel fd f
let with_read_stats ?(measure_stages=false) ?(check_cancel = fun () -> ()) fd f =
  with_fd_internal ~measure_reads:true ~measure_stages ~check_cancel fd (fun file ->
    let result = f file in
    let stats = match file.reads with
      | Some counter -> {logical_bytes=counter.bytes;chunks=counter.chunks_read;saturated=counter.overflow;stages=stage_samples file.stages}
      | None -> assert false in
    result,stats)
let with_borrowed_fd ?(check_cancel = fun () -> ()) fd f =
  let rec prepare () =
    check_cancel ();
    try if not(prepare_reader_raw fd) then raise(Invalid "borrowed positional reader unavailable")
    with Unix.Unix_error(Unix.EINTR,_,_) -> prepare () in
  prepare ();
  let initial=Unix.LargeFile.fstat fd in
  if initial.Unix.LargeFile.st_kind<>Unix.S_REG || initial.Unix.LargeFile.st_size<0L then
    raise(Invalid "not a regular borrowed file");
  let t={input=Positional fd;active=true;initial;check_cancel;reads=None;stages=None} in
  Fun.protect ~finally:(fun () -> t.active <- false) (fun () ->
    let result=f t in check t;result)
let positional_read t fd offset length =
  let output=Bytes.create length in
  let rec loop position = if position<length then begin
    t.check_cancel ();
    let remaining=min 65536 (length-position) in
    let rec attempt () =
      t.check_cancel ();
      try pread_raw fd remaining (Int64.add offset (Int64.of_int position))
      with Unix.Unix_error(Unix.EINTR,_,_) -> attempt () in
    let chunk=attempt () in
    if chunk="" then raise(Invalid "truncated borrowed file");
    Bytes.blit_string chunk 0 output position (String.length chunk);
    loop (position+String.length chunk)
  end in loop 0;Bytes.unsafe_to_string output
let bounds t offset length =
  if offset < 0L || length < 0L || offset > size t || length > Int64.sub (size t) offset then
    raise (Invalid "extent outside file")
let read t offset length =
  require_active t; t.check_cancel ();
  if length < 0 || length > 1048576 then raise (Invalid "read limit");
  bounds t offset (Int64.of_int length);
  try
    let result = match t.input with
      | Buffered channel -> LargeFile.seek_in channel offset; really_input_string channel length
      | Positional fd -> positional_read t fd offset length in
    account_read t length;
    result
  with End_of_file -> raise (Invalid "truncated file")
let iter t offset length f =
  require_active t; t.check_cancel ();
  bounds t offset length;
  (match t.input with Buffered channel -> LargeFile.seek_in channel offset | Positional _ -> ());
  let b = Bytes.create 65536 in
  let rec loop remaining = if remaining > 0L then begin
    t.check_cancel ();
    let n = Int64.to_int (min remaining 65536L) in
    (try match t.input with
      | Buffered channel -> really_input channel b 0 n
      | Positional fd ->
        let position=Int64.add offset (Int64.sub length remaining) in
        Bytes.blit_string (positional_read t fd position n) 0 b 0 n
     with End_of_file -> raise (Invalid "truncated file"));
    account_read t n;
    f b n; loop (Int64.sub remaining (Int64.of_int n))
  end in loop length
let digest t = measure t Hash (fun () ->
  let h = SemanticHash.create () in
  iter t 0L (size t) (fun b n -> SemanticHash.feed h b 0 n);
  check t; SemanticHash.finish h)
