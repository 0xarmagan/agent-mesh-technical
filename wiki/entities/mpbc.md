# MPBC (Multi-Party Block Construction) — relevance to EEZ

**Date:** 2026-09-16 · **Tier:** MEDIUM · **Experts:** mev-sequencing-economist, ethereum-core-dev (isolated dispatch)
**Source:** https://docs.blockspace.forum/mpbc/ (Blockspace Forum)

## What MPBC is
Off-protocol (builder/relay-layer, not a hardfork) mechanism, live on Ethereum mainnet since ~2026-09-16 (~3% of blocks in first 24h). Multiple builders contribute transactions to one block: operators **append** non-competing, non-reverting transactions from opted-in builders on top of the highest-paying single-party base block; the multi-party block ships only if it beats the top single-party bid AND its base builder is that top bidder. Surplus split 25%/25%/25%/25% (base builder / contributor / operator / proposer). V1 scope: non-contentious state only (transfers, self-contained bundles). Compatible with, not dependent on, ePBS/FOCIL.

## Question answered
How does MPBC relate to EEZ, and what benefit could it create?

## Convergent findings (both experts, independently)
1. **MPBC v1 cannot carry EEZ's atomic bundle.** EEZ synchronous composability needs one block to atomically contain `postAndVerifyBatch` (src/EEZ.sol:354) plus the L1 legs / execution-entry consumption (guards `ExecutionNotInCurrentBlock` src/EEZ.sol:826, :856; `RollupBatchActiveThisBlock` src/EEZ.sol:1451) in a specific relative order, touching shared contract state — exactly the "contentious state / granular placement" class MPBC v1 excludes, and MPBC only appends, never inserts ordered bundles.
2. **MPBC doesn't remove the slot-winning problem.** Delivery rule requires the base builder to already be the top bidder, so the composer's bundle must live intact inside the winning builder's base block regardless; MPBC's merging is orthogonal to EEZ inclusion today.
3. **Indirect benefit exists:** a composer that DOES build the base block can absorb extra merged value (25% base-builder surplus share), improving the economics of composer-led block building; and MPBC's standardized builder/operator interfaces are a plausible future integration surface.

## The real hook: MPBC V2
Roadmap (verified from /roadmap): V2 (Q4 2026–Q1 2027) explicitly targets "transactions that require granular placement in the block... competing for state and oracle updates." If shipped, an EEZ composer could plausibly publish its atomic cross-chain bundle as a standardized MPBC builder contribution, getting inclusion without winning the whole slot — this would directly cheapen based sequencing and strengthen EEZ's inclusion story. Speculative until V2 semantics are published (ethereum-core-dev: contentious-state support is framed as unsolved engineering, not scheduled guarantee).

## Key assumptions
- MPBC's v1 non-contentious boundary holds until V2; V2 shipping/semantics unverified.
- EEZ composer inclusion remains a disclosed trust assumption (calldata pinning via `bindMsgSenderInPublicInput` / `expectedRootPerRollup`, comments src/EEZ.sol:239, :619), not an L1 guarantee.

## Unresolved gap (both experts' blind spots converge)
Could the composer restructure its bundle to look "appendable" — e.g. split the batch-post leg from cross-chain legs, or shape it as a self-contained no-external-contention bundle? Needs smart-contract-engineer / rollup-integration-engineer pass plus MPBC /specifications review before ruling v1 integration out entirely.
