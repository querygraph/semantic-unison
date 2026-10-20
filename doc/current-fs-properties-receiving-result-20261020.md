# Filesystem property transitions: actual result

Both compilers passed all 6 cases (17 calls) on 2026-10-20, with production at
`8581f357`:

- stock: `current-fs-properties-receiving-stock-20261019-02`;
- OxCaml: `current-fs-properties-receiving-ox-20261019-02`.

The owner audited every call from raw captures while it still held EXglobal IO
and CPU00..07. An independent post-closure replay (CPU08) matched both owner
audits. [Receipt](../tests/qualification/current-fs-properties-receiving-actual-20261020.json).

These cases close the end-to-end gaps the exactness and filesystem case maps
listed. Every transfer crosses the remote transport.

| Case | Shown end to end |
| --- | --- |
| zero-length | An empty file is created empty, grown to 4096 B, shrunk back to 0 and then deleted, with exact bytes after each call |
| holes | An 8 MiB file with a 6 MiB punched hole arrives byte-exact, and so does a one-byte delta update in the tail extent |
| xattr | With `-xattrs`, an xattr is set, changed and removed; the receiver's xattr names match exactly |
| xattr-default-off | Without `-xattrs`, setting an xattr is "Nothing to do" and nothing propagates |
| acl | With `-acl`, an extended ACL entry arrives with exact text, and clearing it propagates |
| acl-default-off | Without `-acl`, the ACL stays local |

**Finding: holes are not preserved over the remote transport.** The source
occupies 2 101 248 bytes on disk; both the first receipt and the delta update
allocate all 8 392 704 bytes. The bytes stay exact, so this is a space-use
limitation, not a correctness fault. A bare probe showed that local-to-local
synchronization keeps the holes through the clone path. Making remote
transfers sparse-aware would be a product change, which is not done here.

The failed predecessor `stock-01` is preserved with `FAILED-RECOVERY-CLOSED.json`.
Its zero-length deletion removed the only file in the root. Unison's batch
`confirmbigdel` guard then refused the deletion and exited 3. That is correct
safety behavior, and it showed a case-design error. The cases now keep an
anchor file, and the inert fakes model the guard.
