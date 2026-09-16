# EEZ Architecture and API Surface

Current as of the `feature/simplify` refactor. Verify against
`eez-core-protocol/src/interfaces/IEEZ.sol`, `IEEZL2.sol`, and
`docs/CORE_PROTOCOL_SPEC.md` §A–§B before quoting signatures in published content.

## Contents

- [Contract map](#contract-map)
- [The L1/L2 naming split](#the-l1l2-naming-split)
- [L1 structs](#l1-structs)
- [L2 structs](#l2-structs)
- [Entry points](#entry-points)
- [The call hash](#the-call-hash)
- [Proxy derivation](#proxy-derivation)
- [Multi-prover model](#multi-prover-model)
- [Access control](#access-control)

## Contract map

| Path | Role |
|---|---|
| `src/EEZ.sol` (~1540 lines) | L1 central registry: state roots, ether balances, per-rollup queues, `postAndVerifyBatch`, execution |
| `src/L2/EEZL2.sol` (~720) | L2 manager: no proofs, no registry; system-loaded tables |
| `src/base/EEZBase.sol` (~350) | Shared: rolling-hash machinery, proxy registry, `computeCrossChainCallHash`, `ContextResult` transport |
| `src/base/CrossChainProxy.sol` (~115) | CREATE2 proxy per (address, rollupId) |
| `src/base/ExpectedL1ToL2CallTransient.sol` (~193) | Standalone transient-storage experiment — **not imported by any deployed contract**. Don't present it as live. |
| `src/rollupContract/Rollup.sol` (~220) | Reference per-rollup manager: owner, threshold, vkeys, `getCustomData` |
| `src/interfaces/IRollup.sol` | Declares `IRollupContract` — the callback interface the registry uses |
| `src/interfaces/IProofSystem.sol` | `verify(bytes proof, bytes32 publicInputsHash) → bool` |
| `src/interfaces/IMetaCrossChainReceiver.sol` | Hook fired on the batch sender to drive the transient stream |
| `src/proofSystems/ECDSAProofSystem.sol` | Development proof system |
| `src/periphery/Bridge.sol`, `WrappedToken.sol` | ETH/token bridging |
| `src/periphery/defiMock/` | `FlashLoan.sol`, `FlashLoanBridgeExecutor.sol`, `FlashLoanersNFT.sol` — the canonical synchronous-composability demo target |

Deleted in the refactor: `IZKVerifier.sol` (→ `IProofSystem.sol`) and
`ProofSystemRegistry.sol` (no central registry; each rollup's manager owns its allowed
set, and vetting is the rollup owner's responsibility).

## The L1/L2 naming split

Deliberate and worth explaining rather than glossing:

- **L1 (`IEEZ.sol`) uses absolute direction.** An `L2ToL1Call` executes *on* L1; an
  `ExpectedL1ToL2Call` is a reentrant call *leaving* L1.
- **L2 (`IEEZL2.sol`) uses self-relative direction.** `CrossChainCall` / `incomingCalls`
  and `ExpectedOutgoingCrossChainCall` / `expectedOutgoingCalls` — because an L2's
  counterparty may be L1 *or another L2*, so absolute names would often be wrong.
- **The rolling-hash frame vocabulary is direction-neutral** (`CALL_*`, `NESTED_*`) —
  a protocol constant across both chains.

L2 structs are leaner: no `StateUpdate`, no `destinationRollupId`, no
`ExpectedStateRootPerRollup`.

## L1 structs

```solidity
struct StateUpdate {
    uint64  rollupId;
    bytes32 currentState;   // expected pre-state, checked against rollups[rid].stateRoot
    bytes32 newState;
    int256  etherDelta;
}

struct L2ToL1Call {
    uint16  revertNextNCalls;  // consecutive calls (this one included) to force-revert; 0 = none
    bool    isStatic;          // execute via STATICCALL (read-only, no value)
    uint64  gas;               // gas limit for the target call; 0 = forward all remaining
    address sourceAddress;
    uint64  sourceRollupId;
    address targetAddress;
    uint256 value;             // 0 when isStatic
    bytes   data;
}

struct ExpectedL1ToL2Call {
    bytes32      expectedL1toL2Hash;            // keccak256(crossChainCallHash, expectedRollingHash)
    L2ToL1Call[] l2ToL1Calls;                   // this frame's own sub-calls, run to completion
    bytes32      revertedOrStaticRollingHash;   // checked only for STATIC / REVERTED kinds
    bool         success;
    bytes        returnData;                    // revert payload when !success
}

struct ExecutionEntry {
    StateUpdate[]        stateUpdates;          // ≥1, enforced on-chain
    bytes32              proxyEntryHash;        // inbound call hash; bytes32(0) for L2 txs
    L2ToL1Call[]         l2ToL1Calls;
    ExpectedL1ToL2Call[] expectedL1ToL2Calls;
    bytes32              rollingHash;
    uint64               destinationRollupId;
    bool                 success;
    bytes                returnData;
}

struct StaticExecutionEntry {
    ExpectedStateRootPerRollup[] expectedStateRoots;  // part of the MATCH predicate (full scan)
    bytes32      proxyEntryHash;
    L2ToL1Call[] l2ToL1Calls;                         // read-only, no reentrant frames
    bytes32      rollingHash;                         // untagged schema
    uint64       destinationRollupId;
    bool         success;
    bytes        returnData;
}

struct RollupConfig      { address rollupContract; bytes32 stateRoot; uint256 etherBalance; }
struct RollupVerification{ uint64 lastVerifiedBlock; uint64 entryQueueIndex;
                           ExecutionEntry[] entryQueue; StaticExecutionEntry[] staticEntryQueue; }
struct ProxyInfo         { bool isProxy; address originalAddress; uint64 originalRollupId; }
```

### The batch struct

```solidity
struct ProofSystemBatchPerVerificationEntries {
    ExpectedStateRootPerRollup[] expectedStateRootPerRollup;  // optional composer assertions
    ExecutionEntry[]             entries;
    StaticExecutionEntry[]       staticEntries;
    uint256                      immediateEntryCount;         // UNPROVEN dispatch param
    uint256                      immediateStaticEntryCount;   // UNPROVEN dispatch param
    address[]                    proofSystems;                // strictly increasing, no address(0)
    RollupIdWithProofSystems[]   rollupIdsWithProofSystems;   // strictly increasing by rollupId
    uint256[]                    blobIndices;                 // EIP-4844 blobs consumed
    bytes                        callData;                    // hash folded into public input
    bytes[]                      proofs;                      // one per proofSystems entry
    uint64                       blockNumber;                 // 0 = none, uint64.max = latest
    bool                         bindMsgSenderInPublicInput;  // front-run protection
}
```

Two design decisions embedded here that are worth teaching:

- `immediateEntryCount` / `immediateStaticEntryCount` are **not folded into the public
  input**, so the immediate/persistent split can be retuned without re-proving.
  Semantics inside the commitment, scheduling hints outside it.
- `bindMsgSenderInPublicInput` folds `msg.sender` when true (only the submitter can
  land the batch) or `address(0)` when false (permissionless). Per-batch policy.

## L2 structs

Mirror the L1 shapes with self-relative names and no state machinery:

```solidity
struct CrossChainCall { /* identical field layout to L2ToL1Call */ }

struct ExpectedOutgoingCrossChainCall {
    bytes32            expectedOutgoingHash;          // keccak256(crossChainCallHash, expectedRollingHash)
    CrossChainCall[]   incomingCalls;
    bytes32            revertedOrStaticRollingHash;
    bool               success;
    bytes              returnData;
}

struct ExecutionEntry {
    bytes32                          proxyEntryHash;   // never bytes32(0) on L2
    CrossChainCall[]                 incomingCalls;
    ExpectedOutgoingCrossChainCall[] expectedOutgoingCalls;
    bytes32                          rollingHash;
    bool                             success;
    bytes                            returnData;
}

struct StaticExecutionEntry {
    bytes32          proxyEntryHash;
    CrossChainCall[] incomingCalls;
    bytes32          rollingHash;
    bool             success;
    bytes            returnData;
}
```

## Entry points

### L1 (`EEZ.sol`)

| Function | Notes |
|---|---|
| `registerRollup(address rollupContract, bytes32 initialState) → uint64` | Caller pre-deploys an `IRollupContract` manager, then registers. Fires `rollupContractRegistered(rid)` once. |
| `postAndVerifyBatch(batch)` | Validates sorted invariants, fetches vkeys per rollup, verifies one proof per proof system (atomic — any failure reverts), wipes and republishes queues, runs the immediate prefix, fires the meta hook |
| `executeCrossChainCall(address sourceAddress, bytes callData)` | Proxies only. Top-level → consume from the routed queue; reentrant → `_consumeNestedCall` |
| `executeL2Txs(uint64 rollupId)` | Permissionless. Consumes entries with `proxyEntryHash == bytes32(0)` |
| `staticCrossChainCall(address sourceAddress, bytes callData)` | View. Proxies only, via STATICCALL |
| `setStateRoot(uint64 rid, bytes32 newRoot)` | Manager-only escape hatch; same-block lockout |
| Views | `lastVerifiedBlock(rid)`, `queueLength(rid)`, `executionQueueIndex(rid)` |

Internal names likely to appear in reviewed content: `_consumeAndExecuteEntry`,
`_findMatchingEntry`, `_consumeNestedCall`, `_resolveNestedReentrant`, `_executeEntry`,
`_processNCalls`, `_processNStaticCalls`, `executeInContextAndRevert`,
`_decodeContextResult`, `_applyStateUpdates`, `_attemptExecuteImmediateL2Txs`.

### L2 (`EEZL2.sol`)

Constructor takes `rollupId != 0`, a `systemAddress`, and the immutable `USE_GAS_LEFT`
flag. `SYSTEM_ADDRESS` is a trusted node-controlled address — no key, not
reentry-reachable.

| Function | Notes |
|---|---|
| `loadExecutionTable(entries, staticEntries)` | System-only. Wipes and reloads; entries consumable only in the same block |
| `executeIncomingCrossChainCall(...)` | System-only, payable (`msg.value == value` mints inbound ETH). Atomically replaces the table and drives `executions[0]`; `entries[0].proxyEntryHash` must match the explicit params (`EntryHashMismatch`) |
| `executeCrossChainCall` | Same shape as L1, but `sourceRollupId` is forced to `ROLLUP_ID` and any `msg.value` is forwarded to `SYSTEM_ADDRESS` (burn) |
| `staticCrossChainCall` | Scans the persistent static table |

### `CrossChainProxy.sol`

- `executeOnBehalf(address destination, uint64 callGas, bytes data) payable` — manager-driven outbound. **Uses assembly return: for void functions returnData is empty (0 bytes), not ABI-encoded empty bytes.** A recurring source of hash mismatches.
- `staticCheck()` — the `tstore` probe for static-context detection.
- `fallback()` — routes to `executeCrossChainCall` or `staticCrossChainCall`.

## The call hash

Single formula, used everywhere, `public pure` on `EEZBase`:

```solidity
computeCrossChainCallHash(
    bool isStatic, address sourceAddress, uint64 sourceRollupId,
    address targetAddress, uint64 targetRollupId,
    uint256 value, uint64 callGas, bytes data
) → keccak256(abi.encode(...))
```

Field order: `isStatic` → FROM pair → TO pair → `value` → `callGas` → `data`.

`isStatic` in the preimage is what makes a read-only call key distinctly from an
otherwise-identical state-changing one — no separate field needed.

### The `callGas` subtlety

`callGas` is `0` (`ZERO_CALL_GAS`) at every site **except** calls leaving an L2, where
it depends on the immutable `USE_GAS_LEFT`:

- `true` (intended production, pending node support): `uint64(gasleft())` observed when
  `executeCrossChainCall` starts. The prover must commit to the exact forwarded gas.
- `false` (current deployments and test fixtures): fixed at `0`, so outgoing hashes are
  gas-independent and pre-computable.

| Matching site | `callGas` folded |
|---|---|
| Everything on L1 | `0` |
| L2 inbound binding | `0` |
| L2 static matching | `0` |
| Calls leaving an L2 | `gasleft()` if `USE_GAS_LEFT`, else `0` |

Off-chain tooling mirrors this in `script/e2e/shared/E2EHelpers.sol`. Note that
`abi.encode` left-pads integers to 32 bytes, so uint256 rollupIds in tooling produce
identical bytes to the contract's uint64 fields.

## Proxy derivation

```
salt         = keccak256(abi.encodePacked(originalRollupId, originalAddress))
bytecodeHash = keccak256(creationCode ‖ abi.encode(manager, originalAddress, originalRollupId))
proxyAddress = address(uint160(uint256(keccak256(0xff ‖ manager ‖ salt ‖ bytecodeHash))))
```

`computeCrossChainProxyAddress(address originalAddress, uint64 originalRollupId)` takes
**two** parameters. There is no `domain` or `block.chainid` in the salt — so two proxies
on different managers for the same pair share an address only if the managers match.
Worth flagging as a deliberate choice anyone forking should understand.

`RECOVERY_ADDRESS()` receives ether swept from proxies (ether sent to a proxy address
before deployment). `SameNetworkProxy(rollupId)` rejects creating a proxy for the local
rollup.

## Multi-prover model

```
EEZ.sol (registry: roots, balances, queues, proxies — no per-rollup policy)
   ↑ checkProofSystemsAndGetVkeys / getCustomData / rollupContractRegistered
IRollupContract per rollup (owner, threshold, vkey map, add/removeProofSystem)
   ↑ verify(proof, publicInputsHash)
IProofSystem contracts (any verifier — ZK, ECDSA, …)
```

A batch carries a global strictly-increasing `proofSystems[]` and one `proofs[k]` per
entry. Each rollup selects its accepted subset via `proofSystemIndexes[]` (indices into
the global list); its manager validates the subset and returns per-PS vkeys, enforcing
its own threshold. Position lookup uses binary search (`_findIndexPosition`).

The public-inputs hash covers: every entry hash (`keccak256(abi.encode(entry))` over the
*full* struct), every static-entry hash, every selected blob hash, per-rollup
`customData` from `getCustomData(blockNumber)`, `keccak256(callData)`, `boundSender`,
and per-PS a rolling `(rollupId, vkey)` accumulator.

All proofs verify atomically — a single failure reverts the batch. Notably, the three
external calls during verification (`checkProofSystemsAndGetVkeys`, `getCustomData`,
`IProofSystem.verify`) are made inside STATICCALL frames, so a malicious manager or
verifier cannot mutate state mid-verification.

## Access control

| Function | Who |
|---|---|
| `registerRollup` | Anyone |
| `postAndVerifyBatch` | Anyone (proofs authorize; `bindMsgSenderInPublicInput` can pin the submitter) |
| `executeCrossChainCall` (L1/L2) | Registered proxies only |
| `executeL2Txs` | Anyone, must not be inside execution |
| `staticCrossChainCall` | Registered proxies only |
| `executeInContextAndRevert` | Self-call only |
| `_attemptExecuteImmediateL2Txs` | Self-call only (`public`, guarded) |
| `createCrossChainProxy` | Anyone (subject to `SameNetworkProxy`) |
| `setStateRoot` | Current `rollups[rid].rollupContract`, with lockouts |
| `loadExecutionTable`, `executeIncomingCrossChainCall` (L2) | `SYSTEM_ADDRESS` |

Per-rollup ownership ops (`addProofSystem`, `removeProofSystem`,
`updateVerificationKey`, `setThreshold`, `transferOwnership`) live on the rollup's own
manager, not the registry.
