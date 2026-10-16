let check value message = if not value then failwith message
let read name = let channel=open_in_bin name in
  Fun.protect ~finally:(fun () -> close_in channel) (fun () -> really_input_string channel (in_channel_length channel))
let with_file name f = let fd=Unix.openfile name [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () -> SemanticFile.with_fd fd f)
let extension=(module DngSemantic : FormatExtension.S)
let proof path=with_file path (fun file -> match SemanticDelta.inspect extension file with
  | Ok proof -> proof | Error error -> failwith error)
let controls () =
  let base=proof "base.dng" in
  let encoded=SemanticDelta.encode_base_cache base in
  check (encoded=read "golden.sdb") "independent SDB bytes differ";
  let decoded=match SemanticDelta.decode_base_cache encoded with Ok proof -> proof | Error error -> failwith error in
  check (SemanticDelta.describe base=SemanticDelta.describe decoded) "cache proof changed";
  check (SemanticDelta.encode_base_cache decoded=encoded) "cache encoding not deterministic";
  let left=proof "left.dng" and right=proof "right.dng" in
  let plan=with_file "left.dng" (fun file -> match SemanticDelta.reconcile_xmp extension
    ~nonce:(String.make 32 'n') ~base:decoded ~left ~right file with
    | Ok plan -> plan | Error reason -> failwith reason) in
  check (SemanticDelta.target_digest plan=with_file "target.dng" SemanticFile.digest) "cached base exact target differs";
  List.iter (fun name -> check (Result.is_error (SemanticDelta.decode_base_cache (read name)))
    ("bad cache accepted: " ^ name))
    ["bad-checksum.sdb";"bad-version.sdb";"bad-policy.sdb";"bad-nonce.sdb";
     "bad-parsed.sdb";"bad-packet.sdb";"truncated.sdb";"oversized.sdb"];
  let _,peer=match SemanticDelta.decode_request (SemanticDelta.encode_request ~nonce:(String.make 32 'p') base) with
    | Ok claim -> claim | Error reason -> failwith reason in
  check (try ignore(SemanticDelta.encode_base_cache peer);false with Invalid_argument _ -> true)
    "peer-only claim exported as complete base";
  print_endline "PASS 13 independent compact-base codec/reconciliation controls"
let () = controls ()
