(* Unison file synchronizer: src/transfer.mli *)
(* Copyright 1999-2020, Benjamin C. Pierce (see COPYING for details) *)

(*
   Rsync : general algorithm description

     The rsync algorithm is a technique for reducing the cost of a file
   transfer by avoiding the transfer of blocks that are already at the
   destination.
     Imagine we have source and destination computers that have files X and
   Y respectively, where X and Y are similar. The algorithm proceeds as
   follows :
   - The destination computer divides file Y into blocks of an agreed-upon
     size N.
   - For each block, the destination computer computes two functions of the
     block's contents :
       - A 128-bit fingerprint of the block, which with very high
         probability is different from the fingerprints of different blocks.
       - A small checksum, which can be computed in a "rolling" fashion.
         More precisely, if we are given the checksum for the N-byte block
         at offset k, and we are given the bytes at offsets k and N+k, we
         can efficiently compute the checksum for the N-byte block at offset
         k+1.
   - The destination computer sends a list of fingerprints and checksums to
     the source computer. Blocks are identified implicitly by the order in
     which they appear in the list.
   - The source computer searches through file X to identify blocks that
     have the same fingerprints as blocks that appear in the list sent
     from B. The checksums are used to find candidate blocks in a single
     pass through file X. Blocks with identical fingerprints are presumed
     to be identical.
   - The source computer sends instructions for reconstructing file X at the
     destination. These instructions avoid transmitting blocks of X that are
     identical to other blocks in Y by providing the numbers of identical
     blocks and the strings containing the differences.
*)


(* Transfer instruction giving data to build a file incrementally *)
type transfer_instruction = Bytearray.t * int * int

type transmitter = transfer_instruction -> unit Lwt.t
val maxInstructionBytes : int
(** Maximum encoded token bytes emitted by the producer queue, excluding RPC
    tag/file identifier. No claim about represented logical output length. *)


(*************************************************************************)
(* GENERIC TRANSMISSION                                                  *)
(*************************************************************************)

(* Send the whole source file encoded in transfer instructions *)
val send :
    in_channel             (* source file descriptor *)
 -> Uutil.Filesize.t       (* source file length *)
 -> (int -> unit)          (* progress report *)
 -> transmitter            (* transfer instruction transmitter *)
 -> unit Lwt.t

type output_limit
val make_output_limit : Uutil.Filesize.t -> output_limit
(** Fresh logical payload allowance for one transfer, excluding an existing
    append prefix or container header. Nonnegative length; no large allocation.
    Owner-loop only: do not share concurrent mutation across workers/domains.
    Reservation is not OS closure/publication and is never refunded after IO. *)
val check_output_limit : output_limit -> unit
(** Rejects further payload work after logical EOF reservation. Call before
    opening lazy channels. This does not attest IO settlement or publication. *)

val receive :
    ?output_limit:output_limit ->
    out_channel            (* destination file descriptor *)
 -> (int -> unit)          (* progress report *)
 -> transfer_instruction   (* transfer instruction received *)
 -> bool                   (* Whether we have reach the end of the file *)
(** Checks the complete selected token slice before token payload writes.
    Invalid framing raises Util.Transient. The caller already owns the output
    channel; this does not establish publication or source identity.
    With an output limit, reserves the complete frame's logical bytes before
    token writes. EOF must exactly exhaust the allowance; subsequent calls
    refuse. Share one fresh allowance across all chunks of a payload. Failure
    after reservation aborts the transfer; there is no refund/retry authority. *)


(*************************************************************************)
(* RSYNC TRANSMISSION                                                    *)
(*************************************************************************)

module Rsync :
  sig

    (*** DESTINATION HOST ***)

    (* The rsync compression can only be activated when the file size is
       greater than the threshold *)
    val aboveRsyncThreshold : Uutil.Filesize.t -> bool

    (* Built from the old file by the destination computer *)
    type rsync_block_info

    val mrsync_block_info : rsync_block_info Umarshal.t

    (* Expected size of the [rsync_block_info] datastructure (in KiB). *)
    val memoryFootprint : Uutil.Filesize.t -> Uutil.Filesize.t -> int

    (* Compute block information from the old file *)
    val rsyncPreprocess :
           in_channel            (* old file descriptor *)
        -> Uutil.Filesize.t      (* source file length *)
        -> Uutil.Filesize.t      (* destination file length *)
        -> rsync_block_info * int

    (* Interpret a transfer instruction *)
    val rsyncDecompress :
           ?output_limit:output_limit ->
           int                   (* block size *)
        -> in_channel            (* old file descriptor *)
        -> out_channel           (* output file descriptor *)
        -> ?copyFn:              (* function for optimized copying *)
           (   Uutil.Filesize.t  (* input file offset *)
            -> Uutil.Filesize.t  (* data length *)
            -> fallback:         (* default function for copying *)
               (Uutil.Filesize.t (* bytes copied before fallback *)
                -> unit)
            -> unit)
        -> (int -> unit)         (* progress report *)
        -> transfer_instruction  (* transfer instruction received *)
        -> bool
    (** Preflights token framing, then checks block ranges and actual fallback
        read counts before writing each block chunk. Partial-copy fallback must
        report a count within the requested range. Util.Transient on refusal;
        earlier valid tokens may already have written staging data on a dynamic
        basis failure. An optional shared output limit pre-reserves the full
        frame, counting inherited/skipped blocks as logical materialization.
        It has the same exact EOF/no-refund contract as receive, independent of
        physical offsets or bytes written by an arbitrary copy callback.
        No hostile-writer atomicity/publication/physical IO claim. *)

    (*** SOURCE HOST ***)

    (* Using block information, parse the new file and send transfer
       instructions accordingly *)
    val rsyncCompress :
           rsync_block_info
                              (* block info received from the destination *)
        -> in_channel         (* new file descriptor *)
        -> Uutil.Filesize.t   (* source file length *)
        -> (int -> unit)      (* progress report *)
        -> transmitter        (* transfer instruction transmitter *)
        -> unit Lwt.t

  end
