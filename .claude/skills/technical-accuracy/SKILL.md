---
name: technical-accuracy
description: Run before any EEZ content is finalised — checks draft against 5 technical distinctions that must not be blurred. Use after alliance-outreach, content-ingestion, or gip-authoring produces a draft.
---

# Technical Accuracy Skill

Pre-publish gate for EEZ content. Checks any draft that touches EEZ technical claims against five distinctions that have been blurred in the past. A single FAIL blocks approval.

## Trigger

Run this skill whenever a draft:
- Mentions finality, speed, or transaction throughput
- Describes how EEZ chains move state or assets cross-chain
- Describes EEZ's proving or security model
- Uses the words "L2", "layer", "bridge", "transaction", or "ZK prover"
- Is produced by `alliance-outreach`, `content-ingestion`, or `gip-authoring` and will be sent externally

Also run on any draft that the repo owner flags as "check the technical claims."

---

## The 5 Distinctions

---

### 1. Native/synchronous composability vs async messaging

**Correct:** EEZ's cross-chain composability is native and synchronous at the protocol level — a call executes within the same L1 block via proxies, not through an async messaging bridge with its own delayed settlement path. Any specific latency or finality figure (e.g. a settlement time in seconds or minutes) must be verified against current source before use — do not state one from memory. Check `knowledge/sources.md` and `.claude/skills/eez-protocol-dev/references/positioning.md` before writing a number.

**Common wrong version:** Citing a specific finality/settlement time figure without verifying it against source, or describing EEZ's composability as an async bridge/messaging path.

**Pass criterion:** If the draft mentions finality, speed, or a specific time figure, that figure must be traceable to `knowledge/sources.md` or the positioning reference, not asserted from memory. The draft must not describe EEZ-native composability as an async messaging/bridge mechanism.

---

### 2. Execution entries, not transactions

**Correct:** EEZ native rollups process "execution entries." This is the correct technical term. It is not an alias for "transaction."

**Common wrong version:** "Transactions are submitted to EEZ" or "each transaction in the rollup."

**Pass criterion:** Draft uses "execution entries" when describing operations processed inside an EEZ native rollup. "Transaction" is acceptable only when referring to the L1 layer or to a partner chain's own model — not to EEZ-native operations.

---

### 3. Proxies, not bridges

**Correct:** Cross-chain movement in EEZ is handled via proxies. Proxies are synchronous and share state — there are no extra trust assumptions. Bridges are asynchronous and carry their own trust model.

**Common wrong version:** "EEZ bridges assets between chains" or "the EEZ bridge."

**Pass criterion:** Draft does not use the word "bridge" to describe EEZ's cross-chain mechanism. "Proxy" or "proxies" is used instead. If the draft discusses a third-party bridge (e.g. a partner's own bridge), that reference is clearly scoped to the external party and not attributed to EEZ.

---

### 4. Multi-prover, per-rollup threshold

**Correct:** Multi-prover, per-rollup threshold: each rollup sets its own proof threshold and there is NO protocol-level floor — the threshold may be 0. Never claim a protocol-wide multi-prover guarantee.

**Common wrong version:** "EEZ uses a ZK prover" or "the EEZ ZK proof system" as if there is one, or "EEZ requires N proofs" as if a protocol-wide minimum exists.

**Pass criterion:** Draft does not describe EEZ as having "a prover" or "the prover." If proving is mentioned, the per-rollup threshold model is acknowledged — either explicitly (each rollup sets its own threshold, which may be 0) or by avoiding singular/definite framing and avoiding any claim of a protocol-wide floor.

---

### 5. Economic zone framing, not L2 framing

**Correct:** EEZ is an economic zone built on Ethereum. It is not "a Layer 2." Calling it an L2 flattens the positioning and misrepresents the architecture and mission.

**Common wrong version:** "EEZ is an L2," "EEZ is a Layer 2 network," "the EEZ L2."

**Pass criterion:** Draft does not use "L2" or "Layer 2" as a description of EEZ itself. References to EEZ using L2 infrastructure (e.g. "native rollups are a type of L2 construction") are acceptable if they frame EEZ as something built on top of, not equivalent to, that construction.

---

## Eval Format

Run each distinction in order. Output:

```
[NATIVE/SYNC COMPOSABILITY vs ASYNC MESSAGING]
Status: PASS | FAIL | N/A
Issue: (if FAIL) quote the draft's incorrect claim
Fix: (if FAIL) rewritten sentence that is correct

[EXECUTION ENTRIES]
Status: PASS | FAIL | N/A
Issue: (if FAIL) quote the draft's incorrect claim
Fix: (if FAIL) rewritten sentence that is correct

[PROXIES NOT BRIDGES]
Status: PASS | FAIL | N/A
Issue: (if FAIL) quote the draft's incorrect claim
Fix: (if FAIL) rewritten sentence that is correct

[MULTI-PROVER]
Status: PASS | FAIL | N/A
Issue: (if FAIL) quote the draft's incorrect claim
Fix: (if FAIL) rewritten sentence that is correct

[ECONOMIC ZONE NOT L2]
Status: PASS | FAIL | N/A
Issue: (if FAIL) quote the draft's incorrect claim
Fix: (if FAIL) rewritten sentence that is correct
```

---

## Overall Verdict

After all five evaluations:

```
VERDICT: APPROVED
All checked distinctions pass. Draft is cleared for the repo owner's review.
```

or

```
VERDICT: NEEDS REVISION
[N] distinction(s) failed. Apply the fixes above before the draft proceeds.
```

APPROVED means all five are PASS or N/A. A single FAIL produces NEEDS REVISION regardless of the other four.

---

## Data Sources

| Source | Used for |
|---|---|
| `knowledge/sources.md` | Canonical file map for EEZ technical facts |
| `.claude/skills/eez-protocol-dev/references/` | Execution model, architecture, footguns, stack-and-trust, positioning |

When a FAIL produces an ambiguous correction, read the relevant doc above before writing the Fix line. Do not invent technical corrections from memory.

---

## Rules

- N/A is valid when the draft genuinely does not touch that distinction. Do not fail content for not discussing something.
- Do not fail a draft that correctly avoids a topic — silence on a distinction is not a violation.
- Quote the draft's exact text in the Issue field. Do not paraphrase.
- The Fix must be a drop-in replacement, not a note to the author. Write the corrected sentence.
- This skill does not check style, voice, or partner framing — that is `alliance-outreach` scope. Scope here is technical accuracy only.
- If the draft is too ambiguous to evaluate a distinction (e.g. finality mentioned but context unclear), mark FAIL with Issue noting the ambiguity. Ambiguity in a public draft is itself a problem.

## Model
- **Model:** claude-sonnet-5
- **Effort:** high

## Governance
- **Owner:** orchestrator (dispatched pre-publish)
- **Evals:** none defined
- **Retirement trigger:** unused for 90 days, or superseded by a more capable skill
