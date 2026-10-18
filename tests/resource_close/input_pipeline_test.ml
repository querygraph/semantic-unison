let require b s=if not b then failwith s
let read name=let c=open_in_bin name in let s=really_input_string c(in_channel_length c) in close_in c;s
let write name s=let c=open_out_bin name in output_string c s;close_out c
let ()=
 Prefs.loadStrings ["semanticdng = true";"semanticmergebasecache = true";"semanticworkers = 1";"semanticvolumejobs = 1";"adobevalidate = off";"log = false"];
 Features.setEnabled(Features.all());
 let root=Fspath.canonize(Some(Sys.getcwd())) in
 let path name=Fspath.concat root(Path.fromString name) in
 let runtime=SemanticRuntime.get () in
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let settled ()=
  let a=SemanticRuntime.admission_usage () and w=SemanticWorkers.usage runtime.pool and io=IoAdmission.usage runtime.io in
  require(a.transactions=0 && a.pending=0 && a.descriptors=0 && a.payload_bytes=0) "transaction leak";
  require(w.running=0 && w.pending=0 && io.active_jobs=0 && io.pending=0) "work leak";
  require(HelperSupervisor.usage runtime.supervisor=(0,0)) "CPU leak";
  require(Array.length(Sys.readdir "/dev/fd")=baseline) "FD leak" in
 let before=List.map(fun n->n,read n)["base";"left";"right"] in
 let fingerprint=Os.data_only_fingerprint(Fingerprint.file root(Path.fromString "base")) in
 Lwt_unix.run(SemanticSync.capture_common_base_async ~root ~path:(Path.fromString "image.dng") ~source:(path "base"));
 settled();
 require(Option.is_some(SemanticMergeCache.load ~root ~path:(Path.fromString "image.dng") ~fingerprint)) "capture did not store base";
 ignore(Lwt_unix.run(SemanticSync.merge_local_async ~base_fingerprint:fingerprint ~base:(path "base") ~left:(path "left") ~right:(path "right") ~output:(path "output")));
 require(read "output"=read "expected") "saved-file merge not exact";settled();
 write "output" (read "left");
 ignore(Lwt_unix.run(SemanticSync.merge_local_async_with_cache ~cache:(root,Path.fromString "image.dng") ~base_fingerprint:fingerprint ~base:(path "absent-saved-base") ~left:(path "left") ~right:(path "right") ~output:(path "output")));
 require(read "output"=read "expected") "cached merge not exact";settled();
 List.iter(fun(n,s)->require(read n=s) "input bytes changed")before;
 require(SemanticSync.retained_inputs()=[]) "known pipeline retained";
 Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
 print_endline "PASS capture, saved-file and cached scalar merge; exact output; input bytes and all resource ledgers settled"
