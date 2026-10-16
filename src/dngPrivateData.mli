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

type private_extent = {
  block_offset : int64;
  block_length : int64;
  locator_bytes_read : int;
  container_byte_order : byte_order;
  is_big_tiff : bool;
}
val max_ifd0_entries : int
val max_locator_read_bytes : int
(* Diagnostic only: classic TIFF or BigTIFF, either byte order, one primary
   BYTE[4] DNGVersion and one out-of-line BYTE DNGPrivateData. Does not walk
   other directories, inspect private bytes or establish closed references,
   XMP disjointness, DNG validity, vendor identity or semantic eligibility.
   Header/IFD0 overlap, duplicate selected tags, oversized or out-of-file
   extents decline. Unknown other IFD0 tags are ignored for this locator only.
   [read] addresses the entire file. Exact lengths are required; trusted-reader
   exceptions propagate. No existing profile calls this diagnostic API. *)
val locate_ifd0_private :
  read:(int64 -> int -> string) -> size:int64 -> (private_extent, string) result
