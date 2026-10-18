exception Original_error
let require condition reason=if not condition then failwith reason
let make path =
  let ch=open_out_bin path in output_string ch (String.make 64 'r');close_out ch;
  Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let () =
  let mode=Sys.argv.(1) in
  let source=make "source" and inner=make "inner" in
  let source_stat=Unix.LargeFile.fstat source and inner_stat=Unix.LargeFile.fstat inner in
  if mode<>"known" && mode<>"known-error" then ReaderCloseFault.arm ~install:(mode="install");
  let operation () =
    SemanticFile.with_fd source (fun file ->
      require(SemanticFile.read file 0L 1="r") "wrong reader data";
      if mode="nested" then SemanticFile.with_fd inner (fun _ -> raise Original_error)
      else if mode="known-error" || mode="error" then raise Original_error
      else 17) in
  if mode="known" then require(operation ()=17) "known result missing"
  else if mode="known-error" then begin
    let correct=try ignore(operation ());false with Original_error -> true in
    require correct "known operation failure changed"
  end else begin
    let issue=try ignore(operation ());failwith "expected-reader-close-carrier"
      with SemanticFile.Close_uncertain issue -> issue in
    let stat=SemanticFile.close_issue_identity issue in
    require(stat.Unix.LargeFile.st_dev=source_stat.Unix.LargeFile.st_dev && stat.st_ino=source_stat.st_ino) "outer carrier identity changed";
    let close_failed issue=match SemanticFile.close_issue_cause issue with
      | Unix.Unix_error(Unix.EIO,_,_) -> true | _ -> false in
    require(close_failed issue) "close cause missing";
    if mode="nested" then begin
      let nested=match SemanticFile.close_issue_operation_error issue with
        | Some(SemanticFile.Close_uncertain nested) -> nested
        | _ -> failwith "inner carrier lost" in
      let stat=SemanticFile.close_issue_identity nested in
      require(stat.st_ino=inner_stat.st_ino && stat.st_ino<>source_stat.st_ino) "inner identity lost";
      require(close_failed nested && SemanticFile.close_issue_operation_error nested=Some Original_error) "nested causes lost";
      require(SemanticFile.close_issue_descriptor nested<>SemanticFile.close_issue_descriptor issue) "descriptor identities collapsed"
    end else if mode="error" then
      require(SemanticFile.close_issue_operation_error issue=Some Original_error) "operation error lost"
    else if mode="install" then
      require(SemanticFile.close_issue_operation_error issue=Some ReaderCloseFault.Install_failed) "installation error lost"
    else require(SemanticFile.close_issue_operation_error issue=None) "self-referential carrier";
    require(ReaderCloseFault.attempts ()=(if mode="nested" then 2 else 1)) "close retry detected";
    List.iter(fun fd -> ignore(Unix.fstat fd)) (ReaderCloseFault.replacements ());
    (* Even the original borrowed inputs remain valid; no retry touches them. *)
    ignore(Unix.fstat source);ignore(Unix.fstat inner)
  end;
  Printf.printf "PASS reader %s: exact error/identity chain, one close authority; process-exit settlement\n%!" mode
