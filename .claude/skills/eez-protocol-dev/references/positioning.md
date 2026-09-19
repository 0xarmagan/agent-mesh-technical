# Positioning EEZ Honestly

For content aimed at developers deciding whether to build here. The goal is a builder
who can tell whether EEZ fits their problem — not a builder who is impressed. An honest
comparison that says "don't use this for X" is more persuasive to an engineer than an
unqualified pitch, and it's the only version that survives contact with a skeptic.

## Contents

- [The one-sentence claim](#the-one-sentence-claim)
- [What actually differs](#what-actually-differs)
- [The comparison table](#the-comparison-table)
- [When not to use EEZ](#when-not-to-use-eez)
- [Arguments that don't hold up](#arguments-that-dont-hold-up)
- [Phrasebook](#phrasebook)

## The one-sentence claim

> A contract on one chain can call a contract on another and use the return value in
> the same transaction.

That's the whole differentiator. Everything else — rolling hashes, execution tables,
multi-prover verification — is machinery serving it. Lead with the capability, not the
machinery, because the capability is what a builder evaluates.

The honest qualifier, which belongs in the same breath for any claim of atomicity:
within a single L1 block, and contingent on a builder including the bundle.

## What actually differs

Most cross-chain approaches are **asynchronous**: you send a message, it lands later,
and you write your contract as a state machine with a pending state. This isn't a
latency inconvenience — it's a *programming model* constraint. Certain things become
impossible rather than slow:

- A cross-chain call inside a loop or conditional that depends on its result
- Borrowing on chain A, using the funds on chain B, and repaying on A atomically —
  because the repayment must be provably part of the same transaction or the loan is
  unsecured
- Reading a price or balance on another chain and branching on it in the same call
- Any composition where partial completion is not a valid state

The synchronous model's actual gift is that **you can't end up half-done.** Async
messaging forces every integration to answer "what if the second leg never lands," and
most bugs in cross-chain applications live in that answer.

The cost, stated plainly: outcomes must be precomputed off-chain and proven, so someone
has to run a composer that can see both chains, and everything must fit in one L1 block.

## The comparison table

Categories rather than named products, because the mechanism is what determines fit and
product details change faster than content does.

| Approach | Composability | Trust added | Real constraint |
|---|---|---|---|
| **Native L1↔L2 bridge** | Async, slow (proving/challenge delay) | None beyond the rollup itself | Withdrawal latency measured in hours to days; no return values |
| **General message passing** | Async, minutes | An external verifier set or oracle | You inherit that set's security; no same-tx return value |
| **Intent / solver networks** | Effectively sync *for the user* | Solver capital and liveness | The solver takes the risk and prices it; not general contract composability — a solver fills an intent, it doesn't let your contract call another chain |
| **Shared sequencing / atomic inclusion** | Atomic *inclusion*, not atomic *execution* | The shared sequencer | Both txs land together, but neither can use the other's return value — this is the distinction most content blurs |
| **EEZ (synchronous composability via realtime proving)** | Synchronous, same transaction, return values usable | Proof system(s) the rollup chooses; a composer for liveness | One L1 block; builder must include the bundle; precomputation required |

The row worth spending a paragraph on in any comparative piece is shared sequencing.
Atomic inclusion and atomic execution sound alike and are not: inclusion guarantees both
transactions appear, which is enough for some arbitrage and insufficient for anything
where one leg's logic depends on the other's result. EEZ's claim is the stronger one, and
the comparison is only credible if it names the weaker one accurately.

## When not to use EEZ

Include this. A developer-facing comparison without it reads as marketing and gets
discounted wholesale.

- **You don't need return values.** If a fire-and-forget message works, async messaging
  is simpler, has no composer dependency, and is battle-tested. Don't take on this
  machinery for a notification.
- **You need to span chains that aren't in the same batch.** Cross-rollup interaction
  inside the meta hook only works between rollups verified together in one batch. This
  is a real ceiling today.
- **You need mainnet, audited, today.** Both active repos state early-stage, unaudited,
  interfaces and storage layout in flux. Chiado testnet.
- **You need to span ecosystems.** This is for based rollups sharing an L1 sequencing
  context, not a general chain-to-chain interop layer.
- **Your action can't fit one L1 block.** Long-running or multi-block flows need a
  different design.
- **You can't tolerate a liveness dependency.** The composer precomputes tables. If it's
  down, cross-chain calls don't compose — though L1 remains the source of truth and
  followers can still re-derive.

## Arguments that don't hold up

Don't make these; flag them in drafts.

- **"Trustless" without qualification.** Re-derivability is real and worth claiming: any
  follower rebuilds the L2 chain from L1 data alone. Sequencing is a single builder
  today. Claim the first, don't imply the second.
- **"ZK-verified" in present tense.** See `stack-and-trust.md`. Today's attestation
  comes from a daemon that independently re-executes the block window and signs the
  recomputed public input — meaningfully better than a rubber stamp, and not a ZK proof.
  The interesting true story is that the pipeline was built so swapping in a real proof
  changes one interface.
- **"Faster than bridges."** Category error. It's not a faster bridge; it's a different
  programming model. A reader who hears "faster" will benchmark it against a bridge and
  conclude the wrong thing.
- **"Works with your existing contracts, no changes."** Nearly true and the exceptions
  matter: proxy opcode semantics and block-context differences are real behavioral
  changes. Say "most contracts work unchanged, with these specific exceptions."
- **Dismissing async messaging as obsolete.** It's simpler and appropriate for most
  cross-chain needs. Overclaiming here costs credibility with exactly the engineers who
  have shipped async integrations and know their tradeoffs.

## Phrasebook

Reusable one-liners, calibrated for app developers. Use them for consistency across
formats.

**Synchronous composability** — Your contract calls a contract on another chain and uses
the answer in the same transaction, instead of sending a message and handling the reply
later.

**Realtime proving** — The state transition is computed and proven fast enough to settle
within the same L1 block, which is what makes same-transaction calls possible at all.

**Execution entry** — A precomputed record of what a cross-chain call will do: its
target, its return value, and every nested call inside it. The chain checks it rather
than discovering it.

**Execution table** — The set of entries for one block, built by the composer and posted
to L1.

**Rolling hash** — A single hash chaining everything that happened during an entry. If
execution diverges from what was proven anywhere — wrong return value, missing call,
wrong order — the hash differs and the entry is rejected. Builders don't compute it;
they rely on it.

**CrossChainProxy** — The deterministic address that represents your contract on the
other chain. Callers there see it as `msg.sender`. One per
`(address, rollupId)` pair.

**Composer** — The off-chain component that watches both chains, precomputes the tables,
and posts them. App developers don't run one; operators do.

**Based rollup** — A rollup that inherits sequencing from L1 rather than running its own
sequencer, which is what lets two of them share a synchronous execution context.

**Same-block constraint** — Entries are consumable only in the block whose batch proved
them. There is no queue for later.
