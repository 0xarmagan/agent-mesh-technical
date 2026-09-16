# EEZ Execution Model

Normative source: `eez-core-protocol/docs/CORE_PROTOCOL_SPEC.md` (§D Execution Model,
§E Rolling Hash, §F Static Entry Resolution, §H Invariants). Names below match the
current source, post-`feature/simplify`.

## Contents

- [The core inversion](#the-core-inversion)
- [Entry encoding rule](#entry-encoding-rule)
- [The rolling hash](#the-rolling-hash)
- [The unified reentrant table](#the-unified-reentrant-table)
- [Static entries](#static-entries)
- [revertNextNCalls](#revertnextncalls)
- [Consumption and matching](#consumption-and-matching)
- [Lifecycle and same-block rule](#lifecycle-and-same-block-rule)
- [Invariants worth citing](#invariants-worth-citing)

## The core inversion

State transitions are computed off-chain by the composer, attested by proof systems,
and *verified* on-chain. The manager contract never discovers what a cross-chain call
returns — it checks that what happened matches what was proven.

Everything else in this document is machinery serving that inversion.

## Entry encoding rule

From `script/e2e/README.md`, and the single most useful heuristic for reviewing demos:

> Each top-level cross-chain call is one entry on the source chain and one system
> delivery on the destination; calls made *inside* an entry's execution belong to that
> entry.

So a flash loan spanning L1 and L2 is not N entries per hop — the nested calls live
inside their host entry's frames. Miscounting here surfaces as `ExecutionNotFound`
(L1) or `EntryNotFound` (L2), and it's the most common demo bug.

## The rolling hash

One `bytes32` per entry is the primary integrity guarantee. Tag constants live on
`EEZBase` and are protocol constants shared by both chains:

```
CALL_BEGIN     = 1   hash = keccak(hash ‖ 1 ‖ crossChainCallHash)
CALL_END       = 2   hash = keccak(hash ‖ 2 ‖ success ‖ retData)
NESTED_BEGIN   = 3   hash = keccak(hash ‖ 3 ‖ crossChainCallHash)
NESTED_END     = 4   hash = keccak(hash ‖ 4)
CALL_NOT_FOUND = 5   hash = keccak(hash ‖ 5 ‖ crossChainCallHash)
```

Fold helpers: `_rollingHashEntryBegin`, `_rollingHashCallBegin`, `_rollingHashCallEnd`,
`_rollingHashNestedBegin`, `_rollingHashNestedEnd`, `_rollingHashCallNotFound`.

### Seeding matters

The accumulator is not zero at entry start — it must *be* zero beforehand (else
`RollingHashNotCleared`) and is then seeded:

```
// L1 (_rollingHashEntryBegin): ordered (rollupId, currentState) context, closed with identity
seed = keccak(…keccak(0 ‖ rollupId₁ ‖ currentState₁)… ‖ rollupIdₙ ‖ currentStateₙ)
hash = keccak(seed ‖ proxyEntryHash)

// L2 (_seedRollingHash): same shape, empty state prefix
hash = keccak(0 ‖ proxyEntryHash)
```

So the hash binds **starting state plus entry identity**, not merely call results.
Nested frames inherit this transitively. Content that describes the rolling hash as
"a hash of the return values" is materially understating it.

### Three details worth teaching

- **No call index is folded in.** The hash is a chain, so order, count, and nesting are
  already bound. The omission is load-bearing: it's what lets a `revertNextNCalls` span
  be processed as a 0-based sub-slice without diverging from a continuous run.
- **`CALL_NOT_FOUND` exists to prevent forgery.** A reentrant call with no matching
  table row folds tag 5, deliberately distinct from `CALL_END(true, "")`. Otherwise a
  no-match could be laundered as a normal empty return. A prover that pre-hashes tag 5
  has *committed* to a not-found at that position — a faithful outcome, not an attack.
- **Two schemas, not one.** Entry-level is tagged. Static resolution uses an untagged
  `keccak(prev, success, retData)` chain via `_processNStaticCalls`, safe because the
  surrounding key already pins the context tags would disambiguate. `_processNStaticCalls`
  returns a local hash and never touches `_rollingHash` — no cross-contamination.

Final check: `require(_rollingHash == entry.rollingHash)` → `RollingHashMismatch`.
This catches wrong return data, wrong success flag, missing or extra calls, a skipped
or extra nested frame, reordered operations, and unexpected reentrancy.

## The unified reentrant table

Post-refactor there is **one** table for every kind of reentrant call — plain success,
read-only static, and try/catch'd revert. Each row is content-addressed by:

```
expectedL1toL2Hash = keccak256(crossChainCallHash, expectedRollingHash)
```

L2 mirror: `ExpectedOutgoingCrossChainCall.expectedOutgoingHash`, identical formula.

`expectedRollingHash` is `_rollingHash` at the instant the call fires. Because the hash
already chains everything prior, it uniquely pins the execution point — this is what
replaced the old 4-tuple key. **The integrity primitive doubles as the addressing
primitive.** Flag this whenever explaining the design; it's the sharpest idea here.

Also folded into `crossChainCallHash` so they need no field of their own: `isStatic`
(a read keys distinctly from an otherwise-identical write) and the routed rollup.

Resolution by kind:

| Kind | Key | Behavior |
|---|---|---|
| SUCCESS | call key, `success = true` | `_resolveNestedReentrant` runs the sub-array as a committing sub-execution, folding into the host's continuous hash between `NESTED_BEGIN`/`NESTED_END` |
| STATIC | static key | `staticCrossChainCall` runs the sub-array via STATICCALL, untagged hash vs `revertedOrStaticRollingHash`, returns `returnData` (reverts with it if `!success`) |
| REVERTED | call key, `success = false` | `_resolveNestedReentrant` runs the sub-array as a mini-entry (tagged hash) then reverts; the frame's state effects roll back with it |

Each row carries its **own** `l2ToL1Calls[]` / `incomingCalls[]` sub-array, run to
completion. There is no shared partition and no global cursor across the tree. A
reverted sub-execution reuses the host table for its own reentrant calls, since
Solidity forbids recursive structs.

## Static entries

Top-level read-only cross-chain calls resolve from a pool, outside any execution:
`StaticExecutionEntry` in `_transientStaticEntries` or the per-rollup
`staticEntryQueue`.

Match predicate (full scan, not cursor-based): `proxyEntryHash` +
`destinationRollupId` + every `expectedStateRoots` pin equal to the live root.
Referenced proxies must already be deployed (`StaticCallProxyNotDeployed`).

No reentrant table — a reentrant read re-enters the pool as *another*
`StaticExecutionEntry`. No proxy creation, no `revertNextNCalls`, no nesting; STATICCALL
forbids state writes.

### How static context is detected

`tstore` reverts in static context; `tload` does not. The proxy's `_fallback`
self-calls `staticCheck()`, which attempts a `tstore`. If the self-call reverts, the
proxy is in static context and routes to `staticCrossChainCall`.

This is sound because a self-call from inside a STATICCALL is itself a STATICCALL — a
proxy cannot escalate. There is no way to fake a non-static context from inside one.
Transient storage used as a capability probe, not scratch space.

## revertNextNCalls

`uint16 revertNextNCalls` on `L2ToL1Call` / `CrossChainCall`. Value N > 0 means: the
next N calls (this one included) execute, succeed, and have their EVM state effects
rolled back at the protocol layer.

Mechanism: the processor self-calls `executeInContextAndRevert(calls)`, which *always*
reverts with `ContextResult(rollingHash, reentrantConsumed, callsProcessed)`. State
rolls back; the cursors and hash escape via the revert payload and are re-applied by
the outer frame after `_decodeContextResult`.

Why this works, per §E.1:

- `tload` is read-only, so it functions inside a frame that's about to revert — the
  inner self-call observes the outer accumulator and cursors when it starts.
- `tstore` writes are journaled and rolled back with the frame. So hash updates, cursor
  advances, and `_entryEtherDelta` subtractions all vanish — except what escapes via
  the revert payload.

Inside the span, calls fold `CALL_BEGIN`/`CALL_END` exactly as if normal, including
failed ones. **The proof's `rollingHash` must commit to the calls regardless of whether
their state effects survived.**

**Correct use:** a call that ran cleanly on the destination but must be rolled back in
the source's view.
**Incorrect use:** a call that naturally reverts. Use `revertNextNCalls = 0` — the
proxy's `.call` already captures `(false, retData)` into `CALL_END`. This misuse
frequently still passes a happy-path test, which is exactly why it's worth flagging.

Bounds violation: `RevertSpanOutOfBounds(start, span, length)`.

## Consumption and matching

`_consumeAndExecuteEntry` / `_findMatchingEntry` **forward-scan** the queue for the
first entry matching identity (`proxyEntryHash`), routing (`destinationRollupId`), and
state preconditions (every `StateUpdate.currentState` equal to the live root).

Two consequences with opposite ergonomics:

- **Match-time failure is forgiving.** Non-matching candidates are skipped and never
  execute. So alternative entries gated on different `currentState` values can be
  *stacked* in the queue — only the one matching the live root applies. If none match:
  `ExecutionNotFound`.
- **Execution-time failure is sticky.** An entry that matches and *then* reverts
  (`RollingHashMismatch`, `EtherDeltaMismatch`, …) reverts the whole consuming
  transaction **without advancing the cursor**. A retry re-matches the same entry.

The immediate L2Tx prefix is the exception: `_attemptExecuteImmediateL2Txs` wraps each
leading L2Tx entry in try/catch, emitting `L2TxSkipped` and continuing — but a
non-empty run where *every* entry reverts unwinds the whole post with
`AllImmediateL2TxsFailed`.

## Lifecycle and same-block rule

`verificationByRollup[rid]` holds `{lastVerifiedBlock, entryQueueIndex, entryQueue,
staticEntryQueue}`. `lastVerifiedBlock` does three jobs:

1. **Reset marker.** Every batch touching `rid` wipes that rollup's queues and cursor
   first, so a same-block re-verify **replaces** the prior batch rather than appending.
   Safe because consumption re-checks `currentState`.
2. **Read gate.** Consumers require `lastVerifiedBlock == block.number`. Queues never
   leak across blocks (`ExecutionNotInCurrentBlock`).
3. **`setStateRoot` lockout.** Reverts `RollupBatchActiveThisBlock` while equal to the
   current block.

Multiple top-level `postAndVerifyBatch` calls hitting the same rollup in one block are
permitted *by design* — the second supersedes the first. Builders cannot rely on
once-per-block exclusivity; if they need it, it's enforced socially, not on-chain.

## Invariants worth citing

From §H, in the order they matter to a builder:

- **State root consistency (H.1).** Every entry carries ≥1 `StateUpdate`, enforced
  on-chain (`EntryHasNoStateUpdates`), strictly increasing by rollupId
  (`StateUpdatesNotStrictlyIncreasing`). `currentState` must equal the live root
  (`StateRootMismatch`).
- **Ether accounting (H.2).** Signed `etherDelta` per rollup must balance
  (`EtherDeltaMismatch`, `ResidualEntryEtherIn`, `InsufficientRollupBalance`).
- **Rolling hash integrity (H.4).** No path exists where execution diverges from the
  proof and still completes successfully.
- **Proxy determinism (H.5).** One proxy per `(originalAddress, originalRollupId)`,
  CREATE2-derived.
- **Wipe on every verify (H.7)** and **same-block execution (H.6)** — see above.
- **Reentry guard (H.9).** `postAndVerifyBatch` re-entry from anywhere is blocked by
  `PostBatchReentry` via `_insideExecution() || _transientEntries.length != 0`.
