# Filesystems and compatibility (SOL rows 7 and 8) — case maps, 2026-10-19

Read-only mapping; nothing rerun. Receipts bind production by hash, not by
commit, and predate the fixes in `a5fd1bfb`, `defd5732`, `10c5d159` and
`8581f357` ([impact](production-delta-10c5d159-impact-20261019.md)).

## Row 7 — filesystems

| Concern | Tests | Evidence | Limits |
| --- | --- | --- | --- |
| Sparse files | native-stage "Real sparse input" (`F_PUNCHHOLE`, 16 blocks); parser sparse inspector cases | `final-native-stage-v2-actual-20261019.json` 5267/cfd95f/0, audit 2a4ba1/0; sparse creation 465356/0; V1 failure 24444/83daa3/137 preserved | stage snapshot only; no physical-sharing claim |
| Hardlinks | clone-sync held reader + hardlink; clone-interruption old destination/open-reader/hardlink; private-volume old receiver hardlink | clone-sync 43369/a6d4ef/0; interruption V3 61494/84393d/0, audit c160ba/0; private-volume V3 19831/bb1af5/0 | generated fixtures; not power loss |
| Open readers during replacement | sync-properties four old receiving readers; native-stage open snapshot | sync-properties 28308/7b837c/0, audit 455c91/0 | temporal owner evidence, not reopened descriptors |
| Resource forks, xattrs | sync-properties removal; native-stage stripping | as above | selected Darwin properties |
| ACLs | native-stage ACL removal on the private stage only | native-stage receipt | no end-to-end ACL sync transition |
| BSD flags | clone-sync `nodump` → `clone=require` exit 2, then `auto` fallback; native-stage strict refusal | clone-sync receipt (4 `chflags` children reaped 0) | other flags (uchg etc.) not covered |
| Stash / backup | sync-properties local versioned backup, version 0 exact | sync-properties receipt; V2 refusal and 57443/613b87/137 recovery preserved | no rotation; no backup combined with clone/semantic path |
| Cross-volume | private-volume 12 cases: stock/Ox × HFS+↔APFS × clone auto/off/DNG semantic | 19831/bb1af5/0, audit 604d3a/0 | distinct logical filesystems on one physical store |
| Non-APFS clone fallback | APFS→HFS+ exact fallback (generic and DNG) | same | inherited logical bytes are not physical writes |
| Platforms | Darwin only | — | Linux/BSD/Solaris/Windows runtime, ZFS/ReFS and other non-APFS execution unqualified |

Since 2026-10-20, ACL and xattr set/change/remove, the default-off controls,
zero-length files and punched holes run end to end through the remote
transport on both compilers ([result](current-fs-properties-receiving-result-20261020.md)).
Holes keep their bytes but are not preserved: the receiver is fully allocated.

Row 7 gaps: compressed-file and full fork transitions; sparse-aware remote
receive; backup
rotation and backup+semantic combinations; independent physical device,
remount and case-sensitivity cases.

## Row 8 — compatibility

| Concern | Tests | Evidence | Limits |
| --- | --- | --- | --- |
| Genuine upstream peer (current) | 4 orientations stock/Ox × upstream as client/server; seed/update/no-op; 12 calls | `final-default-upstream-peer-actual-20261019.json` 9111/c2e1e7/0 FOUR_CASE_PASS_CLOSED, audit 07dc8d/0; upstream 8772d26a | default `__new-rpc-mode`; 8 KiB fixtures; no real SSH |
| Genuine upstream / retained fork (V6 predecessor) | 12 + 12 calls | `sol-stream-v6-actual-adoption-20261018.json` upstream 67161/cf10d6/0, retained fork 90976/15836f/0 | predecessor candidate 5cc96102 / production 513c121a; never relabelled current |
| Installed old peer archive round trip | 10 stages per compiler via installed 2.53.5, incl. missing-base refusal exit 2 | `final-archive-roundtrip-actual-20261019.json` 29608/8c45ae/0 (18 zero + 2 designated exit 2), audit 9841ff/0; failed metadata audit 89306/915a05/137 preserved | 65 536 B fixture; no RPCv0, SSH or other platforms |
| RPC version range | VERSION 0/1/999 per compiler | `final-rpc-version-actual-20261019.json` 17884/a57f83/0, audit f10171/0 | accepts 1, refuses 0 and 999; RPCv0 dropped by user decision |
| Profiles / preferences | saved `compat.prf`; current-only preferences sent only to current endpoints | sync-properties 28308; default-upstream doc | no profile read by an old peer |
| Archive format / downgrade | round trip above; older `tests/archive_downgrade/qualification.json` | — | downgrade not inferred beyond the round trip |

Row 8 gaps: no receipt binds the final head by commit; no current retained-fork
rerun; only upstream 8772 and 2.53.5;
no real SSH, GUI or non-Darwin case. The stock↔OxCaml cross-compiler peer
suite (`current-cross-peer-receiving-{stock,ox}-20261019-03`: 5 cases and 12
calls per direction, covering seed/delta/no-op, server-side deletion, a skipped
conflict, xattr+ACL in both directions and a gated DNG receive at each endpoint)
passed with owner exit 0 in both directions. Its independent post-closure
replay is pending until the temporary18 series releases its CPU tokens.
