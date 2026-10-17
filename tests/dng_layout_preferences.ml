(* Current DNG layout capability boundary with the unchanged legacy wire schema. *)
let v0 = "org.firstpair.dng-xmp/0"
let v1 = "org.firstpair.dng-xmp/1"
let layout = "org.firstpair.dng-layout/0"
let names handles = List.map FormatExtension.profile handles
let local () = names (SemanticFormats.local_enabled ())
let peer () = names (SemanticFormats.peer_enabled ())
let raw_codec = Umarshal.(list (prod3 string bool string id id))
let profile_codec = Umarshal.(prod2 (list string) (list string) id id)
let bool_codec = Umarshal.(prod2 bool (list string) id id)
let plain_bool = Prefs.createBool "test-plain-bool" false
  ~category:(`Internal `Devel) "" ""
let plain_list = Prefs.createStringList "test-plain-list"
  ~category:(`Internal `Devel) "" ""
let raw dumped =
  Umarshal.from_string raw_codec (Umarshal.to_string Prefs.mdumpedPrefs dumped) 0
let wire entries =
  Umarshal.from_string Prefs.mdumpedPrefs (Umarshal.to_string raw_codec entries) 0
let checks = ref 0
let check condition = incr checks; assert condition
let reset () = Prefs.resetToDefaults (); Features.setEnabled (Features.all ())
let select ids = Prefs.loadStrings (List.map (fun id -> "semanticprofile = " ^ id) ids)
let dumped expected =
  let dump = Prefs.dump 1 in
  let values = raw dump in
  let _,_,alias = List.find (fun (name,_,_) -> name="semanticdng") values in
  check (Umarshal.from_string bool_codec alias 0 = (false,["semanticdng"]));
  check (alias=Umarshal.to_string bool_codec (false,["semanticdng"]));
  let _,_,plain = List.find (fun (name,_,_) -> name="test-plain-bool") values in
  check (plain=Umarshal.to_string bool_codec (Prefs.read plain_bool,["test-plain-bool"]));
  let _,_,plain = List.find (fun (name,_,_) -> name="test-plain-list") values in
  check (plain=Umarshal.to_string profile_codec (Prefs.read plain_list,["test-plain-list"]));
  let _,_,payload = List.find (fun (name,_,_) -> name="semanticprofile") values in
  let ids,names = Umarshal.from_string profile_codec payload 0 in
  check (ids=expected);
  check (names=["semanticprofile"]);
  check (payload=Umarshal.to_string profile_codec (expected,["semanticprofile"]));
  dump
let fatal f = try f (); false with Util.Fatal _ -> true
let () =
  check (Prefs.typ "semanticdng"=`BOOL);
  check (Prefs.typ "test-plain-bool"=`BOOL);
  check (Prefs.typ "semanticprofile"=`STRING_LIST);
  check (Prefs.typ "test-plain-list"=`STRING_LIST);
  reset (); select [v0];
  check (local ()=[v0]); ignore (dumped [v0]);
  check (local ()=[v0]);
  Prefs.set plain_bool true; ignore (dumped [v0]); check (Prefs.read plain_bool);
  Prefs.loadStrings ["test-plain-list = first";"test-plain-list = second"];
  ignore (dumped [v0]); check (Prefs.read plain_list=["second";"first"]);
  reset (); Prefs.loadStrings ["semanticdng = true"];
  check (local ()=[v1;v0;layout]); ignore (dumped [v1;v0;layout]);
  check (local ()=[v1;v0;layout]);
  Features.setEnabled ["dng-xmp-v0"];
  let alias_old = dumped [v0] in
  check (local ()=[v1;v0;layout]); check (peer ()=[v0]);
  (* A first server can retain a superset from its individual connection.
     Its stale true alias must be cleared, so final common IDs alone select v0. *)
  reset (); Prefs.loadStrings ["semanticdng = true"];
  check (local ()=[v1;v0;layout]); Prefs.load alias_old 1;
  check (local ()=[v0]); check (peer ()=[v0]);
  reset (); select [v0;v1];
  Features.setEnabled ["dng-xmp-v0"];
  ignore (dumped [v0]); check (local ()=[v1;v0]); check (peer ()=[v0]);
  Features.setEnabled (Features.all ());
  ignore (dumped [v1;v0]); check (local ()=[v1;v0]); check (peer ()=[v1;v0]);
  Features.resetEnabled ();
  ignore (dumped []); check (local ()=[v1;v0]); check (peer ()=[]);
  reset (); select [v1]; Features.setEnabled ["dng-xmp-v0"];
  ignore (dumped []); check (local ()=[v1]); check (peer ()=[]);
  (* Original v0 clients still send the shorthand boolean. Its loader must
     remain accepted; the separately negotiated capabilities exclude v1. *)
  reset (); Features.setEnabled ["dng-xmp-v0"];
  Prefs.load (wire ["semanticdng",true,
    Umarshal.to_string bool_codec (true,["semanticdng"])]) 1;
  check (local ()=[v1;v0;layout]); check (peer ()=[v0]);
  (* The public CLI accepts only one remote root. These actual preference
     boundary controls exercise both feature-intersection orders, not a claim
     of two-remote transport or synchronization support. *)
  List.iter (fun new_first ->
    List.iter (fun (alias,profiles,expected) ->
      reset (); select profiles;
      if alias then Prefs.loadStrings ["semanticdng = true"];
      let all = Features.all () in
      let old = List.filter (fun feature -> feature<>"dng-xmp-v1" && feature<>"dng-layout-exact-v0") all in
      let first,second = if new_first then all,old else old,all in
      let first_common = Features.inter all first in
      let final_common = Features.inter first_common second in
      Features.setEnabled final_common;
      let before = local () in
      let outgoing = dumped expected in
      check (local ()=before);
      List.iter (fun enabled ->
        reset (); select [v1]; Prefs.loadStrings ["semanticdng = true"];
        Features.setEnabled enabled;
        Prefs.load outgoing 1;
        check (local ()=expected); check (peer ()=expected))
        [first_common;final_common])
      [true,[],[v0]; false,[v0;v1],[v0]; false,[v1],[]])
    [true;false];
  reset (); Prefs.loadStrings ["semanticdng = true"];
  Features.setEnabled ["dng-xmp-v1";"dng-xmp-v0"];
  ignore(dumped [v1;v0]);check(local ()=[v1;v0;layout]);check(peer ()=[v1;v0]);
  Features.setEnabled ["dng-layout-exact-v0"];
  ignore(dumped [layout]);check(local ()=[v1;v0;layout]);check(peer ()=[layout]);
  Features.resetEnabled ();ignore(dumped []);check(peer ()=[]);
  reset ();select [layout];Features.setEnabled ["dng-xmp-v1";"dng-xmp-v0"];
  ignore(dumped []);check(local ()=[layout]);check(peer ()=[]);
  reset (); select ["org.firstpair.dng-xmp/typo"];
  check (fatal (fun () -> ignore (local ())));
  Features.resetEnabled ();
  check (fatal (fun () -> ignore (Prefs.dump 1)));
  Printf.printf "DNG layout preference boundary: %d checks; legacy wire, stale alias clearing, final intersection, local retention and typo rejection.\n" !checks
