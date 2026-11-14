#!/usr/bin/env python3
"""Fixture tests for check_wiki_drift.py: python3 scripts/test_check_wiki_drift.py"""
import subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_wiki_drift as cwd


def sh(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        r = cls.repo = Path(cls.tmp.name) / "up"
        (r / "src" / "base").mkdir(parents=True)
        sh(r, "init", "-q", "-b", "main")
        sh(r, "config", "user.email", "t@t"); sh(r, "config", "user.name", "t")
        lines = [f"line{i}" for i in range(1, 21)]
        (r / "src" / "EEZ.sol").write_text("\n".join(lines) + "\n")
        (r / "src" / "base" / "Old.sol").write_text("a\nb\nc\n")
        (r / "src" / "Dead.sol").write_text("x\n")
        sh(r, "add", "-A"); sh(r, "commit", "-qm", "pin")
        cls.pin = sh(r, "rev-parse", "HEAD")
        # 3 lines inserted after line 2, line 10 edited, lines 15-16 deleted
        new = lines[:2] + ["ins1", "ins2", "ins3"] + lines[2:9] + ["EDITED"] + lines[10:14] + lines[16:]
        (r / "src" / "EEZ.sol").write_text("\n".join(new) + "\n")
        sh(r, "mv", "src/base/Old.sol", "src/base/New.sol")
        sh(r, "rm", "-q", "src/Dead.sol")
        sh(r, "add", "-A"); sh(r, "commit", "-qm", "head")
        cls.R = cwd.Repo(r, "HEAD")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def c(self, written, a, b=None):
        return self.R.classify(self.pin, written, a, b or a)

    def test_ok_before_any_hunk(self):
        self.assertEqual(self.c("EEZ.sol", 1)["status"], "OK")

    def test_moved_after_insertion(self):
        self.assertEqual(self.c("EEZ.sol", 5), {"status": "MOVED", "path": "src/EEZ.sol", "now": "EEZ.sol:8"})

    def test_changed_on_edited_line(self):
        self.assertEqual(self.c("src/EEZ.sol", 10)["status"], "CHANGED")

    def test_changed_on_deleted_line(self):
        self.assertEqual(self.c("EEZ.sol", 15)["status"], "CHANGED")

    def test_moved_after_insert_and_delete(self):
        # +3 inserted, -2 deleted before line 18 -> 19
        self.assertEqual(self.c("EEZ.sol", 18)["now"], "EEZ.sol:19")

    def test_range_touching_hunk_is_changed(self):
        self.assertEqual(self.c("EEZ.sol", 8, 11)["status"], "CHANGED")

    def test_insertion_inside_range_is_changed(self):
        # lines 2-3 straddle the 3-line insertion after line 2: both endpoints map cleanly
        # (2->2, 3->6) but the span grew, so the cited code changed
        self.assertEqual(self.c("EEZ.sol", 2, 3), {"status": "CHANGED", "path": "src/EEZ.sol"})

    def test_range_moved(self):
        self.assertEqual(self.c("EEZ.sol", 4, 6)["now"], "EEZ.sol:7-9")

    def test_rename_followed(self):
        self.assertEqual(self.c("Old.sol", 2), {"status": "MOVED", "path": "src/base/New.sol", "now": "New.sol:2"})

    def test_deleted_file_gone(self):
        self.assertEqual(self.c("Dead.sol", 1)["status"], "GONE")

    def test_unknown_basename(self):
        self.assertEqual(self.c("Nope.sol", 1)["status"], "UNKNOWN")


class Parser(unittest.TestCase):
    def cites(self, s):
        return [(Path(p).name, a, b) for p, a, b, _ in cwd.parse_citations(s)]

    def test_shapes(self):
        self.assertEqual(self.cites("see `src/EEZ.sol:826, :856`"), [("EEZ.sol", 826, 826), ("EEZ.sol", 856, 856)])
        self.assertEqual(self.cites("gate EEZ.sol:825/855)"), [("EEZ.sol", 825, 825), ("EEZ.sol", 855, 855)])
        self.assertEqual(self.cites("(`Rollup.sol:35,208-211`)"), [("Rollup.sol", 35, 35), ("Rollup.sol", 208, 211)])
        self.assertEqual(self.cites("in `Rollup.sol:104-122`."), [("Rollup.sol", 104, 122)])

    def test_frontmatter(self):
        self.assertEqual(cwd.frontmatter("---\nsource-commit: abc\nverified: x\n---\n# t"),
                         {"source-commit": "abc", "verified": "x"})
        self.assertEqual(cwd.frontmatter("# no fm\nsource-commit: abc"), {})


if __name__ == "__main__":
    unittest.main(verbosity=1)
