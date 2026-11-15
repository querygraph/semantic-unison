#!/usr/bin/env python3
"""The SQLite guard: verdicts on real and synthetic database groups, and what
a synchronization does with them.

    run.py --unison UNISON --probe PROBE [--upstream OLD-UNISON] [--keep]

Real fixtures come from Python's sqlite3, copied while a connection is open.
Synthetic write-ahead logs are written here, by code that shares nothing with
the guard.  Everything lives in a temporary directory.
"""
import argparse, os, shutil, sqlite3, struct, subprocess, sys, tempfile
from pathlib import Path

checks = failures = 0

def check(name, ok, detail=""):
    global checks, failures
    checks += 1
    if ok:
        print("ok   " + name)
    else:
        failures += 1
        print("FAIL " + name + (("\n     " + detail.replace("\n", "\n     ")) if detail else ""))

def section(name):
    print("\n== " + name)

# ---- Real fixtures -------------------------------------------------------

SUFFIXES = ("", "-journal", "-wal", "-shm")

def snapshot(db, dest):
    """Copy the database group as it is on disk right now."""
    for suffix in SUFFIXES:
        src = Path(str(db) + suffix)
        if src.exists():
            shutil.copyfile(src, str(dest) + suffix)

def connect(path, **kw):
    return sqlite3.connect(str(path), isolation_level=None, **kw)

def fill(con, rows, start=0, size=200):
    con.execute("BEGIN")
    con.executemany("INSERT INTO t VALUES (?, ?)",
                    [(start + i, bytes([i % 251]) * size) for i in range(rows)])
    con.execute("COMMIT")

def make_real(work, out):
    """Each fixture is a snapshot taken at the moment its name describes."""
    def fresh(name, mode):
        db = work / name
        con = connect(db)
        con.execute("PRAGMA page_size=4096")
        con.execute("PRAGMA journal_mode=" + mode)
        con.execute("CREATE TABLE t (k INTEGER PRIMARY KEY, v BLOB)")
        fill(con, 300)
        return db, con

    # Rollback journal, closed.
    db, con = fresh("closed-delete.db", "DELETE"); con.close(); snapshot(db, out / db.name)
    # PERSIST leaves a journal with a zeroed header; TRUNCATE an empty one.
    db, con = fresh("closed-persist.db", "PERSIST"); con.close(); snapshot(db, out / db.name)
    db, con = fresh("closed-truncate.db", "TRUNCATE"); con.close(); snapshot(db, out / db.name)

    # A transaction that has spilled into the journal and is not committed.
    db, con = fresh("hot-journal.db", "DELETE")
    con.execute("PRAGMA cache_size=1")
    con.execute("BEGIN")
    con.execute("UPDATE t SET v = zeroblob(900)")
    snapshot(db, out / db.name)
    con.execute("ROLLBACK"); con.close()

    # The same before SQLite has synced the journal: its header has no magic
    # number yet.  (Which of the two a given SQLite produces above depends on
    # when it spills its cache, so this one is written by hand.)
    db, con = fresh("unsynced-journal.db", "DELETE"); con.close()
    shutil.copyfile(db, out / db.name)
    (out / (db.name + "-journal")).write_bytes(
        bytes(12) + bytes.fromhex("daffddb2000000120000020000001000") + bytes(484))

    # WAL mode, closed cleanly.
    db, con = fresh("wal-closed.db", "WAL"); con.close(); snapshot(db, out / db.name)

    # WAL mode, a closed database opened read-only (P-28).
    db, con = fresh("wal-readonly-open.db", "WAL"); con.close()
    for suffix in ("-wal", "-shm"):
        Path(str(db) + suffix).unlink(missing_ok=True)
    ro = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    try:
        ro.execute("SELECT count(*) FROM t").fetchall()
    except sqlite3.OperationalError:
        # An older SQLite cannot open it read-only without the two files; a
        # newer one creates them empty, which is the case to keep.
        Path(str(db) + "-wal").write_bytes(b"")
        Path(str(db) + "-shm").write_bytes(bytes(32768))
    snapshot(db, out / db.name)
    ro.close()

    # WAL mode, open, with commits that are not in the main file.
    db, con = fresh("wal-live.db", "WAL")
    con.execute("PRAGMA wal_autocheckpoint=0")
    fill(con, 50, start=1000)
    snapshot(db, out / db.name)

    # The same after a full checkpoint: the log is still there, adds nothing.
    con.execute("PRAGMA wal_checkpoint(FULL)").fetchall()
    snapshot(db, out / "wal-redundant.db")

    # A write after the checkpoint restarts the log: a few new frames, then
    # the old ones, whose salts no longer match.
    con.execute("BEGIN"); con.execute("INSERT INTO t VALUES (5000, x'01')"); con.execute("COMMIT")
    snapshot(db, out / "wal-restarted.db")
    con.execute("PRAGMA wal_checkpoint(FULL)").fetchall()
    snapshot(db, out / "wal-restarted-redundant.db")
    con.close()

    # WAL mode, open, with frames of a transaction that has not committed
    # behind a log that was otherwise checkpointed.
    db, con = fresh("wal-uncommitted.db", "WAL")
    con.execute("PRAGMA wal_autocheckpoint=0")
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    con.execute("PRAGMA cache_size=1")
    con.execute("PRAGMA cache_spill=5")
    con.execute("BEGIN")
    con.execute("UPDATE t SET v = zeroblob(900)")
    snapshot(db, out / db.name)
    con.execute("ROLLBACK"); con.close()

    # Not a database at all, with a file named like a log beside it.
    (out / "text.db").write_text("not a database\n" * 20)
    (out / "text.db-wal").write_text("nor a log\n")

# ---- Synthetic write-ahead logs -----------------------------------------

def wal_sum(data, big, s0=0, s1=0):
    fmt = (">" if big else "<") + "II"
    for i in range(0, len(data), 8):
        x0, x1 = struct.unpack_from(fmt, data, i)
        s0 = (s0 + x0 + s1) & 0xffffffff
        s1 = (s1 + x1 + s0) & 0xffffffff
    return s0, s1

def make_wal(frames, page_size=1024, big=False, salts=(0x11223344, 0x55667788),
             bad_header=False, version=3007000):
    """frames: (page number, db size after commit or 0, page bytes, salts or None)."""
    head = struct.pack(">IIIIII", 0x377f0683 if big else 0x377f0682, version,
                       page_size, 7, *salts)
    s = wal_sum(head, big)
    out = head + struct.pack(">II", s[0] ^ (1 if bad_header else 0), s[1])
    for page, commit, content, frame_salts in frames:
        first = struct.pack(">II", page, commit)
        s = wal_sum(content, big, *wal_sum(first, big, *s))
        out += first + struct.pack(">II", *(frame_salts or salts)) + struct.pack(">II", *s) + content
    return out

def make_main(pages, page_size=1024):
    """A file with a SQLite header and the given page contents."""
    header = b"SQLite format 3\x00" + struct.pack(">H", page_size) + b"\x01\x01\x00\x40\x20\x20"
    first = header + bytes(page_size - len(header))
    return first + b"".join(pages[1:])

def make_synthetic(out):
    ps = 1024
    page = lambda k: bytes([k]) * ps
    main = make_main([None, page(2), page(3)])          # three pages
    first = main[:ps]

    def group(name, wal, main=main, journal=None):
        (out / name).write_bytes(main)
        if wal is not None:
            (out / (name + "-wal")).write_bytes(wal)
        if journal is not None:
            (out / (name + "-journal")).write_bytes(journal)

    # Every committed frame equals the main file, in both byte orders.
    same = [(2, 0, page(2), None), (3, 3, page(3), None)]
    group("syn-redundant-le.db", make_wal(same))
    group("syn-redundant-be.db", make_wal(same, big=True))
    # One committed page differs.
    group("syn-differs.db", make_wal([(2, 0, page(9), None), (3, 3, page(3), None)]))
    # The same page twice: only its last committed version counts.
    group("syn-overwritten.db",
          make_wal([(2, 3, page(9), None), (2, 3, page(2), None)]))
    # The commit says the database has four pages; the file has three.
    group("syn-grown.db", make_wal([(2, 4, page(2), None)]))
    # Frames with no commit at all.
    group("syn-uncommitted.db", make_wal([(2, 0, page(9), None), (3, 0, page(9), None)]))
    # A committed transaction, then frames of one that hasn't committed.
    group("syn-tail.db", make_wal([(2, 3, page(2), None), (3, 0, page(9), None)]))
    # A first frame with other salts: nothing in the log is valid.
    group("syn-stale.db", make_wal([(2, 3, page(9), (1, 2))]))
    # A valid redundant commit, then a stale frame: the log ends at the stale one.
    group("syn-stale-after.db",
          make_wal([(2, 3, page(2), None), (3, 3, page(9), (1, 2))]))
    # Damage: a bad header checksum, an unknown version, page number zero.
    # A frame with the log's salts that fails its checksum or is cut short
    # is one being written; with other salts it is only an old frame.
    group("syn-bad-header.db", make_wal([(2, 3, page(9), None)], bad_header=True))
    group("syn-bad-version.db", make_wal([(2, 3, page(9), None)], version=3007001))
    damaged = bytearray(make_wal([(2, 3, page(9), None)])); damaged[-1] ^= 1
    group("syn-bad-frame.db", bytes(damaged))
    group("syn-cut.db", make_wal([(2, 3, page(9), None)])[:-10])
    damaged = bytearray(make_wal([(2, 3, page(9), (1, 2))])); damaged[-1] ^= 1
    group("syn-bad-frame-stale.db", bytes(damaged))
    group("syn-scrap.db", make_wal([]) + b"\x00\x00\x00\x02scrap")
    group("syn-page-zero.db", make_wal([(0, 3, page(9), None)]))
    # A log whose page size isn't the database's.
    group("syn-page-size.db", make_wal([(2, 3, bytes(2048), None)], page_size=2048))
    # Header only, and shorter than a header.
    group("syn-header-only.db", make_wal([]))
    group("syn-short.db", b"\x37\x7f\x06\x82")
    # Journals: garbage, the magic alone, zeros, and empty.
    group("syn-journal-garbage.db", None, journal=b"garbage" * 10)
    group("syn-journal-magic.db", None, journal=bytes.fromhex("d9d505f920a163d7"))
    group("syn-journal-zeroed.db", None, journal=bytes(28) + b"old journal data")
    group("syn-journal-empty.db", None, journal=b"")
    # A file shorter than a header, and an empty one, are ordinary files.
    (out / "syn-tiny.db").write_bytes(b"SQLite format 3\x00")
    (out / "syn-empty.db").write_bytes(b"")
    (out / "syn-empty.db-wal").write_bytes(make_wal([(2, 3, page(9), None)]))

EXPECT = {
    # name: (state, substring of the detail or None)
    "closed-delete.db": ("quiet", None),
    "closed-persist.db": ("quiet", None),
    "closed-truncate.db": ("quiet", None),
    "hot-journal.db": ("busy", "-journal holds a transaction"),
    "unsynced-journal.db": ("busy", "-journal holds a transaction"),
    "wal-closed.db": ("quiet", None),
    "wal-readonly-open.db": ("quiet", None),
    "wal-live.db": ("busy", "committed frame"),
    "wal-redundant.db": ("redundant-wal", None),
    "wal-restarted.db": ("busy", "committed frame"),
    "wal-restarted-redundant.db": ("redundant-wal", None),
    "wal-uncommitted.db": ("busy", "running or was interrupted"),
    "text.db": ("not-database", None),
    "syn-redundant-le.db": ("redundant-wal", "2"),
    "syn-redundant-be.db": ("redundant-wal", "2"),
    "syn-differs.db": ("busy", "2 committed frames"),
    "syn-overwritten.db": ("redundant-wal", "2"),
    "syn-grown.db": ("busy", "1 committed frame the"),
    "syn-uncommitted.db": ("busy", "running or was interrupted"),
    "syn-tail.db": ("busy", "running or was interrupted"),
    "syn-stale.db": ("quiet", None),
    "syn-stale-after.db": ("redundant-wal", "1"),
    "syn-bad-header.db": ("quiet", None),
    "syn-bad-version.db": ("quiet", None),
    "syn-bad-frame.db": ("busy", "running or was interrupted"),
    "syn-cut.db": ("busy", "running or was interrupted"),
    "syn-bad-frame-stale.db": ("quiet", None),
    "syn-scrap.db": ("quiet", None),
    "syn-page-zero.db": ("quiet", None),
    "syn-page-size.db": ("busy", "1 committed frame the"),
    "syn-header-only.db": ("quiet", None),
    "syn-short.db": ("quiet", None),
    "syn-journal-garbage.db": ("busy", "neither empty nor a finished journal"),
    "syn-journal-magic.db": ("busy", "-journal holds a transaction"),
    "syn-journal-zeroed.db": ("quiet", None),
    "syn-journal-empty.db": ("quiet", None),
    "syn-tiny.db": ("not-database", None),
    "syn-empty.db": ("not-database", None),
}

def test_verdicts(probe, fixtures):
    section("verdicts (SQLite %s)" % sqlite3.sqlite_version)
    names = sorted(EXPECT)
    out = subprocess.run([probe, str(fixtures)] + names, capture_output=True, text=True, timeout=120)
    check("the probe ran", out.returncode == 0, out.stderr)
    got = {}
    for line in out.stdout.splitlines():
        fields = line.split("\t")
        got[fields[0]] = (fields[1], "\t".join(fields[2:]))
    for name in names:
        state, needle = EXPECT[name]
        actual = got.get(name, ("missing", ""))
        ok = actual[0] == state and (needle is None or needle in actual[1])
        check("%s is %s" % (name, state), ok, "found %s %s" % actual)
    # The oracle for "the log adds nothing": SQLite reads the group itself.
    for name in ("wal-live.db", "wal-redundant.db", "wal-restarted.db", "wal-restarted-redundant.db"):
        with tempfile.TemporaryDirectory(dir=str(fixtures.parent)) as scratch:
            snapshot(fixtures / name, Path(scratch) / "with.db")
            shutil.copyfile(fixtures / name, Path(scratch) / "without.db")
            def rows(db):
                con = sqlite3.connect(str(db))
                try:
                    return con.execute("SELECT count(*), max(k) FROM t").fetchall()
                except sqlite3.OperationalError as error:
                    return str(error)
                finally:
                    con.close()
            same = rows(Path(scratch) / "with.db") == rows(Path(scratch) / "without.db")
        check("%s: SQLite agrees that the log %s" % (name, "adds nothing" if same else "holds more"),
              same == (EXPECT[name][0] == "redundant-wal"))

# ---- Synchronizations ----------------------------------------------------

class Sync:
    def __init__(self, unison, top, name, remote=None, extra=()):
        self.a, self.b = top / (name + "-a"), top / (name + "-b")
        self.a.mkdir(); self.b.mkdir()
        self.state = top / (name + "-state"); self.state.mkdir()
        self.env = dict(os.environ, UNISON=str(self.state), HOME=str(top))
        second = str(self.b)
        self.args = [unison]
        if remote:
            launcher = top / (name + "-ssh.py")
            launcher.write_text("#!/usr/bin/env python3\nimport os,sys\na=sys.argv[1:]\n"
                                "i=a.index(%r)\nos.execv(a[i],a[i:])\n" % remote)
            launcher.chmod(0o700)
            second = "ssh://localhost/" + str(self.b)
            self.args += ["-sshcmd", str(launcher), "-servercmd", remote]
        self.args[1:1] = [str(self.a), second]
        self.args += ["-batch", "-ui", "text", "-fastcheck", "false",
                      "-sqlitedb", "Name *.db", "-logfile", str(top / (name + ".log"))] + list(extra)

    def run(self, *more):
        r = subprocess.run(self.args + list(more), env=self.env, capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout + r.stderr

def put(fixtures, name, root, as_name=None):
    """Place a fixture group in a replica, replacing what is there."""
    target = root / (as_name or name)
    for suffix in SUFFIXES:
        Path(str(target) + suffix).unlink(missing_ok=True)
    snapshot(fixtures / name, target)

def listing(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())

def scenarios(unison, fixtures, top, label, remote=None):
    section("synchronization, " + label)
    new = lambda name, extra=(): Sync(unison, top, label.replace(" ", "-") + "-" + name, remote, extra)

    s = new("quiet")
    put(fixtures, "closed-delete.db", s.a, "one.db")
    put(fixtures, "wal-readonly-open.db", s.a, "two.db")
    put(fixtures, "closed-persist.db", s.a, "three.db")
    code, out = s.run()
    check("quiet databases are copied", code == 0 and listing(s.b) == ["one.db", "three.db", "two.db"], out)
    check("the files beside them stay where they are",
          "two.db-wal" in listing(s.a) and "three.db-journal" in listing(s.a))

    s = new("sending")
    put(fixtures, "wal-live.db", s.a, "cat.db")
    put(fixtures, "hot-journal.db", s.a, "hot.db")
    put(fixtures, "closed-delete.db", s.a, "fine.db")
    code, out = s.run()
    check("a database with a live log or a hot journal is not sent, and the run says why",
          code != 0 and listing(s.b) == ["fine.db"]
          and "cat.db is not quiet" in out and "committed frame" in out
          and "hot.db is not quiet" in out, out)
    for suffix in ("-wal", "-shm"):
        (s.a / ("cat.db" + suffix)).unlink()
    (s.a / "hot.db-journal").unlink()
    code, out = s.run()
    check("once they are quiet they are sent", code == 0 and listing(s.b) == ["cat.db", "fine.db", "hot.db"], out)

    s = new("receiving")
    put(fixtures, "closed-delete.db", s.a, "cat.db")
    code, out = s.run()
    check("first copy", code == 0 and listing(s.b) == ["cat.db"], out)
    before = (s.b / "cat.db").read_bytes()
    # The receiver's copy is opened and written: a live log appears beside it.
    put(fixtures, "wal-live.db", s.b, "cat.db")
    (s.b / "cat.db").write_bytes(before)
    put(fixtures, "wal-closed.db", s.a, "cat.db")
    code, out = s.run()
    check("a database is not replaced under a live log",
          code != 0 and (s.b / "cat.db").read_bytes() == before
          and (s.b / "cat.db-wal").exists() and "not quiet" in out, out)

    s = new("redundant")
    put(fixtures, "wal-redundant.db", s.b, "cat.db")
    (s.b / "keep.txt").write_text("x")      # so that a replica is never emptied
    code, out = s.run()
    check("a database whose log adds nothing is sent, without its log",
          code == 0 and listing(s.a) == ["cat.db", "keep.txt"], out)
    kept = (s.b / "cat.db").read_bytes()
    put(fixtures, "closed-delete.db", s.a, "cat.db")
    code, out = s.run()
    check("but it is not replaced under that log",
          code != 0 and (s.b / "cat.db").read_bytes() == kept
          and "would corrupt" in out, out)
    (s.a / "cat.db").unlink()
    code, out = s.run()
    check("nor deleted under it", code != 0 and (s.b / "cat.db").read_bytes() == kept and "would corrupt" in out, out)

    s = new("directory")
    (s.b / "dir").mkdir()
    put(fixtures, "wal-redundant.db", s.b / "dir", "cat.db")
    (s.b / "dir" / "note.txt").write_text("x")
    (s.b / "keep.txt").write_text("x")
    code, out = s.run()
    check("a directory with a database is copied",
          code == 0 and listing(s.a) == ["dir/cat.db", "dir/note.txt", "keep.txt"], out)
    shutil.rmtree(s.a / "dir")
    code, out = s.run()
    check("a directory is not deleted over a database with a log",
          code != 0 and listing(s.b) == ["dir/cat.db", "dir/cat.db-shm", "dir/cat.db-wal", "dir/note.txt", "keep.txt"]
          and "would corrupt" in out, out)

    s = new("warn", ["-sqlitequiet", "warn"])
    put(fixtures, "wal-live.db", s.a, "cat.db")
    code, out = s.run()
    check("sqlitequiet = warn sends it and says so",
          code == 0 and listing(s.b) == ["cat.db"] and "not quiet" in out, out)

    s = new("off", ["-sqlitequiet", "off"])
    put(fixtures, "wal-live.db", s.a, "cat.db")
    code, out = s.run()
    check("sqlitequiet = off sends it silently, still without the files beside it",
          code == 0 and listing(s.b) == ["cat.db"] and "not quiet" not in out, out)

    s = new("ordinary")
    put(fixtures, "text.db", s.a)
    (s.a / "notes.txt").write_text("x")
    (s.a / "notes.txt-wal").write_text("y")
    code, out = s.run()
    check("a file that is no database is copied; a name like a log beside a named database is not",
          code == 0 and listing(s.b) == ["notes.txt", "notes.txt-wal", "text.db"], out)

    s = new("bad-value", ["-sqlitequiet", "sometimes"])
    put(fixtures, "closed-delete.db", s.a, "cat.db")
    code, out = s.run()
    check("an unknown sqlitequiet value stops the run", code != 0 and "off, warn or require" in out and listing(s.b) == [], out)

def old_peer(unison, upstream, fixtures, top):
    section("a peer without the guard (%s)" % Path(upstream).name)
    s = Sync(unison, top, "old-require", upstream)
    put(fixtures, "wal-live.db", s.a, "cat.db")
    code, out = s.run()
    check("sqlitequiet = require refuses to run, and names the feature",
          code != 0 and "sqlite-guard-v0" in out and listing(s.b) == [], out)
    s = Sync(unison, top, "old-warn", upstream, ["-sqlitequiet", "warn"])
    put(fixtures, "closed-delete.db", s.a, "cat.db")
    (s.a / "cat.db-wal").write_bytes(b"")
    code, out = s.run()
    check("sqlitequiet = warn runs without the guard and says so: both hosts see the same files",
          code == 0 and "no SQLite guard" in out and listing(s.b) == ["cat.db", "cat.db-wal"], out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unison", required=True)
    ap.add_argument("--probe", required=True)
    ap.add_argument("--upstream", help="a Unison without the guard, for the old-peer checks")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()
    unison, probe = str(Path(args.unison).resolve()), str(Path(args.probe).resolve())
    top = Path(tempfile.mkdtemp(prefix="unison-sqliteguard-", dir="/private/tmp"))
    try:
        fixtures, work = top / "fixtures", top / "work"
        fixtures.mkdir(); work.mkdir()
        make_real(work, fixtures)
        make_synthetic(fixtures)
        test_verdicts(probe, fixtures)
        scenarios(unison, fixtures, top, "two local roots")
        scenarios(unison, fixtures, top, "over a connection", remote=unison)
        if args.upstream:
            old_peer(unison, str(Path(args.upstream).resolve()), fixtures, top)
    finally:
        if args.keep:
            print("kept " + str(top))
        else:
            shutil.rmtree(top, ignore_errors=True)
    print("\n%d checks, %d failed" % (checks, failures))
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
