let check yes why=if not yes then failwith why
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
 (* Merge-only /2: an opaque Exif MakerNote is admitted, kept identical, and
    never allowed to overlap the XMP region. /0 and /1 still decline it. *)
 let maker=(module struct let profile=DngSemantic.opaque_maker_profile let inspect=DngSemantic.inspect_opaque_maker end : FormatExtension.S) in
 let refused p=with_file p(fun file->match DngSemantic.inspect file,DngSemantic.inspect_extended file with
   | Error a,Error b->a=b && a="unsupported TIFF tag 37500 (opaque or private graph)" | _->false) in
 check(refused "maker-base.dng")"/0 or /1 admitted an opaque MakerNote";
 let mproof p=with_file p(fun file->match SemanticDelta.inspect maker file with Ok p->p | Error e->failwith e) in
 let reason p=with_file p(fun file->match SemanticDelta.inspect maker file with Ok _->"accepted" | Error e->e) in
 check(reason "maker-alias.dng"="XMP aliases protected extent")"MakerNote overlapping XMP accepted";
 check(reason "maker-type.dng"="invalid opaque MakerNote type")"non-opaque MakerNote type accepted";
 check(reason "base.dng"="accepted")"/2 declined the plain v0 fixture";
 let mb=mproof "maker-base.dng" and ml=mproof "maker-left.dng" and mr=mproof "maker-right.dng" in
 let mmake l r file=SemanticDelta.reconcile_xmp maker ~nonce:(String.make 32 'n') ~base:mb ~left:l ~right:r file in
 let mplan=with_file "maker-left.dng"(fun file->match mmake ml mr file with Ok p->p | Error e->failwith e) in
 let mexpected=with_file "maker-target.dng" SemanticFile.digest in
 check(SemanticDelta.target_digest mplan=mexpected)"MakerNote target digest differs from independent target";
 let moutput=Unix.openfile "maker-stage.dng" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
 Fun.protect ~finally:(fun ()->Unix.close moutput)(fun ()->
   ignore(with_file "maker-left.dng"(fun basis->SemanticDelta.apply_report_with_extension maker mplan ~basis ~output:moutput)));
 check(with_file "maker-stage.dng" SemanticFile.digest=mexpected)"materialized MakerNote target differs";
 let changed=mproof "maker-changed.dng" in
 check(with_file "maker-left.dng"(fun f->match mmake ml changed f with
   | Error e->e="reconciliation protected bytes changed" | Ok _->false))"changed MakerNote byte accepted";
 print_endline "PASS16 exact DNG reconciliation/materialization controls"
