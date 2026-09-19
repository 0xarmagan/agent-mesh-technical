# Review: "EEZ Hegota View (WIP)" Notion draft — technical-accuracy pass

**Date:** 2026-09-17 · **Tier:** MEDIUM · **Source draft:** Notion page `3de3b92f9cd080d1a631f88f92002ed0` (EEZ Wiki), last edited 2026-09-17 10:51 UTC
**Dispatch:** eez-protocol-dev, ethereum-core-dev, zk-proving-specialist (parallel, isolated) + technical-accuracy gate. Source clone: eez-core-protocol main @ 03e87cd.

## Gate verdict
NEEDS REVISION — 1/5 FAIL (multi-prover). Sync-vs-async PASS, execution entries PASS, proxies N/A, L2 framing N/A.

## Core claim
The draft's ranking logic is sound but two S-tier justifications rest on wrong mechanics (7906 is not a cross-tx bundle backstop; 8025 proves L1 blocks, not rollup batches), and several EEZ specifics are misnamed or unsourced.

## Findings (severity order)
1. **EIP-7906 mischaracterized.** It asserts a single tx's own pre/post state diff (TXDIFF-style opcodes); it cannot make one tx in a bundle verify that other bundle txs executed. "Only protocol-level backstop for partial inclusion" is false. Reposition as single-tx pre/postcondition checking. FOCIL (EIP-7805, S-tier) is the omitted EIP actually relevant to inclusion.
2. **EIP-8025 layer mismatch.** 8025 = CL-side zkEVM proofs of L1 execution payloads. EEZ multi-prover = per-rollup `IProofSystem` verification of rollup batches in `Rollup.sol:104-122`. No plug-in relationship; at most an analogy.
3. **Multi-prover floor (gate FAIL).** Lens item 2 "Batches carry proofs; L1 verifies them" and the 8025 paragraph omit that `threshold` may be 0 (`Rollup.sol:35,208-211`) — no protocol-level floor. Fix: add "there is no protocol-level floor" to the 8025 sentence.
4. **`postBatch` does not exist.** Entry point is `postAndVerifyBatch` (`EEZ.sol:354`). "Nothing at the protocol level catches it" is too strong: optional `expectedRootPerRollup` assertions (`EEZ.sol:365`, `IEEZ.sol:35`) and the same-block gate `ExecutionNotInCurrentBlock` (`EEZ.sol:203,825,855`) exist. Soften to "no guard against a builder splitting the bundle."
5. **EIP-8146 overstated.** BAL sidecars are an L1 propagation/prefetch optimization for ELs, not a proving-cost reducer; EEZ provers prove rollup state transitions, not L1 blocks. Benefit is indirect at best.
6. **EIP-8371 overstated.** RowDAS distributes PeerDAS reconstruction; it is not a blob-count increase. "More blob capacity" → "more efficient DA reconstruction, enabling future capacity."
7. **Nonce-lane claim UNVERIFIED.** No composer/poster identities in source (NatSpec labels only). Operational claim — label as such.
8. **Derivation wording.** L1 emits `RootUpdated`, `BatchPosted`, `ExecutionConsumed`, `EntryExecuted` etc. (`EEZ.sol:130-166`); L2 emits `ExecutionTableLoaded` (`EEZL2.sol:102`). "Rebuild rollup state from L1 events" overstates what L1 exposes.
9. **EIP-8375 label.** It is ePBS execution-reward burn (MEV-burn economics), not issuance/monetary policy like 8363.
10. **Hegota tiers UNVERIFIED** for all but 8141 (SFI) and 8198 (S-tier recommended). Don't assert tier labels without the ethereum/pm tracker.

Verified correct: 8250→8141 dependency, 8272 recent roots, `revertNextNCalls` live (`EEZ.sol:1098-1169`), "execution table" is source vocabulary (`EEZ.sol:340`, `EEZL2.sol:100`), `CrossChainProxy` staticcall surface (`CrossChainProxy.sol:94`), no "bridge"/"L2" misuse, composer not anthropomorphized as EEZ.

## Key assumption
EIP facts checked via search snippets of eips.ethereum.org / EF blog, not the ethereum/pm inclusion tracker directly.

## Open choice points
- Add FOCIL (7805) to S/A-tier or state why excluded.
- Keep 7906 in S-tier as single-tx precondition tool, or demote.

## Status
2026-09-17: findings 1-9 applied to the Notion page. Open choice points untouched.
