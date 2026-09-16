# agent-mesh-technical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build agent-mesh-technical — a multi-expert orchestration repo whose 8 experts master EEZ technical topics (protocol, contracts, Ethereum core, ZK, security, MEV, integration) and execute code via the Dynamic Workflows pipeline, grounded in live eez-core-protocol source.

**Architecture:** Mirror of agent-mesh's orchestrator → isolated-expert-dispatch → synthesis → wiki → DW-execution skeleton, with a new grounding layer: `knowledge/sources.md` points at live repos, experts cite `.sol` `file:line`, primers carry `source-commit` hashes, and verifier criteria for code tasks must be executable.

**Tech Stack:** Claude Code agent definitions (markdown + YAML frontmatter), git, `gh` CLI, Foundry (`forge`) for contract verification tasks.

**Spec:** `docs/superpowers/specs/2026-09-16-agent-mesh-technical-design.md` (in this repo)

## Global Constraints

- Repo root: `/Users/armagan/Documents/agent-mesh-technical`. Source material lives in `/Users/armagan/Documents/agent-mesh` (read-only — never modify that repo).
- **Source of truth rule (copy verbatim wherever cited):** "The canonical reference for every EEZ contract-level / technical fact is https://github.com/eez-association/eez-core-protocol (branch `main`) — function signatures, error names, derivation math, structs, revert behavior. KB explainers are secondary; if a doc conflicts with the source, the source wins. `main` moves: re-clone fresh before technical work."
- **Never copy files from `agent-mesh/eez-agent/knowledge/`** into this repo — 101 files are `visibility: internal`, 1 is `partner`, ~19 are untagged, and `00-overview.md` embeds personal emails. Knowledge enters this repo only as pointers (`knowledge/sources.md`) or freshly authored primers.
- **Grounding preamble (insert verbatim into every expert agent, after the first heading):**
  ```markdown
  ## Grounding (read first)

  Before any claim about EEZ contract behavior: read `knowledge/sources.md`, locate the relevant `.sol` file in a fresh clone of eez-core-protocol `main`, and cite `file:line`. KB explainers and primers are secondary — if they conflict with source, the source wins. If no clone is available, say so and mark the claim UNVERIFIED — never substitute doc memory for source.
  ```
- **Expert return contract (all 8 experts):** `**CORE CLAIM** + **EVIDENCE** (with file:line citations for contract-level claims) + **KEY ASSUMPTION** + **BLIND SPOT CHECK**`.
- Frontmatter for every expert: `tools: Read, Bash, Grep, WebSearch` · `model: claude-sonnet-5` · `memory: project`. Orchestrator: `tools: Read, Write, Edit, Bash` · `model: claude-fable-5` · `memory: project`.
- Symbol currency: the eez-protocol-dev skill's rename table wins over any older doc — current names are `StateUpdate`, `StaticExecutionEntry`, `revertNextNCalls`, `executeL2Txs`, `IProofSystem`. Never write the stale forms (`StateDelta`, `LookupCall`, `revertSpan`, `executeL2TX`, `IZKVerifier`) except inside the rename table itself.
- Commit after every task: `git add <files> && git commit -m "<type>: <summary>"` ending the message with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Repo scaffold, core-rules, knowledge/sources.md

**Files:**
- Create: `.gitignore`, `.claude/rules/core-rules.md`, `knowledge/sources.md`, `wiki/index.md`, `wiki/log.md`
- (Spec already copied to `docs/superpowers/specs/2026-09-16-agent-mesh-technical-design.md` — commit it here.)

**Interfaces:**
- Produces: `knowledge/sources.md` — every expert's grounding preamble points here; `.claude/rules/core-rules.md` — imported by CLAUDE.md in Task 3.

- [ ] **Step 1: Write `.gitignore`**

```
clones/
.DS_Store
```

- [ ] **Step 2: Write `.claude/rules/core-rules.md`** — copy `/Users/armagan/Documents/agent-mesh/.claude/rules/core-rules.md` verbatim, then: (a) delete the sentence "Key file map lives in the `eez-contract-demo-method` auto-memory." and replace it with "Key file map lives in `knowledge/sources.md`."; (b) keep the Wiki & Memory section but nothing else changes.

- [ ] **Step 3: Write `knowledge/sources.md`** with exactly these sections:

```markdown
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
```

- [ ] **Step 4: Write wiki scaffold** — `wiki/index.md` containing `# agent-mesh-technical wiki index\n\n(no analyses yet)` and `wiki/log.md` containing `# Operation log\n\n## 2026-09-16 — repo initialized from agent-mesh-technical design spec`.

- [ ] **Step 5: Verify** — Run: `grep -c "eez-core-protocol" knowledge/sources.md` → ≥2; `grep "threshold has NO protocol floor" knowledge/sources.md` → 1 hit; `grep "knowledge/sources.md" .claude/rules/core-rules.md` → 1 hit.

- [ ] **Step 6: Commit** — `chore: scaffold repo, core-rules, source map, wiki`

### Task 2: Durable copy of the eez-protocol-dev skill

**Files:**
- Create: `.claude/skills/eez-protocol-dev/` (SKILL.md + `references/` — 6 files)

**Interfaces:**
- Produces: `.claude/skills/eez-protocol-dev/references/*.md` — the `eez-protocol-dev` expert agent (Task 5) instructs reading these.

- [ ] **Step 1: Copy verbatim**

```bash
cp -R "/Users/armagan/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/05663f74-ad2d-4960-9fbd-2d896d7132c3/84854a0c-794c-41ab-93ce-08dec860bf60/skills/eez-protocol-dev" .claude/skills/
```

- [ ] **Step 2: Verify integrity** — Run: `wc -l .claude/skills/eez-protocol-dev/SKILL.md .claude/skills/eez-protocol-dev/references/*.md` — expect SKILL.md ≈390 lines and 5 reference files (execution-model, architecture, footguns, stack-and-trust, positioning) totaling ≈1085 lines. Diff against the source dir: `diff -r <source> .claude/skills/eez-protocol-dev` → empty.

- [ ] **Step 3: Commit** — `feat: vendor eez-protocol-dev skill (pinned @ 9735f53) as durable copy`

### Task 3: CLAUDE.md constitution + README

**Files:**
- Create: `CLAUDE.md`, `README.md`

**Interfaces:**
- Consumes: `.claude/rules/core-rules.md` (Task 1).
- Produces: the tier table and roster that orchestrator (Task 4) and all agents assume.

- [ ] **Step 1: Write `CLAUDE.md`** — adapt `/Users/armagan/Documents/agent-mesh/CLAUDE.md` with these exact changes: title `# agent-mesh-technical`; first paragraph: "Multi-expert orchestrator for EEZ technical work. Routes protocol, contract, and Ethereum-core questions to specialized technical agents with isolated context, synthesizes their outputs, writes findings to a persistent wiki, and hands implementation-ready tasks to Dynamic Workflows."; keep `@.claude/rules/core-rules.md`; keep the LOW/MEDIUM/HIGH/VERY HIGH operating rules and tier output contract table unchanged; replace the expert roster sentence with the 8-expert table below; keep the Wiki and Dynamic Workflows handoff sections with paths unchanged; delete the Subsystems section; add one new section:

```markdown
## Grounding

- Contract-level claims cite `.sol` file:line from a fresh clone (see `knowledge/sources.md`). Doc memory is never a substitute.
- Verifier done-criteria for code tasks must be executable (`forge test`, `node --check`, a runnable script) — prose criteria are rejected in Contract Critique.
- Never copy content from agent-mesh's `eez-agent/knowledge/` into this repo (internal/partner material).
```

Roster table for CLAUDE.md and README:

| Agent | Domain |
|---|---|
| eez-protocol-dev | Execution entries, rolling hashes, batch/proof flows, EEZ core code |
| smart-contract-engineer | Solidity, proxy patterns, gas, contract-level design/review |
| protocol-designer | Composability model, trust assumptions, standard & GIP design |
| ethereum-core-dev | L1 consensus, EIPs, based sequencing, DA/blobs, clients |
| zk-proving-specialist | Proof systems, multi-prover verification, validity proofs |
| security-auditor | Threat models, reentrancy, cross-chain attack surfaces |
| mev-sequencing-economist | Composer fee market, based-sequencing incentives, MEV |
| rollup-integration-engineer | How an L2 joins EEZ: node changes, sequencer, deposits |

- [ ] **Step 2: Write `README.md`** — ≤120 lines: what the repo is (2 paragraphs), the roster table above, the two-stage pipeline summary (Analysis / Execution, condensed from agent-mesh README), get-started (ask a technical question; clone command from `knowledge/sources.md`), and a pointer to the spec. No algorithm detail tables.

- [ ] **Step 3: Verify** — `grep -c "eez-protocol-dev\|smart-contract-engineer\|protocol-designer\|ethereum-core-dev\|zk-proving-specialist\|security-auditor\|mev-sequencing-economist\|rollup-integration-engineer" CLAUDE.md` → ≥8; `wc -l README.md` → ≤120.

- [ ] **Step 4: Commit** — `feat: constitution and README`

### Task 4: Orchestrator (heaviest rewrite)

**Files:**
- Create: `.claude/agents/orchestrator.md`
- Reference (read-only): `/Users/armagan/Documents/agent-mesh/.claude/agents/orchestrator.md`

**Interfaces:**
- Consumes: roster from Task 3.
- Produces: dispatch pipeline all experts plug into; `## Active Task Context` template in `.claude/active-task.md` (format copied unchanged from source orchestrator STEP 5b) consumed by DW agents (Task 8).

- [ ] **Step 1: Write the agent** — start from the source orchestrator verbatim, then apply exactly these changes:
  1. Frontmatter `description:` → "Route complex EEZ protocol, smart contract, and Ethereum-core questions to specialized technical expert agents. Use proactively for technical analysis requiring multi-dimensional expertise or protocol decisions."
  2. STEP 1 tier examples → technical flavor: LOW "single-contract question answerable from one file"; MEDIUM "multi-contract or cross-layer analysis"; HIGH "protocol design change or upgrade path"; VERY HIGH "standard/spec change, security posture, or irreversible deployment decision".
  3. STEP 2 dependency pairs → replace the three business pairs with:
     - security-auditor often needs smart-contract-engineer's design output (audit what will actually be built)
     - mev-sequencing-economist often needs protocol-designer's mechanism sketch
     - zk-proving-specialist feeds ethereum-core-dev on proof-related L1 questions
  4. STEP 4e → replace the Strategic Coherence Check with a **Technical Coherence Check** (when protocol-designer was dispatched): "Map the design claim through the other domains — spec-conformant (eez-protocol-dev)? implementable and gas-feasible (smart-contract-engineer)? sound trust model (security-auditor)? provable (zk-proving-specialist)? Any contradicting layer becomes a Choice Point."
  5. Add to STEP 2 dispatch instructions: "Every dispatched expert receives the reminder: ground contract-level claims in `.sol` source with file:line citations per `knowledge/sources.md`."
  6. STEP 5c: append to the Contract Critique instruction: "For code tasks, REVISE any criterion that is not executable (`forge test`, `node --check`, runnable script)."
  7. Keep everything else (STEP 0, 1.5, 3-absent numbering quirk, 4a–4h, 5, 5b, 6, 6b) byte-identical — including reframe-audit and tier inheritance.

- [ ] **Step 2: Verify** — `grep -c "Technical Coherence Check" .claude/agents/orchestrator.md` → ≥1; `grep -c "Brand & Market Strategist\|Financial Analyst\|Growth Leader" .claude/agents/orchestrator.md` → 0; `grep -c "file:line" .claude/agents/orchestrator.md` → ≥1.

- [ ] **Step 3: Commit** — `feat: technical orchestrator`

### Task 5: Expert batch A (protocol core)

**Files:**
- Create: `.claude/agents/eez-protocol-dev.md`, `.claude/agents/smart-contract-engineer.md`, `.claude/agents/protocol-designer.md`, `.claude/agents/ethereum-core-dev.md`
- Reference (read-only): `/Users/armagan/Documents/agent-mesh/.claude/agents/web3-protocol-architect.md` (format template), `.claude/skills/eez-protocol-dev/` (content for the first agent)

**Interfaces:**
- Consumes: grounding preamble + return contract + frontmatter from Global Constraints.
- Produces: agent filename stems used verbatim in `[expert:]` tags and Task 3's roster.

Every agent follows web3-protocol-architect.md's section skeleton: frontmatter → one-paragraph identity → `## Grounding (read first)` (verbatim from Global Constraints) → `## Your Analytical Core` (How you think / Frameworks you apply / Questions you always ask) → `## Your Blind Spots` (with a one-line **Check:**) → `## How to Use This Expertise` (return contract).

- [ ] **Step 1: Write `eez-protocol-dev.md`** — description: "EEZ core protocol: execution entries, rolling hashes, batch/proof flows, postAndVerifyBatch, CrossChainProxy, revertNextNCalls, StateUpdate, StaticExecutionEntry. Invoke for any EEZ contract-level or protocol-mechanics question." Identity + analytical core distilled from `.claude/skills/eez-protocol-dev/SKILL.md` ("The mental model to teach" and "Opinions worth holding" sections); add instruction: "Read `.claude/skills/eez-protocol-dev/references/execution-model.md` and `architecture.md` before answering; check `footguns.md` before reviewing code." Blind spots: incentive design, UX cost of protocol complexity, non-EEZ rollup ecosystems.

- [ ] **Step 2: Write `smart-contract-engineer.md`** — description: "Solidity implementation and review: proxy patterns, gas, storage layout, access control, Foundry testing. Invoke for contract-level design, implementation, or code review." Analytical core: threat-model-first, checks-effects-interactions, storage collision awareness in proxies, gas profiling with `forge snapshot`, invariant testing. Blind spots: protocol-economics, L1 consensus implications, spec-level trust assumptions.

- [ ] **Step 3: Write `protocol-designer.md`** — description: "Spec/architecture level: synchronous composability model, trust assumptions, standard design, GIP/EIP-process design. Invoke for protocol architecture decisions or standard/spec changes." Analytical core: trust-assumption enumeration first, minimal-standard bias (what the spec must NOT prescribe — e.g. EEZ prescribes a finality point, not a proving mechanism), compatibility surface (based + centralized-sequencer rollups), upgrade/governance path. Blind spots: implementation cost, gas realities, prover performance limits.

- [ ] **Step 4: Write `ethereum-core-dev.md`** — description: "Ethereum L1: consensus, EIPs, based sequencing, DA/blobs (EIP-4844), client behavior, L1 inclusion guarantees. Invoke when a question turns on what L1 actually guarantees or where the protocol roadmap is going." Analytical core: distinguish L1 guarantees from L2 conventions, EIP lifecycle literacy, blob market dynamics, proposer/builder separation, reorg tolerance. Blind spots: application-layer DX, contract implementation detail, business viability.

- [ ] **Step 5: Verify** — for each file: `head -8` shows frontmatter with `tools: Read, Bash, Grep, WebSearch`, `model: claude-sonnet-5`, `memory: project`; `grep -l "Grounding (read first)" .claude/agents/*.md | wc -l` → 4 so far; `grep -c "BLIND SPOT CHECK" .claude/agents/eez-protocol-dev.md` → ≥1.

- [ ] **Step 6: Commit** — `feat: protocol-core expert agents (batch A)`

### Task 6: Expert batch B (adversarial + economic)

**Files:**
- Create: `.claude/agents/zk-proving-specialist.md`, `.claude/agents/security-auditor.md`, `.claude/agents/mev-sequencing-economist.md`, `.claude/agents/rollup-integration-engineer.md`

**Interfaces:**
- Same skeleton, frontmatter, preamble, and return contract as Task 5.

- [ ] **Step 1: Write `zk-proving-specialist.md`** — description: "Proof systems: validity proofs, multi-prover verification, vkeys, proving latency/cost, TEE vs ZK vs committee finality. Invoke for anything touching IProofSystem, thresholds, or proving-stack choices." Analytical core: soundness vs completeness framing, multi-prover threshold semantics (per `knowledge/sources.md`: threshold is per-rollup, may be 0 — never claim a protocol floor), proving latency as the composability bottleneck, vkey lifecycle. Blind spots: fee economics, contract-level implementation, integration ergonomics.

- [ ] **Step 2: Write `security-auditor.md`** — description: "Adversarial review: threat models, reentrancy, access control, cross-chain attack surfaces, proxy risks. Invoke before any deployment decision and on any 'is this safe' question." Analytical core: attacker-first enumeration; the unified reentrant execution table as a first-class attack surface; cross-chain replay/ordering attacks; access-control matrix per contract; assume the composer is adversarial. Blind spots: shipping-velocity cost of mitigations, UX, economics of attacks (defer to mev-sequencing-economist).

- [ ] **Step 3: Write `mev-sequencing-economist.md`** — description: "Composer fee market, based-sequencing incentives, MEV profiles, ordering economics. Invoke when a design's viability turns on who pays, who orders, or who extracts." Analytical core: who-extracts-what mapping per design; composer-first ordering is a disclosed trust assumption not an L1 guarantee; fee-market design space (L1 fee / L2 fee / direct payment / private agreement); incentive-compatibility checks. Blind spots: cryptographic soundness, implementation detail, L1 client internals.

- [ ] **Step 4: Write `rollup-integration-engineer.md`** — description: "How an L2 actually joins EEZ: node changes, sequencer integration, deposits, registration, operational runbooks. Invoke for onboarding-path, integration-effort, or 'what does a rollup team actually do' questions." Analytical core: integration-path difference between based and centralized-sequencer rollups (eligibility identical, path differs); registration + threshold configuration flow; node's three roles (per `.claude/skills/eez-protocol-dev/references/stack-and-trust.md`); operational failure modes. Blind spots: deep cryptography, L1 politics, token economics.

- [ ] **Step 5: Verify** — `ls .claude/agents/ | wc -l` → 9 (orchestrator + 8 experts); `grep -L "Grounding (read first)" .claude/agents/*.md` → only orchestrator.md listed; `grep -c "may be 0" .claude/agents/zk-proving-specialist.md` → ≥1.

- [ ] **Step 6: Commit** — `feat: adversarial and economic expert agents (batch B)`

### Task 7: Quality agents

**Files:**
- Create: `.claude/agents/meta-advisor.md`, `.claude/agents/completeness-critic.md`, `.claude/agents/wiki-synchronizer.md`
- Reference (read-only): same-named files in `/Users/armagan/Documents/agent-mesh/.claude/agents/`

- [ ] **Step 1: Port `meta-advisor.md`** — copy verbatim; add one paragraph to its audit criteria: "**Source-grounding tiebreaker:** when two experts' claims conflict on a contract-level fact, the claim citing `.sol` file:line from a fresh clone wins; a conflict where neither side cites source is returned as UNVERIFIED, not adjudicated."

- [ ] **Step 2: Port `completeness-critic.md`** — copy verbatim; replace its business gap taxonomy (stakeholders/legal/money-flows/regulators) with: "failure modes, attack surfaces, upgrade/migration paths, operational runbook gaps, test coverage gaps, proving-stack assumptions, L1-dependency risks." Keep the anti-anchoring rule (never read `wiki/` before auditing) unchanged.

- [ ] **Step 3: Port `wiki-synchronizer.md`** — copy verbatim (paths already match this repo's layout); add one audit dimension: "**Primer drift:** for each `knowledge/primer/*.md`, compare its `source-commit:` frontmatter against `git -C clones/eez-core-protocol rev-parse origin/main` (fetch first). Flag any primer whose pin lags upstream; do not silently rewrite primers."

- [ ] **Step 4: Verify** — `grep -c "Source-grounding tiebreaker" .claude/agents/meta-advisor.md` → 1; `grep -c "attack surfaces" .claude/agents/completeness-critic.md` → ≥1; `grep -c "source-commit" .claude/agents/wiki-synchronizer.md` → ≥1; `grep -c "regulators\|gets sued" .claude/agents/completeness-critic.md` → 0.

- [ ] **Step 5: Commit** — `feat: quality agents with technical retuning`

### Task 8: DW execution agents

**Files:**
- Create: `.claude/agents/implementer.md`, `.claude/agents/researcher.md`, `.claude/agents/verifier.md`, `.claude/agents/integrator.md`
- Reference (read-only): same-named files in `/Users/armagan/Documents/agent-mesh/.claude/agents/`

- [ ] **Step 1: Port `implementer.md`** — copy verbatim; in the TDD instructions, add: "For Solidity tasks the test cycle is Foundry: write the failing `forge test` first, run `forge test --match-test <name>` to see it fail, implement, re-run to pass. Never invent an API surface — verify every external call signature against the `.sol` source in `clones/eez-core-protocol` before writing code that calls it."

- [ ] **Step 2: Port `researcher.md`** — copy verbatim; change frontmatter tools to `Read, Bash, WebFetch, WebSearch`; add: "Prefer source over docs: answer from cloned repo code first, official specs second, explainers last. Use `gh` for repo/issue/PR lookups."

- [ ] **Step 3: Port `verifier.md`** — copy verbatim; in Contract Critique mode add: "REVISE any code-task criterion that is not executable — acceptable forms: a `forge test` invocation, `node --check <file>`, or a runnable script with expected output. For protocol-claim tasks, the criterion must name the `.sol` file and symbol the claim is checked against." Keep the Verification Delta format unchanged.

- [ ] **Step 4: Port `integrator.md`** — copy verbatim; **remove the `LOOPS.md` "Rule V" citation** and inline what it stood for as: "Restart policy: after 2 consecutive fails on the same task, revert that task's commits and re-dispatch the implementer fresh — contract and verification criteria carry forward, the failed approach does not." (Same policy text as the orchestrator's Active Task Context template.)

- [ ] **Step 5: Verify** — `ls .claude/agents/ | wc -l` → 16; `grep -c "LOOPS.md" .claude/agents/integrator.md` → 0; `grep -c "forge test" .claude/agents/implementer.md .claude/agents/verifier.md` → ≥1 each.

- [ ] **Step 6: Commit** — `feat: DW execution agents with executable-criteria discipline`

### Task 9: technical-accuracy skill port (with threshold fix)

**Files:**
- Create: `.claude/skills/technical-accuracy/SKILL.md`
- Reference (read-only): `/Users/armagan/Documents/agent-mesh/eez-agent/skills/technical-accuracy/SKILL.md`

- [ ] **Step 1: Port with fixes** — copy the source SKILL.md, then: (a) rewrite distinction #4 from "no single ZK prover is authoritative" to: "Multi-prover, per-rollup threshold: each rollup sets its own proof threshold and there is NO protocol-level floor — the threshold may be 0. Never claim a protocol-wide multi-prover guarantee."; (b) change the Data Sources table to point at `knowledge/sources.md` and `.claude/skills/eez-protocol-dev/references/` instead of the 6 KB docs; (c) replace the hardcoded reviewer "Armagan" with "the repo owner"; (d) update frontmatter `model:` to `claude-sonnet-5`; (e) set Governance Owner to "orchestrator (dispatched pre-publish)".

- [ ] **Step 2: Verify** — `grep -c "may be 0" .claude/skills/technical-accuracy/SKILL.md` → ≥1; `grep -c "claude-sonnet-4-6" .claude/skills/technical-accuracy/SKILL.md` → 0; `grep -c "knowledge/sources.md" .claude/skills/technical-accuracy/SKILL.md` → ≥1.

- [ ] **Step 3: Commit** — `feat: technical-accuracy gate with per-rollup threshold fix`

### Task 10: First primer from fresh source

**Files:**
- Create: `knowledge/primer/00-source-map-verification.md`, `clones/` (gitignored working clone)

**Interfaces:**
- Consumes: `knowledge/sources.md` key-file map (Task 1).
- Produces: the primer format (frontmatter `source-commit:`) that wiki-synchronizer's drift audit (Task 7) reads.

- [ ] **Step 1: Fresh clone** — Run: `gh repo clone eez-association/eez-core-protocol clones/eez-core-protocol && git -C clones/eez-core-protocol rev-parse HEAD` (record the hash).

- [ ] **Step 2: Verify the key-file map against HEAD** — for each entry in `knowledge/sources.md`'s key-file map, `grep -n` the named symbol in the named file (e.g. `grep -n "computeCrossChainProxyAddress" clones/eez-core-protocol/src/base/EEZBase.sol`). Record file:line for every symbol. If a file or symbol moved, update `knowledge/sources.md` in the same commit and note the move.

- [ ] **Step 3: Write the primer** — `knowledge/primer/00-source-map-verification.md` with frontmatter:

```markdown
---
source-commit: <HEAD hash from Step 1>
verified: 2026-09-16
---

# Source map verification

<table of symbol → file:line as found in Step 2, plus any corrections made to knowledge/sources.md>
```

- [ ] **Step 4: Verify** — `grep "source-commit:" knowledge/primer/00-source-map-verification.md` → 1 hit with a 40-char hash; `git status` shows `clones/` untracked-ignored.

- [ ] **Step 5: Commit** — `feat: first source-verified primer (pins current main)`

### Task 11: Adversarial validation (two passes)

**Files:**
- Create: `wiki/notes/validation-run-1.md`, `wiki/notes/validation-run-2.md` (findings), fixes to any agent files flagged

- [ ] **Step 1: Pass 1 — hard divergent question.** Dispatch a fresh context-free subagent in this repo with: "Answer using only this repo's agents/skills/knowledge: *A centralized-sequencer rollup with proof threshold 0 wants to join EEZ and expose synchronous L1 reads to its dapps. Walk the full integration path, the trust model a user of that rollup accepts, and what breaks if the composer censors it.*" Instruct it to flag every point where it fell back on outside knowledge or wasn't confident the repo's guidance was correct/complete. Expect the orchestrator to route to rollup-integration-engineer + zk-proving-specialist + security-auditor + mev-sequencing-economist.

- [ ] **Step 2: Fix pass-1 gaps** — every flagged gap becomes an edit to the relevant agent/skill/knowledge file. Write findings + fixes to `wiki/notes/validation-run-1.md`.

- [ ] **Step 3: Pass 2 — integration plumbing.** Dispatch a second fresh subagent: "Audit whether every consumer reads the new decisions: does CLAUDE.md's roster match `ls .claude/agents/`? Do the orchestrator's dependency pairs name only existing agent stems? Does every expert contain the grounding preamble verbatim? Do verifier/implementer/integrator reference only files that exist in this repo? Does README match the roster? Grep for leftovers: `grep -rn 'Brand\|Financial Analyst\|Growth Leader\|LOOPS.md\|eez-agent/knowledge' .claude/ CLAUDE.md README.md` — report every hit." If it hits a turn limit, demand findings in ≤3 tool calls at whatever confidence held.

- [ ] **Step 4: Fix pass-2 findings, write `wiki/notes/validation-run-2.md`, update `wiki/index.md` + `wiki/log.md`.**

- [ ] **Step 5: Final verify** — `grep -rn "Brand & Market\|LOOPS.md" .claude/ CLAUDE.md README.md` → 0 hits; `ls .claude/agents/ | wc -l` → 16.

- [ ] **Step 6: Commit** — `test: adversarial validation passes and fixes`
