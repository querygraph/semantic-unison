let describe file =
  match DngSemantic.component_regions file with
  | Error reason -> Error reason
  | Ok regions ->
    let regions=List.sort (fun (a:DngSemantic.component_region) b ->
      Int64.compare a.offset b.offset) regions in
    let rec disjoint stop = function
      | [] -> true
      | (region:DngSemantic.component_region)::rest ->
        region.offset>=stop && disjoint (Int64.add region.offset region.length) rest in
    if not(disjoint 0L regions) then Error "DNG component physical aliases unsupported"
    else
    let children=List.map (fun (region:DngSemantic.component_region) ->
      let role=match region.role with
        | DngSemantic.Image_bytes -> ComponentHash.Encoded_pixels
        | DngSemantic.Standard_value -> ComponentHash.Standard_metadata
        | DngSemantic.Private_value -> ComponentHash.Private_metadata
        | DngSemantic.Structure -> ComponentHash.Structural in
      {ComponentHash.id="dng/"^region.logical_id;schema=region.schema;
       role;offset=region.offset;length=region.length;children=[]}) regions in
    Ok {ComponentHash.id="dng";schema="dng-physical-partition/0";
        role=ComponentHash.Structural;offset=0L;length=SemanticFile.size file;children}
