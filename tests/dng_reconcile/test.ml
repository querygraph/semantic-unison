let checks=Atomic.make 0
let check yes why=Atomic.incr checks;if not yes then failwith why
let fd p=Unix.openfile p [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let with_file p f=let d=fd p in Fun.protect ~finally:(fun ()->Unix.close d)(fun ()->SemanticFile.with_fd d f)
let extension=(module DngSemantic : FormatExtension.S)
let proof p=with_file p(fun file->match SemanticDelta.inspect extension file with Ok p->p | Error e->failwith e)
let () =
 let base=proof "base.dng" and left=proof "left.dng" and right=proof "right.dng" in
 let make l r file=SemanticDelta.reconcile_xmp extension ~nonce:(String.make 32 'n') ~base ~left:l ~right:r file in
 let plan=with_file "left.dng"(fun file->match make left right file with Ok p->p | Error e->failwith e) in
 let swapped=with_file "right.dng"(fun file->match make right left file with Ok p->p | Error e->failwith e) in
 check(SemanticDelta.target_digest plan=SemanticDelta.target_digest swapped)"replica order target differs";
 let expected=with_file "target.dng" SemanticFile.digest in
 check(SemanticDelta.target_digest plan=expected)"target digest differs from independent target";
 let output=Unix.openfile "stage.dng" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
 Fun.protect ~finally:(fun ()->Unix.close output)(fun ()->
   let report=with_file "left.dng"(fun basis->SemanticDelta.apply_report_with_extension extension plan ~basis ~output) in
   check(report.SemanticDelta.logical_bytes_written=3072 && report.write_calls=1)"write-window report differs");
 check(with_file "stage.dng" SemanticFile.digest=expected)"materialized target differs";
 let bad=proof "opaque.dng" in
 check(with_file "left.dng"(fun f->Result.is_error(make left bad f)))"opaque edit accepted";
 check(with_file "right.dng"(fun f->Result.is_error(make left right f)))"stale live basis accepted";
 let conflict=proof "conflict.dng" in
 check(with_file "left.dng"(fun f->Result.is_error(make left conflict f)))"competing rating accepted";
 let _,peer=match SemanticDelta.decode_request(SemanticDelta.encode_request ~nonce:(String.make 32 'p') base) with Ok p->p | Error e->failwith e in
 check(with_file "left.dng"(fun f->Result.is_error(SemanticDelta.reconcile_xmp extension ~nonce:(String.make 32 'n') ~base:peer ~left ~right f)))"peer-only base accepted";
 check(with_file "left.dng"(fun f->Result.is_error(SemanticDelta.reconcile_xmp extension ~nonce:"bad" ~base ~left ~right f)))"invalid nonce accepted";
 (* Merge-only /2: an opaque Exif MakerNote and primary-IFD DNGPrivateData are
    admitted, kept identical, and never allowed to overlap the XMP region.
    /0 and /1 still decline both. *)
 let maker=(module struct let profile=DngSemantic.opaque_maker_profile let inspect=DngSemantic.inspect_opaque_maker end : FormatExtension.S) in
 let refused p tag=with_file p(fun file->match DngSemantic.inspect file,DngSemantic.inspect_extended file with
   | Error a,Error b->a=b && a=Printf.sprintf "unsupported TIFF tag %d (opaque or private graph)" tag | _->false) in
 check(refused "maker-base.dng" 37500)"/0 or /1 admitted an opaque MakerNote";
 check(refused "priv-base.dng" 50740)"/0 or /1 admitted DNGPrivateData";
 let mproof p=with_file p(fun file->match SemanticDelta.inspect maker file with Ok p->p | Error e->failwith e) in
 let reason p=with_file p(fun file->match SemanticDelta.inspect maker file with Ok _->"accepted" | Error e->e) in
 List.iter (fun (p,expected) -> check(reason p=expected)(p^": "^reason p)) [
   "maker-alias.dng","XMP aliases protected extent"; "priv-alias.dng","XMP aliases protected extent";
   "maker-type.dng","invalid merge-only field type or count"; "priv-type.dng","invalid merge-only field type or count";
   "priv-ifd1.dng","DNGPrivateData outside primary IFD"; "base.dng","accepted";
   "scalar-base.dng","accepted"; "scalar-count.dng","invalid merge-only field type or count";
   "extra-base.dng","accepted"; "gain-type.dng","invalid merge-only field type or count";
   "long-unknown.dng","unsupported TIFF tag 60000 (opaque or private graph)";
   "gain-alias.dng","XMP aliases protected extent"];
 (* A run-time admission (dngmergeadmit) accepts exactly the named field. *)
 DngSemantic.admit_fields ["Image",60000,9];
 check(reason "long-unknown.dng"<>"accepted")"admission of another type accepted the field";
 DngSemantic.admit_fields ["Image",60000,4];
 check(reason "long-unknown.dng"="accepted")"admitted field still declined";
 DngSemantic.admit_fields [];
 check(refused "scalar-base.dng" 37393)"/0 or /1 admitted ImageNumber";
 let merges prefix=
   let file n=prefix^"-"^n^".dng" in
   let mb=mproof(file "base") and ml=mproof(file "left") and mr=mproof(file "right") in
   let mmake l r f=SemanticDelta.reconcile_xmp maker ~nonce:(String.make 32 'n') ~base:mb ~left:l ~right:r f in
   let mplan=with_file(file "left")(fun f->match mmake ml mr f with Ok p->p | Error e->failwith e) in
   let mexpected=with_file(file "target") SemanticFile.digest in
   check(SemanticDelta.target_digest mplan=mexpected)(prefix^": target digest differs from independent target");
   let moutput=Unix.openfile(file "stage") [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
   Fun.protect ~finally:(fun ()->Unix.close moutput)(fun ()->
     ignore(with_file(file "left")(fun basis->SemanticDelta.apply_report_with_extension maker mplan ~basis ~output:moutput)));
   check(with_file(file "stage") SemanticFile.digest=mexpected)(prefix^": materialized target differs");
   mmake ml in
 List.iter (fun (prefix,changed) ->
   let make=merges prefix in
   match changed with
   | None -> ()
   | Some p -> let bad=mproof p in
     check(with_file(prefix^"-left.dng")(fun f->match make bad f with
       | Error e->e="reconciliation protected bytes changed" | Ok _->false))(p^": changed opaque byte accepted"))
   ["maker",Some "maker-changed.dng"; "priv",Some "priv-changed.dng"; "both",None;
    "extra",Some "extra-changed.dng"; "sub",Some "sub-changed.dng"; "many",None; "undef",None; "comp",Some "comp-changed.dng"];
 check(with_file "sub-base.dng"(fun file->DngSemantic.inspect_extended file=Error "multiple XMP packets"))
   "/1 admitted a sub-image XMP packet";
 check(refused "extra-base.dng" 34858)"/0 or /1 admitted TimeZoneOffset";
 check(with_file "undef-base.dng"(fun file->DngSemantic.inspect_extended file=Error "unsupported XMP type or packet size"))
   "/1 admitted an UNDEFINED XMP packet";
 (* 302 properties: past the advisory observation limit, inside the merge limit. *)
 let packet=with_file "many-base.dng"(fun f->SemanticFile.read f 1024L 8192) in
 check(XmpObservation.observe packet=Error "XMP property limit exceeded")"observation limit raised";
 check(Result.is_ok(XmpMerge.merge ~base:packet ~left:packet ~right:packet))"merge refused a large packet";
 Printf.printf "PASS%d exact DNG reconciliation/materialization controls\n" (Atomic.get checks)
