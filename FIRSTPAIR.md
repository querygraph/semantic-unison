slug: semantic-unison
shelf: unix
default_edition: full

# Publication contract

This fork owns its code, the manual in `docs/semantic-unison-book.md`, the cover
and headboard in `cover/`, and the blog post in `docs/blog/semantic-unison/`.
FirstPair owns catalog entries, stable download and reader routes, and Blob
manifests. Follow the shared `~/src/firstpair/AGENTS.md` publication rules.

The book is by Alexy Khrabrov with Claude as co-author. Code in the book, like
packdir, is Apache 2.0. Semantic Unison derives from Unison and stays GPL v3.

`origin` here is upstream Unison, which takes no part in this book, so always
pass this fork as the source:

```sh
PATH=/usr/local/bin:$PATH ~/src/firstpair/publishing/scripts/build-library-book.sh --repo-root ~/src/semantic-unison
cd ~/src/firstpair
npm run library:publish -- ~/src/semantic-unison --source https://github.com/querygraph/semantic-unison
```
