let inspect path =
  let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let result=SemanticFile.with_fd fd (SemanticDelta.inspect (module JpegSemantic)) in
  Unix.close fd;result
let () = match Array.to_list Sys.argv with
  | [_;"inspect";path] ->
      (match inspect path with Error why -> Printf.printf "REJECT %s\n" why
       | Ok proof -> List.iter (fun r -> Printf.printf "REGION %Ld %d\n"
           r.FormatExtension.offset r.length) (SemanticDelta.describe proof).regions)
  | [_;"apply";basis;target;stage] ->
      (match inspect basis,inspect target with
       | Ok base,Ok target ->
           (match SemanticDelta.plan ~nonce:(String.make 32 'j') ~base ~target with
            | Error why -> Printf.printf "FALLBACK %s\n" why
            | Ok plan ->
                let b=Unix.openfile basis [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
                let o=Unix.openfile stage [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
                let report=SemanticFile.with_fd b (fun file ->
                  SemanticDelta.apply_report_with_extension (module JpegSemantic) plan ~basis:file ~output:o) in
                Unix.close b;Unix.close o;
                Printf.printf "APPLIED %d %d\n" report.SemanticDelta.logical_bytes_written report.write_calls)
       | _ -> print_endline "FALLBACK ineligible")
  | _ -> failwith "usage: inspect path | apply basis target stage"
