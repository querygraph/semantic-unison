type verdict = Not_matched | Recognized | Indeterminate of string
module type S = sig
  val format : string
  val identify : SemanticFile.t -> verdict
end
type handle = { format : string; suffixes : string list; recognizer : (module S) }
let max_recognizers = 16
let trusted ?(suffixes=[]) ((module R : S) as recognizer) =
  if R.format = "" || String.length R.format > 128 || String.contains R.format '\000'
  then invalid_arg "invalid candidate format identifier";
  if List.length suffixes > 16 || List.exists (fun suffix ->
    String.length suffix < 2 || String.length suffix > 32 || suffix.[0] <> '.' ||
    String.contains suffix '\000' || String.contains suffix '/' ||
    String.contains suffix '\\') suffixes then
    invalid_arg "invalid candidate format suffix";
  {format=R.format;recognizer;
   suffixes=List.sort_uniq String.compare (List.map String.lowercase_ascii suffixes)}
let format handle = handle.format
let matches_filename handle filename =
  let filename = String.lowercase_ascii filename in
  List.exists (Filename.check_suffix filename) handle.suffixes
let identify handle file =
  let module R = (val handle.recognizer : S) in
  match R.identify file with
  | Indeterminate why when String.length why > 1024 ->
      Indeterminate (String.sub why 0 1024)
  | verdict -> verdict
