---
source-commit: 03e87cddc05bf9c5fce97877498830c644f83192
verified: 2026-09-16
---

# Source map verification

Fresh clone of `eez-association/eez-core-protocol` @ `main`, verified against
`knowledge/sources.md`'s key-file map. All symbols matched; no files or
symbols moved since the map's prior 2026-07-16 verification. One ambiguity in
the map's wording was clarified in the same commit (see Corrections below).

## Symbol → file:line

| Symbol | File | Line |
|---|---|---|
| `computeCrossChainProxyAddress` (definition) | `src/base/EEZBase.sol` | 228 |
| `SameNetworkProxy(rollupId)` error (declaration) | `src/base/EEZBase.sol` | 162 |
| `SameNetworkProxy` revert site (in `_createCrossChainProxyInternal`, not the view fn) | `src/base/EEZBase.sol` | 218 |
| `_createCrossChainProxyInternal` (definition) | `src/base/EEZBase.sol` | 210 |
| `computeCrossChainCallHash` (definition) | `src/base/EEZBase.sol` | 254 |
| `executeOnBehalf` (dispatch in fallback) | `src/base/CrossChainProxy.sol` | 52-53 |
| `_fallback` (definition) | `src/base/CrossChainProxy.sol` | 86 |
| `executeCrossChainCall` (definition) | `src/EEZ.sol` | 807 |
| `ExecutionNotInCurrentBlock` (declaration) | `src/EEZ.sol` | 203 |
| `ExecutionNotFound` (revert site) | `src/EEZ.sol` | 1231 |
| `threshold` (state var) | `src/rollupContract/Rollup.sol` | 35 |
| `checkProofSystemsAndGetVkeys` (definition) | `src/rollupContract/Rollup.sol` | 106 |
| `ThresholdNotMet(submitted,required)` (declaration) | `src/rollupContract/Rollup.sol` | 58 |
| `ProofSystemNotAllowed` (declaration) | `src/rollupContract/Rollup.sol` | 51 |
| threshold has no protocol floor (owner can set 0 or any value) | `src/rollupContract/Rollup.sol` | 207-211 |
| `struct ExecutionEntry` (L1 shape) | `src/interfaces/IEEZ.sol` | 127 |
| `struct CrossChainCall` | `src/interfaces/IEEZL2.sol` | 32 |
| `struct ExecutionEntry` (L2 shape) | `src/interfaces/IEEZL2.sol` | 73 |

## Corrections made to `knowledge/sources.md`

- **Key-file map header**: stamped `verified 2026-09-16 against commit 03e87cddc05bf9c5fce97877498830c644f83192` (was `verified 2026-07-16`).
- **`IEEZ.sol` / `IEEZL2.sol` struct entry**: the map previously read "structs `CrossChainCall`, `ExecutionEntry`" as if both structs were shared across both files. Verified ground truth: `ExecutionEntry` is defined **separately in each file with different fields** (L1: `rollupUpdates`/`l2ToL1Calls`/`destinationRollupId`; L2: `incomingCalls`/`expectedOutgoingCalls`, no destination field — it's implicitly "this L2"). `CrossChainCall` is defined **only in `IEEZL2.sol`**; the L1-side counterpart is `L2ToL1Call`, a distinct type name. Reworded the map entry to state this explicitly so a future reader doesn't assume a single shared struct.

No file paths or exported symbol names moved. The rest of the map is accurate as written.
