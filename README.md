# Semantic Unison

[Semantic Unison](https://github.com/querygraph/semantic-unison) is an
**LLM-friendly fork of [Unison](https://github.com/bcpierce00/unison)** with
semantic extensions for efficient, trustworthy file synchronization.
AI-assisted code, documentation, and contributions are welcome, with transparent
attribution, reviewable changes, and testing.

Our goals:

- **Semantic hashing:** distinguish image payloads, standard metadata, previews,
  and private fields while preserving unknown bytes exactly.
- **Gradual camera understanding:** grow DNG and MakerNote coverage through
  composable, versioned plugins and incremental refinement of component hashes.
- **Precise updates and merges:** transfer bounded metadata changes and merge
  compatible edits while verifying the exact resulting file.
- **APFS clone updates:** reuse the receiver’s existing data in a private clone,
  reducing unnecessary rewriting for ordinary files as well as photographs.
- **Optional Adobe validation:** check DNG structure, decoding, and raw digests
  through explicitly configured validation policies.
- **Coordinated parallelism:** use OCaml and OxCaml workers efficiently, with
  explicit ownership, cancellation, and shared resource budgets.

We credit Unison’s authors and retain the project’s existing [licensing](LICENSE) and
attribution. This fork is maintained independently of upstream.

Read the [design](SOL.md) and
[the manifesto](I-AM-AN-HONEST-WORKING-LLM.md).
