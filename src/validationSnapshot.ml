type report = {
  bytes : int64; sha256 : string; native_clone : bool;
  logical_bytes_written : int64; source_stats : Unix.LargeFile.stats;
}
let invalid reason = raise (SemanticFile.Invalid reason)
let stable a b =
  {a with Unix.LargeFile.st_atime=0.} = {b with Unix.LargeFile.st_atime=0.}
let materialize ~check_cancel ~max_bytes ~clone ~source ~output =
  if max_bytes < 0L then invalid_arg "ValidationSnapshot.max_bytes";
  check_cancel ();
  let before=Unix.LargeFile.fstat source and target=Unix.LargeFile.fstat output in
  let size=before.Unix.LargeFile.st_size in
  if before.Unix.LargeFile.st_kind<>Unix.S_REG || size<0L || size>max_bytes then
    invalid "snapshot source kind/size exceeds admitted scope";
  if before.Unix.LargeFile.st_dev=target.Unix.LargeFile.st_dev &&
     before.Unix.LargeFile.st_ino=target.Unix.LargeFile.st_ino then
    invalid "snapshot must not share the source inode";
  if target.Unix.LargeFile.st_kind<>Unix.S_REG || target.Unix.LargeFile.st_size<>0L ||
     target.Unix.LargeFile.st_nlink<>1 then invalid "snapshot output must be private and empty";
  let writer=SemanticFile.prepare_writer ~check_cancel output in
  let source_position=Unix.LargeFile.lseek source 0L Unix.SEEK_CUR
  and target_position=Unix.LargeFile.lseek output 0L Unix.SEEK_CUR in
  if target_position<>0L then invalid "snapshot output cursor must start at zero";
  check_cancel ();
  let result=WholeFileClone.validate_result ~expected_length:size
    (clone ~expected_length:size source output) in
  if Unix.LargeFile.lseek source 0L Unix.SEEK_CUR<>source_position ||
     Unix.LargeFile.lseek output 0L Unix.SEEK_CUR<>target_position then
    invalid "snapshot native adapter changed a descriptor cursor";
  if not (stable before (Unix.LargeFile.fstat source)) then
    invalid "snapshot source changed during native operation";
  let native_clone=match result with
    | WholeFileClone.Native_shared _ -> true
    | WholeFileClone.No_work _ -> false
    | WholeFileClone.Declined _ -> false
    | WholeFileClone.Failed receipt -> WholeFileClone.raise_failed receipt in
  let copy=match result with WholeFileClone.Declined _ -> true | _ -> false in
  let after_native=Unix.LargeFile.fstat output in
  if after_native.Unix.LargeFile.st_dev<>target.Unix.LargeFile.st_dev ||
     after_native.Unix.LargeFile.st_ino<>target.Unix.LargeFile.st_ino ||
     after_native.Unix.LargeFile.st_nlink<>1 ||
     after_native.Unix.LargeFile.st_size<>(if copy then 0L else size) then
    invalid "snapshot adapter output identity/length differs";
  let written=ref 0L in
  let digest=SemanticFile.with_fd ~check_cancel source (fun input ->
    if copy then begin
      let hash=SemanticHash.create () in
      SemanticFile.iter input 0L size (fun data count ->
        check_cancel ();
        let text=Bytes.unsafe_to_string data in
        let rec write offset =
          if offset<count then begin
            check_cancel ();
            let rec attempt () =
              check_cancel ();
              try SemanticFile.write_at writer text offset (count-offset)
                (Int64.add !written (Int64.of_int offset))
              with Unix.Unix_error (Unix.EINTR,_,_) -> attempt () in
            let amount=attempt () in
            if amount=0 then invalid "snapshot write made no progress";
            write (offset+amount)
          end in
        write 0;SemanticHash.feed hash data 0 count;
        written:=Int64.add !written (Int64.of_int count));
      SemanticHash.finish hash
    end else SemanticFile.digest input) in
  check_cancel ();
  let copied=Unix.LargeFile.fstat output in
  if copied.Unix.LargeFile.st_size<>size || copied.Unix.LargeFile.st_nlink<>1 ||
     copied.Unix.LargeFile.st_dev<>target.Unix.LargeFile.st_dev ||
     copied.Unix.LargeFile.st_ino<>target.Unix.LargeFile.st_ino then
    invalid "snapshot materialized identity/length differs";
  let output_digest=SemanticFile.with_fd ~check_cancel output SemanticFile.digest in
  if digest<>output_digest then invalid "snapshot complete digest differs";
  check_cancel ();
  if not (stable before (Unix.LargeFile.fstat source)) then
    invalid "snapshot source changed during materialization";
  {bytes=size;sha256=SemanticHash.hex digest;native_clone;
   logical_bytes_written= !written;source_stats=before}
