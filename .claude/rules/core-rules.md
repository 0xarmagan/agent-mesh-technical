# Core Rules

<!-- Imported by CLAUDE.md — loaded at session start for all files -->

## EEZ Technical Source of Truth
- The canonical reference for every EEZ **contract-level / technical** fact is the repo **https://github.com/eez-association/eez-core-protocol** (branch `main`) — function signatures, error names, derivation math, structs, revert behavior, thresholds, opcode behavior. Ground technical claims in the actual `.sol` source, not in the KB explainers/deep-dive/Remix PoC/`00-conventions`.
- Those KB docs are **secondary** — conceptual framing only. **If a doc conflicts with the source, the source wins.**
- `main` moves: `git pull` / re-clone fresh before technical work; never trust a stale copy. Key file map lives in `knowledge/sources.md`.

## Wiki & Memory
- Read `wiki/index.md` and the linked note before citing a prior analysis as precedent.
- `wiki/meta/` files are created on first real need — a missing file means "nothing learned yet," not an error. If one exists but looks stale, flag it rather than silently re-deriving.
- After learning a durable user preference or correction, write it to `wiki/meta/user-prefs.md` (create if needed) — not just this session.
- If a `.claude/agent-memory/<Agent>/MEMORY.md` index drifts from the files actually present, treat it as a bug to fix.
- Before adding a new agent, skill, or pipeline mechanism, log the rationale as a `wiki:` entry in `wiki/log.md`.
- For speculative/hypothetical questions ("if we did X, what would...") that haven't been committed to or scheduled, a `wiki/log.md` entry is sufficient write-back — reserve `wiki/notes/` for decisions and analyses with standing reference value.
- Edit existing wiki notes and agent files in place rather than creating duplicates; re-check writebacks against `wiki/index.md` for stale or duplicate entries.
