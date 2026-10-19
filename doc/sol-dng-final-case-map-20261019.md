# DNG parser, preservation and SDE case map — 2026-10-19

[Current SDE binding audit](sol-dng-final-case-bindings-20261019.json) freshly
matches82 explicit source bindings and4 saved artifacts across stock/Ox. The
original actual controller3582/9768d4/0/no session ran127 commands/2224 assertions
per compiler. No parser/test execution was repeated in this mapping audit.

[Fixed fixture inventory](sol-dng-fixed-case-inventory-20261019.json) enumerates
33 valid and247 invalid deterministic cases from existing source in memory.
It is an inventory, **not247 actual parser refusals**. No new fuzz campaign,
camera file, sparse file, or SDK operation was involved. Generated arbitrary
payloads are not pixel-valid photographs.

| Requirement | Source case | Evidence / remaining limit |
| --- | --- | --- |
| Both TIFF byte orders, exact packet patch | `tests/semantic/test.ml` fixed endian loop; `tests/semantic/conformance/run.py` golden dng-le/dng-be | Current SDE golden proof/wire/materialization coverage matches current explicit dependencies. Semantic test also has a random loop; this audit does not start that loop or a new campaign. |
| Classic versus BigTIFF, inline/out-of-line scalar widths | `tests/dng_profile_v1/fixtures.py:149`–257,266–308 |33valid fixture layouts include both endian orders, modern scalars, camera profiles and supported pointer/extent types. Extended-profile actual receipt must still be rebound/renewed against final parser source. |
| EXIF/GPS/Interop and SubIFD chains | `tests/dng_profile_v1/fixtures.py:186`–205; `tests/semantic/test.ml:210`–227 | Explicit graph layouts and work-limit refusals exist. Source coverage does not certify every camera graph. |
| Strip/tile/JPEG preview delineation | `tests/dng_profile_v1/fixtures.py:169`–172,190–208 | Protected extent placements cover primary/subimage strips/tiles and JPEG preview. They protect encoded bytes, not decoded-pixel equivalence. |
| Embedded original, opcodes, ICC | `tests/dng_profile_v1/fixtures.py:173`–177 | Independent opaque original-raw payload, three opcode-list payloads, ICC. `run.py:155`–171 mutates protected bytes and tail and requires Other_bytes, not editable metadata. No interpretation of opaque contents inferred. |
| MakerNotes/private tags | `tests/semantic/test.ml:201`–209; newer component/private fixtures | Conservative legacy refusal remains distinct from gradual private interpretation. Unknown fields may stay opaque and do not block deployment. Newer component receipts include changed sources and need their own final evidence scope. |
| Count/width overflow, duplicate/cyclic/repeated IFDs | `tests/dng_profile_v1/fixtures.py:333`–429 |247invalid fixtures include table geometry, field types, graph cardinality, cycles and relative camera-profile pointer violations. Inventory does not establish final actual rejection execution. |
| XMP aliases protected extents | `tests/dng_profile_v1/fixtures.py:430`–448,467–479; legacy fixed alias case | Exact header/table/pointer-list/pixels/original/opcode/profile/preview aliases are named. Both forward and inverse XMP alias cases exist. Broader profile actual-source mapping remains open. |
| >4GiB sparse offsets | `tests/dng_profile_v1/run.py:98`–129 | Existing four inspector-only sparse cases: primary or XMP high offset, both endian orders. No full-file digest/apply/physical savings claim; not executed by this inventory. |
| Entire noneditable complement | `tests/dng_profile_v1/run.py:155`–171; current SDE golden/binding vectors | Protected mutable blocks plus unreferenced tail changes cannot silently become metadata-only edits. No smaller-field meaning assumption is needed. |
| Malformed wire / wrong binding / exact apply | `tests/semantic/conformance/run.py:124`–183 and fixed golden vectors | Current strict-prefix truncation and nonce/profile/size/base/complement/region/hash/count binding checks. An envelope passing request binding still needs target verification during apply. |
| Stage alias/stale stage | `tests/semantic/test.ml:176`–185,228`–233 | Source has same-inode/wrong-basis prewrite refusal. Final scope must track the actual fixed suite, not infer safety from only a final digest. |

## Next required actions

- Renew or explicitly bind the extended `/1` parser and later component/private
  coverage against the final candidate. The Oct13/17 receipt names alone do not
  prove current-source execution after parser changes.
- Trace bounded XML/IFD work and component decoder limits to their actual cases;
  neither this inventory nor a green build substitutes for that mapping.
- Preserve all historical successes, refusals and limitations. New MakerNote
  plugins can refine interpretation/cache identities incrementally; exhaustive
  private-byte understanding is not a deployment gate.
- Run final receiving Adobe qualification only after source/fixtures are ready
  and Photo's current IO window is released. Do not reuse old admissions.

The in-memory inventory initially used a nonexistent lease-close method and
exited1 without child creation. Its failure is recorded in the inventory. The
fresh successor reacquired the same CPU4 set and explicitly closed descriptors
with the qualified closer, without inventing a child settlement. No resources
remain held by that operation. Photo bulk IO remains separately active.
