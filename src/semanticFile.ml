exception Invalid of string
type writer = { output : Unix.file_descr; positional : bool }
external prepare_writer_raw : Unix.file_descr -> bool = "unison_semantic_prepare_writer"
external pwrite_raw : Unix.file_descr -> string -> int -> int -> int64 -> int
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
type t = { channel : in_channel; initial : Unix.LargeFile.stats;
           check_cancel : unit -> unit }
let size t = t.initial.Unix.LargeFile.st_size
let same_inode t fd =
  let b = Unix.LargeFile.fstat fd in
  t.initial.Unix.LargeFile.st_dev = b.Unix.LargeFile.st_dev &&
  t.initial.Unix.LargeFile.st_ino = b.Unix.LargeFile.st_ino
let check t =
  t.check_cancel ();
  let a = t.initial and b = Unix.LargeFile.fstat (Unix.descr_of_in_channel t.channel) in
  if a.Unix.LargeFile.st_dev <> b.Unix.LargeFile.st_dev || a.Unix.LargeFile.st_ino <> b.Unix.LargeFile.st_ino ||
     a.Unix.LargeFile.st_size <> b.Unix.LargeFile.st_size || a.Unix.LargeFile.st_mtime <> b.Unix.LargeFile.st_mtime ||
     a.Unix.LargeFile.st_ctime <> b.Unix.LargeFile.st_ctime then
    raise (Invalid "file changed while inspecting")
let with_fd ?(check_cancel = fun () -> ()) fd f =
  check_cancel ();
  let initial = Unix.LargeFile.fstat fd in
  if initial.Unix.LargeFile.st_kind <> Unix.S_REG || initial.Unix.LargeFile.st_size < 0L then
    raise (Invalid "not a regular file");
  let channel = Unix.in_channel_of_descr (Unix.dup ~cloexec:true fd) in
  let t = {channel;initial;check_cancel} in
  match f t with
  | result -> (try check t; close_in channel; result with e -> close_in_noerr channel; raise e)
  | exception e -> close_in_noerr channel; raise e
let bounds t offset length =
  if offset < 0L || length < 0L || offset > size t || length > Int64.sub (size t) offset then
    raise (Invalid "extent outside file")
let read t offset length =
  t.check_cancel ();
  if length < 0 || length > 1048576 then raise (Invalid "read limit");
  bounds t offset (Int64.of_int length);
  LargeFile.seek_in t.channel offset;
  try really_input_string t.channel length with End_of_file -> raise (Invalid "truncated file")
let iter t offset length f =
  t.check_cancel ();
  bounds t offset length;
  LargeFile.seek_in t.channel offset;
  let b = Bytes.create 65536 in
  let rec loop remaining = if remaining > 0L then begin
    t.check_cancel ();
    let n = Int64.to_int (min remaining 65536L) in
    (try really_input t.channel b 0 n with End_of_file -> raise (Invalid "truncated file"));
    f b n; loop (Int64.sub remaining (Int64.of_int n))
  end in loop length
let digest t =
  let h = SemanticHash.create () in
  iter t 0L (size t) (fun b n -> SemanticHash.feed h b 0 n);
  check t; SemanticHash.finish h
