let entries = Prefs.makeEndpointLocal (Prefs.createInt "validationtreeentries" 0
  ~local:true ~category:(`Advanced `General) "maximum entries per validation tree snapshot"
  "Zero retains unlimited legacy enumeration. A positive endpoint-local limit \
   bounds discovered entries, including hidden files, before name buffering. \
   This is a structural limit, not a heap/RSS bound.")
let path_bytes = Prefs.makeEndpointLocal (Prefs.createInt "validationtreepathbytes" 0
  ~local:true ~category:(`Advanced `General) "maximum path bytes per validation tree snapshot"
  "Zero retains unlimited legacy enumeration. A positive endpoint-local limit \
   bounds cumulative relative path bytes before name buffering. Properties, \
   symlink targets and native/SDK allocation are not counted as path bytes.")
let memory = Prefs.makeEndpointLocal (Prefs.createInt "validationtreememory" 0
  ~local:true ~category:(`Advanced `General) "estimated validation manifest budget in MiB"
  "Zero retains legacy manifest accounting. A positive endpoint-local budget \
   reserves two snapshots and file-validation workspaces before enumeration. \
   Retained metadata estimates are capped while scanning; this is not RSS or \
   a bound on transient property/native/SDK allocations. Changing it needs restart.")
let snapshot = ref None
let memory_bytes () =
  let mib = Prefs.read memory in
  if mib < 0 || mib > max_int / 2097152 then
    raise (Util.Fatal "Invalid validationtreememory budget");
  let bytes = mib * 1048576 in
  (match !snapshot with
   | None -> snapshot := Some bytes
   | Some previous when previous = bytes -> ()
   | Some _ -> raise (Util.Fatal "Restart Unison to change validationtreememory"));
  bytes
let budget () =
  let max_entries = Prefs.read entries and max_path_bytes = Prefs.read path_bytes in
  if max_entries < 0 || max_path_bytes < 0 then
    raise (Util.Fatal "Validation tree limits must be nonnegative");
  ValidationTreeBudget.create_with_memory ~max_memory_bytes:(memory_bytes ()) ~max_entries ~max_path_bytes
