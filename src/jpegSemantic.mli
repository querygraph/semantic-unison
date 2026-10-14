(** Bounded standard JPEG APP1 XMP locator. At most8192 cumulative marker prefix/fill bytes. One nonempty standard packet before
    the first scan, one supported frame and a bounded marker header are required.
    Extended/duplicate packets and unsupported framing fall back to ordinary
    transfer. Entropy, subsequent scans, EXIF, ICC, opaque APP data and trailers
    are never interpreted or edited. This is not image validity/rendering proof.
    Core layout/complement/full-file checks require exact source reconstruction. *)
include FormatExtension.S
