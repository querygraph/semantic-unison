# Generated SDK fixture preservation

Actual owner `961bfc/exit0/NOsession` preserved two generated fixtures using native `fclonefileat` only. Both receiving clones are distinct, single-link, read-only inodes in persistent Unison-owned storage. Their 87,022,256 total bytes were hashed once against historical SHA256 values. Source epochs stayed unchanged; source payload hash bytes were zero. No SDK or Photo operation ran.

The exact plan and manifest bindings are in [the actual receipt](../tests/qualification/sdk-generated-fixture-preservation-actual-20261019.json). Independent metadata-only audit `4b1b2f/exit0/NOsession` verified the 14 execution pins, source/clone identities, manifest and row bindings, exact destination records, and canonical resource identities. The whole Unison8+EX bundle was freshly acquired and closed. This audit performed no extra payload hash.

Four original disposable controls passed (`12401d/0`): unchanged read-only/writable sources, distinct read-only destination, no overwrite, preserved failed hash target, and propagated close uncertainty without numeric retry. Test doubles are not native clone proof; the actual run supplies that narrow evidence.

Uncompressed and JPEG fixtures are preserved. JXL and the twelve scalar merge states remain missing. Current input binding accepts only `/private/tmp`; a versioned trusted persistent-root integration is still needed. The old shared-SDK-host V1/V2 results were inspected as metadata: their twelve calls reference the deleted original temporary inputs, not surviving working clones. No final Adobe matrix, semantic eligibility, pixel equivalence, production deployment, or complete goal claim follows.
