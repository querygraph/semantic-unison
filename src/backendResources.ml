type coverage = Accounting_only | Allocator_callbacks of string list | Address_space
type t = {backend:string;cpu:int;bytes:int;covered:int;uncovered:int;descriptors:int;coverage:coverage}
let none = {backend="";cpu=0;bytes=0;covered=0;uncovered=0;descriptors=0;coverage=Accounting_only}
let identifier s = s <> "" && String.length s <= 128 && String.for_all
  (function 'a'..'z'|'A'..'Z'|'0'..'9'|'.'|'/'|'_'|'-' -> true | _ -> false) s
let sum a b =
  if a < 0 || b < 0 || a > max_int - b then invalid_arg "backend resource credit overflow";
  a+b
let make ~backend ~cpu_lanes ~covered_bytes ~uncovered_estimate ~descriptor_credits ~coverage =
  if not (identifier backend) || cpu_lanes < 1 || cpu_lanes > 128 ||
     descriptor_credits < 0 || descriptor_credits > 65536 then
    invalid_arg "invalid backend resource declaration";
  (match coverage with
   | Accounting_only -> if covered_bytes <> 0 then invalid_arg "accounting-only cannot claim covered allocations"
   | Allocator_callbacks names ->
       if covered_bytes <= 0 || names = [] || List.length names > 16 ||
          List.exists (fun s -> not (identifier s)) names ||
          List.length (List.sort_uniq String.compare names) <> List.length names then
         invalid_arg "invalid backend allocation coverage"
   | Address_space -> if covered_bytes <= 0 then invalid_arg "address-space limit must be positive");
  {backend;cpu=cpu_lanes;bytes=sum covered_bytes uncovered_estimate;
   covered=covered_bytes;uncovered=uncovered_estimate;descriptors=descriptor_credits;coverage}
let cpu_lanes t = t.cpu
let bytes t = t.bytes
let covered_bytes t = t.covered
let uncovered_estimate t = t.uncovered
let descriptors t = t.descriptors
let coverage t = t.coverage
let backend t = t.backend
let maximum plans = List.fold_left (fun total plan ->
  {none with backend="sequential-backends";cpu=max total.cpu plan.cpu;
   bytes=max total.bytes plan.bytes;uncovered=max total.bytes plan.bytes;descriptors=max total.descriptors plan.descriptors}) none plans
let add_cost t ~bytes ~descriptors = sum bytes t.bytes,sum descriptors t.descriptors

let equal a b = a = b
