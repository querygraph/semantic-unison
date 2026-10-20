(** Isolated full-file snapshot kernel, not scan selection or helper execution.
    The caller owns admission, cancellation, namespace and descriptor lifetime.
    Worker dispatch is available; callers select scan paths and scope. *)
type report = {
  bytes : int64;
  sha256 : string;
  native_clone : bool;
  logical_bytes_written : int64;
  source_stats : Unix.LargeFile.stats;
}
val existing_clone : expected_length:int64 -> Unix.file_descr -> Unix.file_descr ->
  WholeFileClone.result
(** The existing strict whole-file FD clone primitive and decoder. No named
    output creation or second filesystem clone engine. Platform/filesystem
    declines retain their original scope. *)
val materialize :
  check_cancel:(unit -> unit) -> max_bytes:int64 ->
  clone:(expected_length:int64 -> Unix.file_descr -> Unix.file_descr -> WholeFileClone.result) ->
  source:Unix.file_descr -> output:Unix.file_descr -> report
(** Borrow a readable source and an exclusively created, private, empty,
    single-link, read/write regular output on a distinct inode. Empty/single-link
    observations do not establish exclusive ownership: caller must provide it.
    Reuse [Fs.clone_file_status] as [clone] at integration, never a second native
    clone implementation. Only a checked no-effect decline permits bounded
    ordinary copying; native failure or inconsistent effects never do.

    Verify the complete output SHA-256 against the source stream and fence
    source metadata before/after. Cooperative [SemanticFile] stability checks
    use OCaml stat timestamps; caller retains name bindings and any stronger
    platform epoch fences. No hostile same-UID/ABA or physical-storage claim.
    Calls may move shared descriptor positions. No path creation, unlink, chmod,
    source writes, fsync, descriptor retirement or publication is performed.
    On any failure discard the private output after all owners settle. *)
