let check condition reason = if not condition then failwith reason
let bytes path = let input=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in input)
    (fun () -> really_input_string input (in_channel_length input))
let fixture length operation =
  let path=Filename.temp_file "snapshot-source-" "" in
  let target=Filename.temp_file "snapshot-output-" "" in
  let data=String.init length (fun i -> Char.chr ((i*71+13) land 255)) in
  let channel=open_out_bin path in output_string channel data;close_out channel;
  let source=Unix.openfile path [Unix.O_RDONLY] 0
  and output=Unix.openfile target [Unix.O_RDWR] 0 in
  Fun.protect ~finally:(fun () -> Unix.close source;Unix.close output;Sys.remove path;Sys.remove target)
    (fun () -> operation path target data source output)
let decline ~expected_length _ _=WholeFileClone.platform_decline ~expected_length
let copy ?(cancel=fun () -> ()) ?(limit=1048576L) ?(clone=decline) source output =
  ValidationSnapshot.materialize ~check_cancel:cancel ~max_bytes:limit ~clone ~source ~output
let rejected operation =
  match operation () with
  | _ -> failwith "expected snapshot refusal"
  | exception SemanticFile.Invalid _ | exception Invalid_argument _
  | exception Unix.Unix_error _ | exception WholeFileClone.Invalid_native_status _ -> ()
let () =
  List.iter (fun size -> fixture size (fun path target data source output ->
    let report=copy source output in
    check (bytes path=data && bytes target=data) "exact snapshot/source bytes";
    check (report.ValidationSnapshot.bytes=Int64.of_int size && not report.native_clone &&
      report.logical_bytes_written=Int64.of_int size) "ordinary snapshot accounting";
    let hash=SemanticHash.create () in SemanticHash.feed hash (Bytes.of_string data) 0 size;
    check (report.sha256=SemanticHash.hex (SemanticHash.finish hash)) "independent expected snapshot digest"))
    [0;1;65535;65536;65537;131111];
  fixture 100 (fun path target data source output ->
    let called=ref false in
    let clone ~expected_length a b=called:=true;decline ~expected_length a b in
    rejected (fun () -> copy ~clone ~limit:99L source output);
    check (not !called && bytes target="" && bytes path=data) "budget refusal precedes native/write";
    rejected (fun () -> copy source source);
    check (bytes path=data) "same-inode refusal preserved source";
    ignore (Unix.write_substring output "x" 0 1);
    rejected (fun () -> copy ~clone source output);
    check (not !called && bytes target="x") "nonempty output refusal precedes native/write");
  fixture 100 (fun path target data source output ->
    let clone ~expected_length:_ _ _=raise (Unix.Unix_error (Unix.EIO,"injected clone","")) in
    rejected (fun () -> copy ~clone source output);
    check (bytes target="" && bytes path=data) "native exception must not select fallback");
  fixture 100 (fun path target data source output ->
    let clone ~expected_length _ destination =
      ignore (Unix.write_substring destination data 0 100);
      ignore (Unix.LargeFile.lseek destination 0L Unix.SEEK_SET);
      WholeFileClone.Native_shared {requested=expected_length;completed=expected_length;
        backend=WholeFileClone.Macos_fclonefileat;phase=WholeFileClone.Cursor_verification;
        errno=None;native_code=0L;mutation=WholeFileClone.Known_prefix} in
    let report=copy ~clone source output in
    check (report.native_clone && report.logical_bytes_written=0L && bytes target=data && bytes path=data)
      "correct simulated native result verified without fallback");
  fixture 100 (fun path target data source output ->
    let clone ~expected_length _ _ =
      WholeFileClone.Failed {requested=expected_length;completed=0L;
        backend=WholeFileClone.Macos_fclonefileat;phase=WholeFileClone.Native_clone;
        errno=Some Unix.EIO;native_code=5L;mutation=WholeFileClone.No_effect} in
    rejected (fun () -> copy ~clone source output);
    check (bytes target="" && bytes path=data) "typed no-effect failure must not select fallback");
  fixture 100 (fun path target data source output ->
    let clone ~expected_length _ destination =
      ignore (Unix.write_substring destination (String.make 100 'X') 0 100);
      ignore (Unix.LargeFile.lseek destination 0L Unix.SEEK_SET);
      WholeFileClone.Native_shared {requested=expected_length;completed=expected_length;
        backend=WholeFileClone.Macos_fclonefileat;phase=WholeFileClone.Cursor_verification;
        errno=None;native_code=0L;mutation=WholeFileClone.Known_prefix} in
    rejected (fun () -> copy ~clone source output);
    check (bytes path=data && bytes target=String.make 100 'X')
      "claimed native success verified digest; no fallback overwrite");
  fixture 131111 (fun path target data source output ->
    let checks=ref 0 in
    let cancel ()=incr checks;if !checks=12 then raise Exit in
    (match copy ~cancel source output with
     | _ -> failwith "cancellation ignored" | exception Exit -> ());
    check (bytes path=data) "cancelled snapshot mutated source";
    check (String.length (bytes target)<=String.length data) "cancelled output escaped input size");
  print_endline "PASS snapshot exact/budget/alias/nonempty/native-success/native-failure/false-success/cancellation"
