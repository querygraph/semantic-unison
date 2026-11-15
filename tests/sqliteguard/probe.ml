(* Prints what SqliteGuard.inspect finds for each NAME in DIR:
     probe.exe DIR NAME...
   one line per name, "NAME<TAB>STATE[<TAB>DETAIL]". *)

let () =
  match Array.to_list Sys.argv with
  | _ :: dir :: names ->
      let root = Fspath.canonize (Some dir) in
      List.iter (fun name ->
        let line =
          match SqliteGuard.inspect root (Path.fromString name) with
          | SqliteGuard.Not_database -> "not-database"
          | SqliteGuard.Quiet -> "quiet"
          | SqliteGuard.Redundant_wal n -> Printf.sprintf "redundant-wal\t%d" n
          | SqliteGuard.Busy reason -> "busy\t" ^ reason
          | exception Util.Transient reason -> "error\t" ^ reason in
        Printf.printf "%s\t%s\n" name line) names
  | _ -> prerr_endline "usage: probe DIR NAME..."; exit 2
