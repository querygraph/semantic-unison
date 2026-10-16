type job={path:string;expected:string}
let () =
  let jobs : job SemanticMailbox.t=SemanticMailbox.create ~capacity:2 in
  let channel=open_in "expected.sha256" in let expected=input_line channel in close_in channel;
  (match SemanticMailbox.push jobs {path="input.bin";expected} with Added -> () | _ -> failwith "enqueue");
  SemanticMailbox.close jobs;
  let domain=Domain.Safe.spawn(fun () ->
    match SemanticMailbox.pop jobs with
    | Item job ->
        let fd=Unix.openfile job.path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
        let digest=SemanticFile.with_fd fd (fun file -> SemanticHash.hex(SemanticFile.digest file)) in
        Unix.close fd;if digest<>job.expected then failwith "digest"
    | _ -> failwith "missing job") in
  Domain.join domain;
  (match SemanticMailbox.pop jobs with Drained -> () | _ -> failwith "not drained");
  print_endline "PASS actual production CMI/CMX portable Hash File Mailbox contracts"
