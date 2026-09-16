# The EEZ Stack and What Is Actually Proven

Read this whenever content makes a claim about security, ZK proofs, decentralization,
or production-readiness. The gap between the architecture's intent and today's
deployment is the single easiest thing to get wrong in developer content.

## Contents

- [Repo map](#repo-map)
- [The node: three roles](#the-node-three-roles)
- [The trust model today](#the-trust-model-today)
- [Deployment reality](#deployment-reality)
- [How to phrase trust claims](#how-to-phrase-trust-claims)
- [Documentation trust hierarchy](#documentation-trust-hierarchy)

## Repo map

Organization: `github.com/eez-association`.

| Repo | Status | Role |
|---|---|---|
| `eez-core-protocol` | Active | Solidity contracts — `EEZ.sol` (L1), `EEZL2.sol` (L2). ~4k lines of Solidity plus e2e scripts, 8 version tags |
| `eez-rollup0` | Active | The node — ~52k lines of Rust across 12 crates. Targets Gnosis Chiado |
| `sync-rollups-poc` | **Archived Jun 2026** | The reth-based prototype both were rewritten from. Its `CLAUDE.md` "Lessons Learned" section is the most valuable document in the org |
| `stateless` | Fork | Paradigm's stateless Ethereum block validation — the re-execution backend |
| `zisk-eth-client`, `zisk-patch-stateless` | Pinned forks | Polygon's ZisK zkVM — the ZK endgame. `zisk-patch-stateless` is pinned to branch `zisk/ed189a5` |
| `solidity-simplified-transient-demo` | Small | Transient-storage experiment |

Note that `eez-rollup0` carries `eez-core-protocol` as a submodule, and previously a
`sync-rollups-protocol` submodule that isn't among the public repos.

## The node: three roles

`eez-rollup0`'s crates: `eez-composer`, `eez-driver`, `eez-deriver`, `eez-l1`,
`eez-node`, `eez-protocol`, `eez-proof-signer`, `eez-prover`, `eez-prover-client`,
`eez-payload-codec`, `eez-control-rpc`, `eez-evm-inspector`.

- **Sequencer** produces L2 blocks, driving a stock reth node. Ordinary blocks most of
  the time, plus one special **Sync block** per L1 block carrying the cross-chain work.
- **Composer** builds the execution tables and posts them to `EEZ` on L1. This is the
  component that does the off-chain precomputation the whole protocol depends on.
- **Deriver** rebuilds the entire L2 chain from L1 alone, reading `BatchPosted` events
  and re-running the transactions. A follower needs no trust in the sequencer.

### Two behaviors worth teaching

**Commit first, repair if needed.** The Sync block is added to L2 immediately; the L1
submission is watched in the background; if it doesn't land, the L2 block is rolled
back. L1 is the source of truth — L2 only keeps what L1 confirms. This is a real design
stance, not an implementation detail, and it's why the rewind/sibling-reorg machinery
exists.

**Cross-chain ingress fronts.** Two transparent RPC proxies — L1→L2 (inbound) and L2→L1
(outbound). `eth_sendRawTransaction` sent to a front is **held** and composed into the
next Sync block; every other `eth_*` forwards to that front's source-chain RPC.
Configured by `EEZ_L1_XCHAIN_PORT` / `EEZ_L2_XCHAIN_PORT` — **unset means that front is
disabled; there is no default port.** Interception happens at the RPC layer, so the node
itself stays stock. This is the integration point a builder actually touches.

## The trust model today

This is where content goes wrong most often, so be precise.

### What exists

`eez-proof-signer` is a validation and attestation daemon with its own SPEC.md. Per its
README, it "accepts one composer-streamed L2 block window, re-executes every block with
Stateless, binds the supported settlement effects and DA payload to that execution, and
signs the independently recomputed public-input hash." It is **single-flight and fails
closed** — any admission, validation, settlement, deadline, or signing failure returns
no signature.

So the current attestation is an ECDSA signature — but it is **not** a rubber stamp. The
signer independently re-executes the block window (via Paradigm's stateless validation)
and recomputes the public input itself. What the ECDSA stands in for is *succinctness*,
not verification.

On-chain, `IProofSystem` is satisfied by `ECDSAProofSystem.sol` (and
`MockECDSAProofSystem` in the node's contracts). The `EEZ` contract still enforces the
chain of state roots itself, which is why a non-succinct attestation is enough to test
liveness and consistency.

### What doesn't exist yet

Real ZK validity proofs. `eez-prover` and `eez-prover-client` are scaffolded but
essentially empty; the ZisK forks are the intended backend.

### Why the strategy is defensible

Build the whole pipeline — composition, posting, derivation, settlement, rewind — with
an honest-but-non-succinct attestation, so swapping in a real proof changes one
interface. The multi-prover design makes that swap a per-rollup configuration change
rather than a core-contract migration. That's a legitimately good engineering story and
worth telling *as* that story, rather than eliding the current state.

## Deployment reality

- **Supported L1: Gnosis Chiado** (testnet). Deployment configs also exist for
  `gnosis-100`, `kurtosis-1337`, and an `ethereum-1` placeholder.
- The Chiado setup runs an **embedded** L1 node plus a lighthouse consensus client — no
  separate L1 node. Protocol deploy must run *before* `up`, because it writes
  `deployments.env` and the L2 `genesis.json` whose timestamp is pinned to the deploy
  block.
- Both active repos state: **early-stage, not audited, interfaces and storage layout
  still in flux.**
- Recent commit activity is unglamorous liveness work — bounded post-batches, prover
  error retryability classification, closing an L1 watcher startup scan gap, unconsumed
  outbound transactions re-appended without their system loads. That pattern suggests
  something actually running, which is a fair thing to say and better evidence than a
  claim of maturity.

### Test surface

- `eez-core-protocol`: `forge test`; e2e scenarios under
  `script/e2e/<category>/<direction>/<scenario>/` with categories `one_way`,
  `multi_call`, `multi_tx`, `nested`, `reentrant`, `revert`. Local mode runs everything
  on anvil with the test playing sequencer; network mode drives a live devnet through
  the ingress fronts.
- `eez-rollup0`: `cargo test --workspace`; `scripts/xchain-test.sh` drives both
  directions × all op types × direct and wrapper paths, with matrix and load modes.

## How to phrase trust claims

Concrete substitutions to suggest when reviewing:

| Instead of | Write |
|---|---|
| "verified by ZK proofs" | "verified by a configurable proof system — today an attestation from a daemon that independently re-executes the block window, with ZK proving in development" |
| "trustless" | "re-derivable: any follower can rebuild the L2 chain from L1 data alone" (this part is real) |
| "atomic L1↔L2 calls" | "atomic within a single L1 block, given a builder that includes the bundle" |
| "production ready" | Don't. Say "testnet on Chiado, unaudited, interfaces in flux." |
| "decentralized sequencing" | The sequencer is a single builder today; derivation is the decentralization property, not sequencing |

The honest version is more interesting than the inflated one, and it's the version a
builder can act on.

## Documentation trust hierarchy

When sources disagree, believe them in this order:

1. **Source code** — `src/interfaces/IEEZ.sol`, `IEEZL2.sol`, `src/EEZ.sol`,
   `src/L2/EEZL2.sol`, `src/base/EEZBase.sol`
2. **`docs/CORE_PROTOCOL_SPEC.md`** — current and normative, ~1400 lines
3. **`docs/CAVEATS.md`**, `MULTI_PROVER_SPEC.md`, `EXECUTION_ENTRY_SPEC.md`,
   `STATIC_ENTRY.md`
4. **READMEs** — mostly current, but `eez-core-protocol`'s still links a
   `docs/LOOKUP_SPEC.md` that no longer exists
5. **`CLAUDE.md` files** — **stale in `eez-core-protocol`.** Describes the pre-refactor
   design with obsolete type names. Useful only as a record of what changed
6. **`sync-rollups-poc`** — archived, and its protocol details are superseded. But its
   "Lessons Learned — Hard-Won Rules" section is still the best operational document in
   the org

The drift is instructive in itself: where the team's documented review pipeline ran
(`core-worker → auditor → test-writer → qa → spec-writer → maintainer`), the spec stayed
precise. Where it didn't, the AI-facing context file rotted. Worth mentioning if content
touches their development process.
