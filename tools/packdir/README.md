# unison-packdir

`unison-packdir` is the [`packdir`](https://github.com/querygraph/packdir) command, installed
beside `unison` under this name. All of its code, and its tests, live in that project: packing,
unpacking, repacking, verifying, and the GNU-style `ls`, `cat`, `stat`, `du`, `find`, `rm`, `cp` and
`mv` over packed trees.

Unison's packed roots link the same library (`Packdir.Container`) through
`src/packdirSupport.sqlite.ml`. When the opam `packdir` package isn't installed, dune skips this
tool and Unison builds without packed roots, refusing `packdepth` with a message. The design is in
[`docs/packdir-design.md`](../../docs/packdir-design.md).

```sh
opam pin add -y --switch 5.4.0+ox packdir ~/src/packdir
opam pin add -y --switch default packdir ~/src/packdir
```

`unison-bench.sh` and `cold-remount.sh` are the benchmarks of Unison itself onto Ten.
