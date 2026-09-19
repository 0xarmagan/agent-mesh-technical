# Validation run 1 — hard divergent question (2026-09-16)

## Question posed
A deliberately hard, divergent scenario spanning: a centralized-sequencer rollup joining EEZ, a threshold of 0, synchronous L1 reads, and composer censorship — chosen to diverge from the pipeline's usual based-rollup framing.

## Outcome
The pipeline answered successfully with `file:line` grounding throughout (no invented protocol facts). Six gaps were found during adjudication.

## Gaps found → fixes applied

1. **Eligibility vs. integration-path conflation** (`rollup-integration-engineer.md`) — the agent asserted a based-vs-centralized-sequencer integration-path divergence as established fact, when only eligibility (sequencing-agnostic, confirmed in `Rollup.sol`/`EEZ.sol`) is actually grounded; no repo doc enumerates a distinct centralized-sequencer path. → **FIX 1**: softened to state eligibility is sequencing-agnostic and mark path-divergence claims UNVERIFIED.
2. **Positioning/registration scope gap undocumented** — `positioning.md:82` scopes synchronous composability to based rollups sharing an L1 sequencing context, but registration itself is sequencing-agnostic; whether a centralized-sequencer rollup can be a first leg vs. only a second leg is unresolved and wasn't flagged anywhere. → **FIX 2a**: added to `knowledge/sources.md` Open questions.
3. **Composer censorship failure mode undocumented** — composer inclusion is a disclosed liveness dependency, but the dapp-observable failure mode (revert vs. stall vs. Sync-block rollback) isn't documented in source or docs. → **FIX 2b**: added to `knowledge/sources.md` Open questions.
4. **Missing key-file entry for synchronous L1 reads** — `staticCrossChainCall`, the primitive behind synchronous L1 reads, had no entry in the `knowledge/sources.md` key-file map despite being central to the scenario. → **FIX 3**: added entry citing `EEZ.sol:1313` (`staticCrossChainCall` definition) and `EEZ.sol:1412` (the static-path `StaticCallWithValue` revert, inside `_processNStaticCalls`). The initial citation in this entry was wrong — it cited `EEZ.sol:1126` for the static-path revert, but that line's revert belongs to `_processNCalls` (the non-static path), and `EEZ.sol:887` is a NatSpec comment, not code. Corrected in commit a419d92.
5. **Unverifiable finality figures in technical-accuracy gate** — the skill's distinction #1 asserted "~20 minutes" async / "~12 seconds" native figures and "async path"/"native rollup" terminology that ground in nothing in this repo or the source clone. → **FIX 4**: rewrote to keep the substance (native/synchronous composability, not an async bridge) and require any latency figure to be checked against `knowledge/sources.md` + `positioning.md` before use.
6. **Quality layer missing from CLAUDE.md** — CLAUDE.md named the DW execution layer (implementer/researcher/verifier/integrator) but never named the quality agents (`meta-advisor`, `completeness-critic`, `wiki-synchronizer`), so a reader following CLAUDE.md wouldn't discover them. → **FIX 5**: added one sentence naming all three.

## Parked (no action needed)
- **Pin-freshness assertion** — a claim that `.claude/skills/eez-protocol-dev/references/` pins are current. This is a self-documenting staleness note (the file already says "pinned to eez-core-protocol @ 9735f53, Aug 2026 — see its rename table for stale symbols") and doesn't need a fix; parked as acceptable as-is.
