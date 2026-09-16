# EEZ Source Map

## Repos (canonical, in priority order)
- https://github.com/eez-association/eez-core-protocol — branch `main`, THE source of truth for contract facts. Clone fresh: `gh repo clone eez-association/eez-core-protocol clones/eez-core-protocol`
- https://github.com/eez-association/eez-rollup0 — reference rollup implementation
- https://github.com/eez-association/sync-rollups-poc — earlier PoC, historical reference only

No local clones are kept in version control (`clones/` is gitignored). A missing clone is a setup error to surface, never a reason to fall back to doc memory.

## Key-file map (verified 2026-07-16, re-verify against fresh main)
- `src/base/EEZBase.sol` — `computeCrossChainProxyAddress`, the `SameNetworkProxy(rollupId)` guard in `_createCrossChainProxyInternal` (NOT in the view fn), `computeCrossChainCallHash`
- `src/base/CrossChainProxy.sol` — `executeOnBehalf` / `_fallback`
- `src/EEZ.sol` — `executeCrossChainCall` (reverts `ExecutionNotInCurrentBlock` / `ExecutionNotFound`)
- `src/rollupContract/Rollup.sol` — `threshold` + `checkProofSystemsAndGetVkeys` (`ThresholdNotMet(submitted,required)`, `ProofSystemNotAllowed`); threshold has NO protocol floor — may be 0
- `src/interfaces/IEEZ.sol` + `IEEZL2.sol` — structs `CrossChainCall`, `ExecutionEntry`
- Builder-utility ranking: rank primitives by frequency in `script/e2e/*`, not by doc prominence

## Working rules (carried from agent-mesh field experience)
- Build code demos at the primitive level; tell use-cases as vision content until the code catches up.
- Accuracy traps: the composer is permissionless and is not "EEZ"; composer-first ordering is a disclosed trust assumption, not an L1 guarantee; resolution ≠ settlement.

## Secondary material (conceptual only, conflicts lose to source)
- `.claude/skills/eez-protocol-dev/references/` in this repo (pinned to eez-core-protocol @ 9735f53, Aug 2026 — see its rename table for stale symbols)
- agent-mesh `eez-agent/knowledge/` explainers — DO NOT copy into this repo (internal/partner content); consult in place if needed.
