# Clone-selected properties: source review

This is a source inspection, not runtime receiving qualification. The exact
generated-fixture request is [shared-property-io-request-v1.json](shared-property-io-request-v1.json).
It remains subject to its own fresh IO admission; no Photo payload is involved.

Receiver-basis staging is deliberately data-only. In `src/copy_stubs.c`, the
clone-stage path opens the owned stage by retained parent, verifies output
identity and single-link ownership, clears inherited ACLs, changes the working
mode to0600, and opens its writable descriptor. It then enumerates and removes
inherited xattrs. On Darwin this includes `com.apple.ResourceFork`. A failure
returns through the existing failed-stage ownership/cleanup path rather than
presenting a completed data-only clone. These operations target the new stage,
not the retained basis or an old reader's inode.

Both ordinary receiver-clone preparation in `src/copy.ml` and semantic staging
in `src/semanticRemote.ml` use this native clone-stage family. This review does
not extend those contracts to legacy or additional-name publication families.

`Copy.transferResourceForkAndSetFileinfo` transfers a resource fork only when
the source-selected fork length is nonzero. Thus the earlier data-only stage
normalization matters when an old destination has a fork and the new source
does not. The function subsequently loads extended property data and calls
`setFileinfo`; producer checks surround these operations before the final
fingerprint check.

`Props.Xattr.setXattrs` compares selected source attributes with current stage
attributes, writes changed selected values, and removes destination-only
selected names. Ignore preferences remain part of that comparison.
`Props.set` applies ownership and type/creator, xattrs, time, permissions, then
ACLs. Therefore selected readonly permissions do not precede xattr application;
ACL application remains after chmod as required by the existing property model.

The new matrix checks named xattr/fork removal,0640→0400 mode selection,
data/basis exactness, retained old-reader bytes/fork/xattr/mode, and no-op
identity/property epochs. It must establish actual behavior through the CLI,
not merely call the native stage helper. It does not establish arbitrary ACL,
ignored-xattr, AppleDouble, sparse/compressed, hostile-writer or power-loss
coverage. Old reader ctime/nlink are not invariants because replacing the
directory entry legitimately changes them.
