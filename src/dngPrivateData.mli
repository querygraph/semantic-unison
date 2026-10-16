(** Bounded framing evidence for one explicitly recognized DNGPrivateData
    container. This is NOT a format-extension eligibility proof: embedded maker
    structures still need a separately qualified closed-reference policy. No
    existing DNG profile calls this module or widens its accepted tag set. *)
type byte_order = Little | Big
type maker_section = {
  payload_offset : int64;
  payload_length : int64;
  original_offset : int64;
  byte_order : byte_order;
}
type framing = { sections : maker_section list; header_bytes_read : int }
val max_block_length : int64
val max_sections : int
(* [read] uses offsets relative to the proposed private block, not the TIFF.
    Reads only framing bytes, never maker payloads. Exact lengths are required.
    Other creators, section keys, trailing bytes and nonzero alignment padding
    are conservative declines. Exceptions from the trusted reader propagate. *)
val inspect_adobe_makn :
  read:(int64 -> int -> string) -> length:int64 -> (framing, string) result
