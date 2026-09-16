# EEZ Source Map

## Repos (canonical, in priority order)
- https://github.com/eez-association/eez-core-protocol — branch `main`, THE source of truth for contract facts. Clone fresh: `gh repo clone eez-association/eez-core-protocol clones/eez-core-protocol`
- https://github.com/eez-association/eez-rollup0 — reference rollup implementation
- https://github.com/eez-association/sync-rollups-poc — earlier PoC, historical reference only

No local clones are kept in version control (`clones/` is gitignored). A missing clone is a setup error to surface, never a reason to fall back to doc memory.

## Key-file map (verified 2026-09-16 against commit 03e87cddc05bf9c5fce97877498830c644f83192, re-verify against fresh main)
- `src/base/EEZBase.sol` — `computeCrossChainProxyAddress`, the `SameNetworkProxy(rollupId)` guard in `_createCrossChainProxyInternal` (NOT in the view fn), `computeCrossChainCallHash`
- `src/base/CrossChainProxy.sol` — `executeOnBehalf` / `_fallback`
- `src/EEZ.sol` — `executeCrossChainCall` (reverts `ExecutionNotInCurrentBlock` / `ExecutionNotFound`)
- `src/rollupContract/Rollup.sol` — `threshold` + `checkProofSystemsAndGetVkeys` (`ThresholdNotMet(submitted,required)`, `ProofSystemNotAllowed`); threshold has NO protocol floor — may be 0
- `src/interfaces/IEEZ.sol` (L1) + `IEEZL2.sol` (L2) — each file defines its OWN `ExecutionEntry` struct with different fields (L1: IEEZ.sol:127, has `rollupUpdates`/`l2ToL1Calls`; L2: IEEZL2.sol:73, has `incomingCalls`/`expectedOutgoingCalls`) — do not treat them as one shared struct. `CrossChainCall` exists ONLY in `IEEZL2.sol`:32; the L1-side equivalent is `L2ToL1Call`, not `CrossChainCall`.
- `src/EEZ.sol` — `staticCrossChainCall` (function definition at EEZ.sol:1313, `external view`) — the primitive behind synchronous L1 reads. It resolves via `_resolveStaticEntry` → `_processNStaticCalls` (EEZ.sol:1405), whose static sub-call dispatch reverts `StaticCallWithValue` at EEZ.sol:1412. (The `StaticCallWithValue` revert at EEZ.sol:1126 belongs to `_processNCalls`, the non-static entry-consumption dispatch reached from `_consumeAndExecuteEntry`/`executeCrossChainCall` — not to `staticCrossChainCall`.)
- Builder-utility ranking: rank primitives by frequency in `script/e2e/*`, not by doc prominence

## Working rules (carried from agent-mesh field experience)
- Build code demos at the primitive level; tell use-cases as vision content until the code catches up.
- Accuracy traps: the composer is permissionless and is not "EEZ"; composer-first ordering is a disclosed trust assumption, not an L1 guarantee; resolution ≠ settlement.

## Secondary material (conceptual only, conflicts lose to source)
- `.claude/skills/eez-protocol-dev/references/` in this repo (pinned to eez-core-protocol @ 9735f53, Aug 2026 — see its rename table for stale symbols)
- agent-mesh `eez-agent/knowledge/` explainers — DO NOT copy into this repo (internal/partner content); consult in place if needed.

## Open questions (validation 2026-09-16)
- **Positioning vs. registration scope mismatch.** `.claude/skills/eez-protocol-dev/references/positioning.md:82` scopes synchronous composability to "based rollups sharing an L1 sequencing context," while registration itself is sequencing-agnostic (nothing in `Rollup.sol`/`EEZ.sol` gates registration on sequencing topology). Whether a centralized-sequencer rollup can be a first leg (calling out) vs. only a second leg (called into) is unresolved in source/docs — do not assert either direction without a citation.
- **Composer censorship consequence.** Composer inclusion is a disclosed liveness dependency; a censored call is simply never composed — there is no on-chain error and no forced-inclusion mechanism found in source. The precise dapp-observable failure mode (revert vs. stall vs. Sync-block rollback) is not yet documented — mark UNVERIFIED if asked.
