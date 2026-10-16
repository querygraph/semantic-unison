let policy="org.firstpair.xmp-scalars-three-way/0"
exception Conflict of string
let conflict reason=raise(Conflict reason)
let merge ~base ~left ~right =
  try
    let view packet=match XmpObservation.scalar_view packet with
      | Ok view -> view | Error reason -> conflict reason in
    let b=view base and l=view left and r=view right in
    if b.shell<>l.shell || b.shell<>r.shell then
      conflict "non-allowlisted packet bytes changed";
    let fields view=List.map(fun (s:XmpObservation.scalar)->s.scalar_name) view.XmpObservation.scalars in
    if fields b<>fields l || fields b<>fields r then conflict "scalar shape changed";
    let choose (b:XmpObservation.scalar) (l:XmpObservation.scalar) (r:XmpObservation.scalar) =
      if l.value=b.value && r.value=b.value then b.encoded
      else if l.value=b.value then r.encoded
      else if r.value=b.value then l.encoded
      else if l.value=r.value then min l.encoded r.encoded
      else conflict "competing scalar edits" in
    let selected=List.map2(fun (b,l) r -> b,choose b l r)
      (List.combine b.scalars l.scalars) r.scalars in
    let output=Buffer.create(String.length base) and at=ref 0 in
    List.iter(fun ((scalar:XmpObservation.scalar),encoding)->
      Buffer.add_substring output base !at (scalar.first- !at);
      Buffer.add_string output encoding;at:=scalar.last) selected;
    Buffer.add_substring output base !at (String.length base- !at);
    if Buffer.length output>1048576 then conflict "merged packet limit";
    Ok(Buffer.contents output)
  with Conflict reason -> Error reason
