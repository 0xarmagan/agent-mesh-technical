#!/usr/bin/env python3
"""Citation drift check: re-verify `File.sol:N` citations in pinned notes against upstream main.

  check_wiki_drift.py [paths...] [--repo DIR] [--ref REF] [--no-fetch] [--json]

A note is pinned by a `source-commit: <sha>` line in its YAML frontmatter. For every
`File.sol:N[-M]` citation in a pinned note, the diff between the pin and REF (default
origin/main) classifies it as:
  OK       line untouched and unmoved
  MOVED    content untouched, line number shifted -> prints the new number
  CHANGED  a diff hunk touches the cited line(s), or lines were inserted inside
           a cited range -> re-read before citing
  Caveat: line-based, not semantic. A single-line citation (or a range outside any
  hunk) stays OK/MOVED even if its enclosing function, modifiers or callees changed.
  GONE     file deleted at REF (renames are followed)
  UNKNOWN  basename not found at the pin
Files with citations but no pin are listed as UNPINNED. `.rs` citations (eez-rollup0)
are counted as unchecked in v1. Report-only: never rewrites notes.

Exit 0 = no drift, 1 = drift (MOVED/CHANGED/GONE/UNKNOWN/UNPINNED), 2 = setup error. Stdlib only.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPO = ROOT / "clones" / "eez-core-protocol"
DEFAULT_PATHS = ["wiki", "knowledge"]

# `src/EEZ.sol:826, :856` · `EEZ.sol:825/855` · `Rollup.sol:35,208-211` · `Rollup.sol:104-122`
NUM = r"\d+(?:[-–]\d+)?"
CITE = re.compile(rf"(?P<path>[\w./-]*?[\w]+\.sol):(?P<nums>{NUM}(?:\s*[/,]\s*:?{NUM})*)")
RS_CITE = re.compile(r"[\w./-]*?[\w]+\.rs:\d+")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    return dict(
        (k.strip(), v.strip()) for k, _, v in
        (line.partition(":") for line in text[4:end].splitlines()) if _
    )


def parse_citations(text):
    """Yield (path_as_written, start, end, lineno_in_note)."""
    for m in CITE.finditer(text):
        note_line = text.count("\n", 0, m.start()) + 1
        for part in re.split(r"\s*[/,]\s*:?", m.group("nums")):
            a, _, b = part.replace("–", "-").partition("-")
            yield m.group("path"), int(a), int(b or a), note_line


def hunks(repo, pin, ref, old_path, new_path):
    out = git(repo, "diff", "-U0", "--no-color", f"{pin}:{old_path}", f"{ref}:{new_path}")
    return [(int(a), int(b or 1), int(c), int(d or 1)) for a, b, c, d in HUNK.findall(out)]


def map_line(line, hs):
    """Return new line number, or None if a hunk touches `line`."""
    offset = 0
    for old_start, old_len, _, new_len in hs:
        if old_len == 0:            # pure insertion after old_start
            if line > old_start:
                offset += new_len
        elif old_start <= line < old_start + old_len:
            return None
        elif line >= old_start + old_len:
            offset += new_len - old_len
    return line + offset


class Repo:
    def __init__(self, path, ref):
        self.path, self.ref = path, ref
        self._files, self._renames, self._hunks = {}, {}, {}

    def files_at(self, pin):
        if pin not in self._files:
            self._files[pin] = git(self.path, "ls-tree", "-r", "--name-only", pin).splitlines()
        return self._files[pin]

    def resolve(self, pin, written):
        """Map a citation's path (maybe a bare basename) to a full path at the pin."""
        written = written.lstrip("./")
        hits = [f for f in self.files_at(pin) if f == written or f.endswith("/" + written)]
        return hits[0] if len(hits) == 1 else None

    def status(self, pin, path):
        """('M'|'R'|'D'|None, new_path) for `path` between pin and ref."""
        if pin not in self._renames:
            table = {}
            for row in git(self.path, "diff", "-M", "--name-status", pin, self.ref).splitlines():
                cols = row.split("\t")
                table[cols[1]] = (cols[0][0], cols[-1])
            self._renames[pin] = table
        return self._renames[pin].get(path, (None, path))

    def classify(self, pin, written, start, end):
        path = self.resolve(pin, written)
        if path is None:
            return {"status": "UNKNOWN"}
        st, new_path = self.status(pin, path)
        if st == "D":
            return {"status": "GONE", "path": path}
        if st is None:
            return {"status": "OK", "path": path}
        key = (pin, path)
        if key not in self._hunks:
            self._hunks[key] = hunks(self.path, pin, self.ref, path, new_path)
        hs = self._hunks[key]
        mapped = [map_line(n, hs) for n in range(start, end + 1)]
        if any(m is None for m in mapped):
            return {"status": "CHANGED", "path": new_path}
        new_start, new_end = mapped[0], mapped[-1]
        if new_end - new_start != end - start:   # lines inserted inside the cited range
            return {"status": "CHANGED", "path": new_path}
        if (new_start, new_end) == (start, end) and new_path == path:
            return {"status": "OK", "path": path}
        span = str(new_start) if new_start == new_end else f"{new_start}-{new_end}"
        return {"status": "MOVED", "path": new_path, "now": f"{Path(new_path).name}:{span}"}


def scan(repo, notes):
    report = {"ref": repo.ref, "ref_sha": git(repo.path, "rev-parse", "--short", repo.ref).strip(), "files": []}
    for note in notes:
        text = note.read_text(encoding="utf-8")
        cites = list(parse_citations(text))
        rs = len(RS_CITE.findall(text))
        if not cites and not rs:
            continue
        rel = str(note.relative_to(ROOT)) if note.is_relative_to(ROOT) else str(note)
        pin = frontmatter(text).get("source-commit")
        entry = {"file": rel, "pin": pin, "rs_unchecked": rs, "citations": []}
        if pin:
            try:
                git(repo.path, "cat-file", "-e", f"{pin}^{{commit}}")
            except subprocess.CalledProcessError:
                entry["error"] = f"pin {pin} not found in {repo.path}"
                pin = None
        for written, a, b, note_line in cites:
            cite = {"cite": f"{Path(written).name}:{a}" + (f"-{b}" if b != a else ""), "line": note_line}
            cite.update(repo.classify(pin, written, a, b) if pin else {"status": "UNPINNED"})
            entry["citations"].append(cite)
        report["files"].append(entry)
    return report


def render(report):
    out = [f"# Citation drift vs {report['ref']} ({report['ref_sha']})", ""]
    for f in report["files"]:
        drift = [c for c in f["citations"] if c["status"] != "OK"]
        pin = (f["pin"] or "UNPINNED")[:7]
        ok = len(f["citations"]) - len(drift)
        out.append(f"## {f['file']}  (pin {pin}; {ok} OK, {len(drift)} drifted"
                   + (f", {f['rs_unchecked']} .rs unchecked" if f["rs_unchecked"] else "") + ")")
        if "error" in f:
            out.append(f"- ERROR: {f['error']}")
        for c in drift:
            extra = f" → {c['now']}" if c["status"] == "MOVED" else ""
            out.append(f"- {c['status']:<8} {c['cite']}{extra}  (note line {c['line']})")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=DEFAULT_PATHS)
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not (args.repo / ".git").exists():
        print(f"setup error: no clone at {args.repo} (see knowledge/sources.md)", file=sys.stderr)
        return 2
    if not args.no_fetch:
        try:
            git(args.repo, "fetch", "-q", "origin")
        except subprocess.CalledProcessError as e:
            print(f"warning: fetch failed, comparing against local {args.ref}: {e.stderr.strip()}", file=sys.stderr)

    notes = []
    for p in map(Path, args.paths):
        p = p if p.is_absolute() else ROOT / p
        # log.md is append-only history citing many past pins; check it only when named explicitly
        notes += sorted(n for n in p.rglob("*.md") if n.name != "log.md") if p.is_dir() else [p]
    report = scan(Repo(args.repo, args.ref), notes)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 1 if any(c["status"] != "OK" for f in report["files"] for c in f["citations"]) else 0


if __name__ == "__main__":
    sys.exit(main())
