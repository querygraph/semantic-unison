(* unison-dngscan: read-only survey of DNG files against the built-in merge.

   Walks the given paths, and for every *.dng file runs the same inspectors the
   merge uses: dng-xmp /0, /1 and the merge-only /2, then an identity XmpMerge of
   the embedded packet at its fixed length. A file that passes both can take a
   built-in merge. For any other file the /2 grammar is walked once more to list
   every field it does not know, not just the first. Files are opened read-only
   and only their TIFF directories and XMP packet are read; nothing is written
   under the scanned paths. Work is sharded over forked worker processes. *)

type verdict = Mergeable | Xmp_unsupported of string | Declined of string | Error of string

type record = {
  path : string; size : int64;
  v0 : bool; v1 : bool; v2 : bool; verdict : verdict;
  unknown : (string * int * int * int64) list;
}

let usage = "usage: unison-dngscan [-j WORKERS] [-cache WALK] [-admit IFD:TAG:TYPE]... [-tags REVIEW.tsv] [-o REPORT.jsonl [-resume]] PATH...\n\
\       unison-dngscan -semdiff ROOT... [-sameview] [-preserve | -preservefull] [-preservedb DIR] [-tree NAME | -suffix[=SUF]] [-review] [-v] [-hdd PATH [-readers N] | -ssd PATH]... [-catchup [-catchupto ROOT]] [-o REPORT.jsonl [-resume]] LEFT [-- UNISON-ARGS]\n\
\       unison-dngscan -summarize [-catchup ...] [-preserve ...] REPORT.jsonl... [-- UNISON-ARGS]"

let is_dng name =
  String.lowercase_ascii (Filename.extension name) = ".dng"

let cache_format = "unison-dngscan-walk/1"
let walk_dngs ?cache roots = ScanCommon.walk ?cache ~format:cache_format ~keep:is_dng roots

let read_packet file (region : FormatExtension.region) =
  let buffer = Buffer.create region.length in
  let rec loop at left =
    if left > 0 then begin
      let n = min left 1048576 in
      Buffer.add_string buffer (SemanticFile.read file at n);
      loop (Int64.add at (Int64.of_int n)) (left - n)
    end in
  loop region.offset region.length;
  Buffer.contents buffer

let ok = function Ok _ -> true | Result.Error _ -> false

let inspect path =
  let blank = {path; size = 0L; v0 = false; v1 = false; v2 = false;
               verdict = Error ""; unknown = []} in
  match Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 with
  | exception Unix.Unix_error (e, _, _) -> {blank with verdict = Error (Unix.error_message e)}
  | fd ->
      Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
        try
          SemanticFile.with_borrowed_fd fd (fun file ->
            let size = SemanticFile.size file in
            let v0 = ok (DngSemantic.inspect file) and v1 = ok (DngSemantic.inspect_extended file) in
            match DngSemantic.inspect_opaque_maker file with
            | Ok {FormatExtension.regions = [region]} ->
                let packet = read_packet file region in
                let verdict = match XmpMerge.merge ~base:packet ~left:packet ~right:packet with
                  | Ok merged when String.length merged = String.length packet -> Mergeable
                  | Ok _ -> Xmp_unsupported "identity merge changes packet length"
                  | Result.Error reason -> Xmp_unsupported reason in
                {blank with size; v0; v1; v2 = true; verdict}
            | Ok _ -> {blank with size; v0; v1; v2 = true; verdict = Xmp_unsupported "not one XMP region"}
            | Result.Error reason ->
                let unknown, _ = DngSemantic.unknown_fields file in
                {blank with size; v0; v1; verdict = Declined reason; unknown})
        with
        | SemanticFile.Invalid reason -> {blank with verdict = Error reason}
        | Unix.Unix_error (e, _, _) -> {blank with verdict = Error (Unix.error_message e)})

open ScanCommon

let verdict_fields = function
  | Mergeable -> "mergeable", ""
  | Xmp_unsupported r -> "xmp-unsupported", r
  | Declined r -> "declined", r
  | Error r -> "error", r

let json r =
  let kind, reason = verdict_fields r.verdict in
  Printf.sprintf "{\"path\":%s,\"size\":%Ld,\"dng-xmp/0\":%b,\"dng-xmp/1\":%b,\"dng-xmp/2\":%b,\"verdict\":%s,\"reason\":%s,\"unknown\":[%s]}"
    (json_string r.path) r.size r.v0 r.v1 r.v2 (json_string kind) (json_string reason)
    (String.concat "," (List.map (fun (d, tag, typ, n) ->
       Printf.sprintf "{\"ifd\":%s,\"tag\":%d,\"type\":%d,\"count\":%Ld}" (json_string d) tag typ n) r.unknown))

(* Reader for this command's own report lines, used by -resume. Lines that do
   not parse, such as one cut short when a run was stopped, are dropped and their
   files scanned again. *)
exception Bad_line

let record_of_line line =
  match (try parse line with Bad_json -> raise Bad_line) with
  | Obj fields ->
      let get k = try List.assoc k fields with Not_found -> raise Bad_line in
      let str k = match get k with Str s -> s | _ -> raise Bad_line in
      let bool k = match get k with Bool b -> b | _ -> raise Bad_line in
      let num v = match v with Num s -> Int64.of_string s | _ -> raise Bad_line in
      let reason = str "reason" in
      let verdict = match str "verdict" with
        | "mergeable" -> Mergeable | "xmp-unsupported" -> Xmp_unsupported reason
        | "declined" -> Declined reason | "error" -> Error reason | _ -> raise Bad_line in
      let unknown = match get "unknown" with
        | Arr items -> List.map (function
            | Obj f ->
                let g k = try List.assoc k f with Not_found -> raise Bad_line in
                (match g "ifd" with Str d -> d | _ -> raise Bad_line),
                Int64.to_int (num (g "tag")), Int64.to_int (num (g "type")), num (g "count")
            | _ -> raise Bad_line) items
        | _ -> raise Bad_line in
      {path = str "path"; size = num (get "size"); v0 = bool "dng-xmp/0";
       v1 = bool "dng-xmp/1"; v2 = bool "dng-xmp/2"; verdict; unknown}
  | _ -> raise Bad_line
  | exception (Failure _ | Invalid_argument _) -> raise Bad_line

(* Complete report lines from an earlier run, rewritten so the report ends on a
   whole line before new results are appended. *)
let load_report path =
  if not (Sys.file_exists path) then [] else begin
    let ch = open_in_bin path in
    let kept = ref [] in
    (try while true do
       let line = input_line ch in
       match record_of_line line with
       | r -> kept := (r, line) :: !kept
       | exception Bad_line -> ()
     done with End_of_file -> ());
    close_in ch;
    let kept = List.rev !kept in
    let temp = path ^ ".resume" in
    let out = open_out_bin temp in
    List.iter (fun (_, line) -> output_string out line; output_char out '\n') kept;
    close_out out;
    Sys.rename temp path;
    List.map fst kept
  end

let bump table key example =
  match Hashtbl.find_opt table key with
  | Some (n, e) -> Hashtbl.replace table key (n + 1, e)
  | None -> Hashtbl.replace table key (1, example)

let sorted table =
  List.sort (fun (k, (a, _)) (k', (b, _)) -> compare (b, k) (a, k')) (Hashtbl.fold (fun k v l -> (k, v) :: l) table [])

let () =
  let workers = ref 8 and report = ref "" and resume = ref false and cache = ref "" and roots = ref [] in
  let admit = ref [] and tags = ref "" in
  let semdiff = ref [] and sameview = ref false and summarize = ref false and catchup = ref false in
  let catchup_to = ref "" and catchup_file = ref "" and db = ref false and db_archive = ref "" in
  let rules = ref "" and exiftool = ref "" and unison = ref "" and unison_args = ref [] in
  let preserve_full = ref false and review = ref false and verbose = ref false and kinds = ref [] and readers = ref None and placement = ref (Semdiff.Tree "review") in
  (* -suffix=SUF: Arg has no optional values, so split it here. *)
  let argv = Array.concat (Array.to_list (Array.map (fun a ->
    if String.length a > 8 && String.sub a 0 8 = "-suffix=" then [|"-suffixname"; String.sub a 8 (String.length a - 8)|]
    else [|a|]) Sys.argv)) in
  (try Arg.parse_argv argv [
    "-suffixname", Arg.String (fun s ->
      if s = "" || String.contains s '/' then raise (Arg.Bad "-suffix=SUF: SUF must be a plain name");
      placement := Semdiff.Suffix s), "SUF  as -suffix=SUF";
    "-semdiff", Arg.String (fun r -> semdiff := !semdiff @ [r]),
      "ROOT  compare every file under LEFT with its match under ROOT (repeatable): same relative path, else same file name";
    "-sameview", Arg.Set sameview, " also decide whether a pair differs only in tags that cannot affect rendering";
    "-summarize", Arg.Set summarize, " summarize -semdiff reports given as arguments instead of scanning";
    "-catchup", Arg.Set catchup, " then run unison to copy what is missing (creation only)";
    "-catchupto", Arg.Set_string catchup_to, "ROOT  long-term root to catch up (default: the first -semdiff root)";
    "-catchupfile", Arg.Set_string catchup_file, "FILE  catch-up list (default: REPORT.catchup)";
    "-preserve", Arg.Set db, " store metadata differences in a dng-compare archive (default ROOT/.dng-compare/LEFT)";
    "-preservedb", Arg.String (fun d -> db := true; db_archive := d), "DIR  dng-compare archive for -preserve";
    "-preservefull", Arg.Unit (fun () -> db := true; preserve_full := true),
      " -preserve, and also keep each metadata-only file in full as a verified delta (dng-compare preserve_apo)";
    "-hdd", Arg.String (fun p -> kinds := !kinds @ [("hdd", p)]),
      "PATH  PATH's disk is spinning: one reader at a time; recorded for later runs (any path on the disk)";
    "-readers", Arg.Int (fun n -> if n < 1 || n > 64 then raise (Arg.Bad "-readers: 1..64"); readers := Some n),
      "N  streams that may read each -hdd disk at once (default 1); recorded with it";
    "-ssd", Arg.String (fun p -> kinds := !kinds @ [("ssd", p)]),
      "PATH  PATH's disk is solid state: parallel readers; recorded for later runs";
    "-v", Arg.Set verbose, " -semdiff: listing progress, each file that is not identical, preservation output";
    "-review", Arg.Set review, " from the -o report only: keep the files whose content differs, as -preserve does";
    "-tree", Arg.String (fun n -> placement := Semdiff.Tree n),
      "TREE  keep differing files under ROOT/../TREE/ROOTNAME/ (default review)";
    "-suffix", Arg.Unit (fun () -> placement := Semdiff.Suffix ""),
      " keep differing files beside the long-term file as NAME_2.EXT, NAME_3.EXT, ...; -suffix=SUF names NAME_SUF.EXT";
    "-rules", Arg.Set_string rules, "FILE  dng-compare metadata_rules.json (default $DNG_COMPARE_HOME or ~/src/dng-compare)";
    "-exiftool", Arg.Set_string exiftool, "PATH  dng-compare's metadata-extract-exiftool-rs-oxcaml worker";
    "-unison", Arg.Set_string unison, "PATH  unison binary for -catchup";
    "--", Arg.Rest (fun a -> unison_args := !unison_args @ [a]), "ARGS  further unison arguments for -catchup";
    "-j", Arg.Set_int workers, "N  worker processes, up to 256 (default 8); the scan is I/O bound";
    "-o", Arg.Set_string report, "FILE  write one JSON line per DNG as results arrive";
    "-cache", Arg.Set_string cache, "FILE  reuse and update directory listings whose mtime is unchanged";
    "-admit", Arg.String (fun spec -> match DngSemantic.parse_admission spec with
      | Ok field -> admit := !admit @ [field]
      | Error reason -> raise (Arg.Bad reason)),
      "IFD:TAG:TYPE  also admit this field in /2, as the dngmergeadmit preference does";
    "-tags", Arg.Set_string tags, "FILE  write the fields outside /2 as a review table with admit specs";
    "-resume", Arg.Set resume, " keep the complete lines already in the -o report, skip those files and append";
  ] (fun p -> roots := p :: !roots) usage
   with Arg.Bad m -> prerr_string m; exit 2 | Arg.Help m -> print_string m; exit 0);
  if (!roots = [] && not (!review && !report <> "")) || !workers < 1 || !workers > 256 || (!resume && !report = "") then
    (prerr_endline usage; exit 2);
  if !semdiff <> [] || !summarize || !review then begin
    let home = Semdiff.dng_compare_default () in
    Semdiff.run {Semdiff.left_roots = (if !summarize then [] else List.rev !roots); review = !review;
      preserve_full = !preserve_full; placement = !placement; verbose = !verbose; disk_kinds = !kinds; readers = !readers;
      right_roots = !semdiff; workers = !workers; report = !report; resume = !resume; cache = !cache;
      sameview_flag = !sameview; summarize = !summarize; reports = (if !summarize then List.rev !roots else []);
      catchup = !catchup; catchup_to = !catchup_to; catchup_file = !catchup_file;
      db = !db; db_archive = !db_archive;
      rules_path = (if !rules <> "" then !rules else Filename.concat home "metadata_rules.json");
      exiftool_path = !exiftool; dng_compare_home = home; unison_path = !unison; unison_args = !unison_args}
  end;
  DngSemantic.admit_fields !admit;
  let started = Unix.gettimeofday () in
  let all_files, walk_errors, (listed, reused) =
    walk_dngs ?cache:(if !cache = "" then None else Some !cache) (List.rev !roots) in
  (* Earlier results count only for files this walk found again. *)
  let found = Hashtbl.create (Array.length all_files) in
  Array.iter (fun p -> Hashtbl.replace found p ()) all_files;
  let earlier = if !resume then load_report !report else [] in
  let earlier = List.filter (fun r -> Hashtbl.mem found r.path && (Hashtbl.remove found r.path; true)) earlier in
  let files = List.filter (fun p -> Hashtbl.mem found p) (Array.to_list all_files) |> Array.of_list in
  Printf.eprintf "dngscan: %d DNG files found in %.0fs (%d directories read, %d from cache), %d already in the report; scanning %d with %d workers\n%!"
    (Array.length all_files) (Unix.gettimeofday () -. started) listed reused (List.length earlier)
    (Array.length files) !workers;
  let out = if !report = "" then None
    else Some (open_out_gen [Open_wronly; Open_creat; Open_binary; if !resume then Open_append else Open_trunc] 0o644 !report) in
  (* Report lines are written as results arrive, so a partial report is readable. *)
  let collected = ref earlier and last_flush = ref (Unix.gettimeofday ()) in
  let failed_workers = run_pool ~label:"dngscan" ~workers:!workers files inspect (fun (r : record) ->
    collected := r :: !collected;
    Option.iter (fun ch ->
      output_string ch (json r); output_char ch '\n';
      if Unix.gettimeofday () -. !last_flush >= 30. then (last_flush := Unix.gettimeofday (); flush ch)) out) in
  let results = List.sort (fun a b -> compare a.path b.path) !collected in
  let missing = Array.length all_files - List.length results in
  let verdicts = Hashtbl.create 8 and reasons = Hashtbl.create 32 and unknown = Hashtbl.create 64 in
  let profiles = Array.make 3 0 and bytes = ref 0L in
  List.iter (fun r ->
        bytes := Int64.add !bytes r.size;
        if r.v0 then profiles.(0) <- profiles.(0) + 1;
        if r.v1 then profiles.(1) <- profiles.(1) + 1;
        if r.v2 then profiles.(2) <- profiles.(2) + 1;
        let kind, reason = verdict_fields r.verdict in
        bump verdicts kind r.path;
        if reason <> "" then bump reasons (kind ^ ": " ^ reason) r.path;
        List.iter (fun (d, tag, typ, n) ->
          bump unknown (Printf.sprintf "%s tag %d type %d count %s" d tag typ
            (if n = 1L then "1" else "n")) r.path)
          (List.sort_uniq compare (List.map (fun (d, t, ty, n) -> d, t, ty, if n = 1L then 1L else 2L) r.unknown)))
    results;
  Option.iter close_out out;
  Printf.printf "DNG files: %d (%.1f GiB) in %.0fs\n" (Array.length all_files)
    (Int64.to_float !bytes /. 1073741824.) (Unix.gettimeofday () -. started);
  Printf.printf "accepted by inspector: dng-xmp/0 %d, /1 %d, /2 %d\n" profiles.(0) profiles.(1) profiles.(2);
  Printf.printf "\nverdicts:\n";
  List.iter (fun (k, (n, _)) -> Printf.printf "  %8d  %s\n" n k) (sorted verdicts);
  if Hashtbl.length reasons > 0 then begin
    Printf.printf "\nreasons (first stop of the real inspector or XMP merge):\n";
    List.iter (fun (k, (n, e)) -> Printf.printf "  %8d  %s\n            e.g. %s\n" n k e) (sorted reasons)
  end;
  (* Review table: one row per directory, tag and type, with the files that
     carry it and the spec that would admit it. *)
  let review = Hashtbl.create 64 in
  List.iter (fun r ->
    List.iter (fun (d, tag, typ) -> bump review (d, tag, typ) r.path)
      (List.sort_uniq compare (List.map (fun (d, t, ty, _) -> d, t, ty) r.unknown))) results;
  let review = List.sort (fun ((_, (a, _)) as x) ((_, (b, _)) as y) -> compare (b, fst x) (a, fst y))
      (Hashtbl.fold (fun k v l -> (k, v) :: l) review []) in
  if !tags <> "" then begin
    let ch = open_out_bin !tags in
    output_string ch "ifd\ttag\ttype\tfiles\tadmit\texample\n";
    List.iter (fun ((d, tag, typ), (n, e)) ->
      Printf.fprintf ch "%s\t%d\t%d\t%d\t%s:%d:%d\t%s\n" d tag typ n d tag typ e) review;
    close_out ch
  end;
  if !admit <> [] then
    Printf.printf "\nadmitted with -admit: %s\n" (String.concat " "
      (List.map (fun (d, t, ty) -> Printf.sprintf "%s:%d:%d" d t ty) !admit));
  if Hashtbl.length unknown > 0 then begin
    Printf.printf "\nfields outside dng-xmp/2 (files containing each):\n";
    List.iter (fun (k, (n, e)) -> Printf.printf "  %8d  %s\n            e.g. %s\n" n k e) (sorted unknown);
    Printf.printf "\nto try them, after review: %s\n" (String.concat " "
      (List.map (fun ((d, t, ty), _) -> Printf.sprintf "-admit %s:%d:%d" d t ty) review))
  end;
  if walk_errors <> [] then begin
    Printf.printf "\nunreadable paths: %d\n" (List.length walk_errors);
    List.iter (fun (p, e) -> Printf.printf "  %s: %s\n" p e) walk_errors
  end;
  if missing > 0 || failed_workers > 0 then
    Printf.printf "\nINCOMPLETE: %d files without a result, %d workers failed\n" missing failed_workers;
  let all_mergeable = Hashtbl.length verdicts = 1 && Hashtbl.mem verdicts "mergeable" in
  exit (if missing > 0 || failed_workers > 0 || walk_errors <> [] then 2
        else if all_mergeable then 0 else 1)
