# EEZ Footguns, Errors, and Hard-Won Rules

Read before signing off on any demo or published claim. Sources:
`eez-core-protocol/docs/CAVEATS.md`, the error definitions in `src/EEZ.sol` /
`src/L2/EEZL2.sol` / `src/base/EEZBase.sol`, and the "Lessons Learned — Hard-Won Rules"
section of the archived `sync-rollups-poc/CLAUDE.md`.

## Contents

- [Protocol-level footguns](#protocol-level-footguns)
- [Demo-authoring footguns](#demo-authoring-footguns)
- [Error catalogue](#error-catalogue)
- [Operational rules from production incidents](#operational-rules-from-production-incidents)
- [Claims to challenge in content](#claims-to-challenge-in-content)

## Protocol-level footguns

These come from `CAVEATS.md` — 13 lines, all load-bearing. If a demo or explainer
contradicts one of these, it's a blocking issue.

### Opcodes lie on cross-chain proxies

The single sharpest builder footgun in the system.

- `delegatecall`, `balance`, `extcodesize`, `extcodecopy` return information about **the
  proxy itself**, not the proxied contract.
- Block-state opcodes (`blocknumber`, `blockhash`, `blockgaslimit`, `chainid`,
  `coinbase`, …) reflect **the chain the call is executing on**, not the source chain.
  So the same logical action observes different values on L1 vs L2.

Any demo whose contract logic branches on these, or whose narrative implies cross-chain
consistency of block context, is teaching a bug.

### Revert reasons are indistinguishable

A caller — contract or EOA — cannot tell whether a proxy call reverted because the
execution table had no matching entry, or because the destination call itself reverted.
Both bubble up identically. Demos that appear to distinguish them are fiction, and
error-handling code copied from them will mislead.

### Match-time skips, execution-time blocks

Consumption forward-scans and **skips** non-matching candidates — so alternative
entries gated on different `currentState` values can be stacked in the persistent
queues, and only the one matching the live root applies. If none matches:
`ExecutionNotFound`.

But an entry that matches and *then* reverts mid-execution reverts the whole consuming
transaction **without advancing the cursor** — a retry re-matches the same entry. Ergo:
speculative alternatives are a supported pattern; post-match failure is sticky.

### The transient phase is self-contained

While a `postAndVerifyBatch` is mid-flight (the meta-hook window), **all** resolution is
served exclusively from that batch's own transient tables — both execution entries and
top-level static reads. `staticCrossChainCall` never falls through to the persistent
queues during the hook.

Consequence, and the most under-communicated limitation in the protocol: **cross-rollup
interaction inside the meta hook only works between rollups verified together in the
same batch.** A rollup verified by an earlier batch in the same block passes the block
gate but misses with `ExecutionNotFound`. Anything else must wait for the batch to
finish, or be re-verified jointly.

### The untrusted meta hook

`postAndVerifyBatch` calls
`IMetaCrossChainReceiver(msg.sender).executeMetaCrossChainTransactions()` when non-L2Tx
immediate entries remain and `msg.sender` has code. The hook may revert, consume some
entries, ignore the call, or try to re-enter. Defenses: re-entry blocked by
`PostBatchReentry`; partial consumption is fine because the persistent remainder is
published anyway and `currentState` is the backstop; a hook revert reverts the entire
batch atomically, and the next caller can retry cleanly.

### Same-block replacement, not exclusivity

Multiple `postAndVerifyBatch` calls hitting the same rollup in one block are permitted;
the later one wipes and supersedes the earlier. Content that promises once-per-block
exclusivity is wrong — it's a social-layer guarantee if it exists at all.

## Demo-authoring footguns

### `revertNextNCalls` for natural reverts

The most common conceptual error. `revertNextNCalls > 0` is for calls that *succeeded*
and must be force-rolled-back. A naturally-reverting call needs `revertNextNCalls = 0` —
the proxy's `.call` already captures `(false, retData)` into `CALL_END`. The misuse
often still passes a happy-path test, so it survives casual review.

### Void returns are empty, not ABI-encoded empty

`executeOnBehalf` uses an assembly return. For a void function, returnData is **0
bytes**, not 64 bytes of ABI-encoded emptiness. Getting this wrong changes the
`CALL_END` fold and produces a `RollingHashMismatch` that looks like a protocol bug.

### Miscounted entries

The encoding rule: one entry per top-level cross-chain call on the source chain, one
system delivery on the destination; calls made *inside* an entry's execution belong to
that entry. Miscounting yields `ExecutionNotFound` / `EntryNotFound`.

### Silently playing sequencer

Local-mode e2e tests have the test itself act as sequencer and post batches. That's
correct for a test and misleading in a tutorial — readers conclude building execution
tables is their job. In production the composer does it. Say which mode the demo is in.

### CREATE2 bytecode determinism is a build problem

From the POC's rules, and it bites hard:

- Two `out/` directories can produce **different bytecode for the same contract** from
  separate `forge build` invocations with different metadata. Mixing sources breaks
  CREATE2 addresses.
- Host and Docker forge versions differ — bytecodes will differ. Compile in one place.
- `forge inspect` ≠ `forge build` output. Read JSON artifacts for CREATE2 computation.

Demos that compute proxy addresses locally and compare against a devnet need to say
where the bytecode came from.

### Stale state between runs

Fresh deploy (`down -v`) when changing anything affecting L1 entries or batch format.
Stale L1 state blocks recovery on restart and produces confusing failures.

## Error catalogue

Useful for interpreting a failing demo. Grouped by what actually went wrong.

**Table/matching failures — usually a builder or encoding bug**
`ExecutionNotFound`, `EntryNotFound(crossChainCallHash, callGas)`,
`NoExpectedL1ToL2CallFound`, `EntryHashMismatch`, `EmptyEntries`,
`ExecutionNotInCurrentBlock(rollupId)`

**Integrity failures — execution diverged from the proof**
`RollingHashMismatch`, `RollingHashNotCleared`, `UnconsumedL2ToL1Calls`,
`RevertSpanOutOfBounds(start, span, length)`, `UnexpectedContextRevert(revertData)`

**State/value failures**
`StateRootMismatch(rollupId)`, `ExpectedStateRootMismatch(rollupId)`,
`EtherDeltaMismatch`, `ResidualEntryEtherIn`, `InsufficientRollupBalance`,
`EtherTransferFailed`, `ValueMismatch`

**Batch validation failures — malformed batch**
`InvalidProof`, `InvalidProofSystemConfig`, `DuplicateProofSystem(ps)`,
`RollupNotInBatch(rollupId)`, `EntryHasNoStateUpdates`,
`StateUpdatesNotStrictlyIncreasing(rollupId)`,
`ExpectedStateRootsNotStrictlyIncreasing(rollupId)`,
`ImmediateCountExceedsEntries`, `ImmediateStaticEntryCountExceedsStaticEntries`,
`ImmediateStaticEntriesWithoutImmediateEntries`, `ImmediateCountStrandsLeadingL2Tx`,
`AllImmediateL2TxsFailed`

**Authorization / lifecycle**
`UnauthorizedProxy`, `Unauthorized`, `NotSelf`, `PostBatchReentry`,
`NotRollupContract`, `InvalidRollupContract`, `InvalidRollupId`,
`RollupBatchActiveThisBlock(rollupId)`, `SetStateRootNotAllowedDuringExecution`,
`L2TXNotAllowedDuringExecution`, `SameNetworkProxy(rollupId)`,
`InvalidRecoveryAddress`

**Proxy-authority failures — a batch tried to drive a rollup it didn't prove**
`CallSourceNotVerified(rollupId)`, `ReentrantDestinationNotVerified(rollupId)`,
`EntryDestinationNotInStateUpdates(rollupId)`,
`StaticEntryDestinationNotPinned(rollupId)`

**Static-path failures**
`StaticCallProxyNotDeployed(sourceProxy)`, `StaticCallWithValue`, `NonStaticSubCall`

**Not an error — a transport**
`ContextResult(rollingHash, reentrantConsumed, callsProcessed)` is the deliberate revert
payload from `executeInContextAndRevert`. Seeing it in a trace is normal.

## Operational rules from production incidents

From the archived POC. Worth citing in content about running a node, and worth
respecting in any tooling a demo ships.

### The dev-key incident (2026-04-15)

A testnet wedged at L2 block 5354 for 30+ minutes. External use of the public reth dev
key (mnemonic `test test test … junk`) submitted transactions at the same nonce the
builder expected, and replace-by-fee with a 50,000,000× gas overbid evicted the
builder's `postBatch` from the L1 mempool. The receipt timed out after 15 attempts —
and the real bug was that the timeout path left the hold armed, so since the hold check
runs *before* the flush, no retry could ever fire. The chain could not self-recover.

Rules that came out of it:

- **Never use a well-known dev key as a builder, composer, or poster key.** Flag this in
  any demo, tutorial, or compose file. Deploy scripts should reject it outright.
- **Set the hold BEFORE submitting, not after.** Set after, and a failure leaves an
  unclearable hold. Set before, and failure triggers the rewind that clears it. Failure-
  path reachability is determined by statement order.
- **Always reset the nonce after any L1 tx failure**, including the receipt-timeout
  path. Otherwise: permanent livelock — the builder keeps building and never submits.
- **"Nonce gap = invisible death."** Submissions sit in the queued pool while block
  production continues. Diagnose with `cast rpc txpool_inspect`.

### Never fabricate state roots

> "NEVER align state roots by overwriting pre_state_root — NO EXCEPTIONS."

A mismatch means a real derivation or filtering bug. Fabricating roots produces blocks
fullnodes cannot reproduce. The rule against the tempting local fix — and the right
instinct to model in content.

### Engine API can't rewind

`engine_forkchoiceUpdatedV3(head=ancestor)` is a **silent no-op** by Engine API spec on
Ethereum engine kinds. Use sibling reorg: `newPayloadV3(N')` then
`forkchoiceUpdatedV3(head=N'.hash)`. Guard at 48 blocks — 75% of reth's 64-block
changeset retention — and halt production loudly before the eviction window closes.
Never commit a sibling without asserting its state root matches the expected root first.

### Bundle size is empirical

`postBatch` and the user's L1 txs must land in the same L1 block for atomicity.
rbuilder-chiado **silently drops** bundle contents past roughly 3 transactions, which is
lost inclusion, not a visible error. `EEZ_MAX_USER_TXS_PER_BUNDLE` defaults to 3 for
this reason. Raise only against a builder measured to include larger bundles atomically.

### Protocol-first, not pattern-first

> "NEVER implement a fix for just the specific pattern that broke."

Read the spec, implement the general mechanism, and use protocol identity primitives
(the proxy registry, `computeCrossChainProxyAddress`) rather than trace heuristics —
trace parsing is fragile and breaks with wrapper contracts. Most of the other debugging
rules are downstream of having violated this once.

## Claims to challenge in content

When reviewing a draft, these specific claims should trigger scrutiny:

| Claim | The correction |
|---|---|
| "Atomic cross-chain execution" | True *given a cooperating builder*. `postBatch` and user txs must land in one L1 block; bundle limits are real. Say so. |
| "Verified by ZK proofs" | Not in current deployments. See `stack-and-trust.md`. |
| "Full cross-rollup composability" | Inside the meta hook, only between rollups verified in the same batch. |
| "Audited" / production-ready | Both active repos say early-stage, unaudited, interfaces and storage layout in flux. |
| "Your contracts work unchanged" | Mostly — but the proxy opcode caveats and block-context differences are real behavioral changes. |
| "You can retry a failed entry" | Match-time misses skip; post-match failures re-match the same entry. Not a general retry. |
| "Entries queue up for later" | No. `lastVerifiedBlock == block.number` or nothing. |
| Any struct or function name from the stale list | Check it against `src/interfaces/`. |
