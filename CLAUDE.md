# agent-mesh-technical

Multi-expert orchestrator for EEZ technical work. Routes protocol, contract, and Ethereum-core questions to specialized technical agents with isolated context, synthesizes their outputs, writes findings to a persistent wiki, and hands implementation-ready tasks to Dynamic Workflows.

@.claude/rules/core-rules.md

## How this repo operates

- **LOW-complexity questions** (single-domain, clear, reversible): answer directly. No expert dispatch, no writeback.
- **MEDIUM+ analysis** (multi-domain, ambiguous, high-stakes, or long-horizon): Read `.claude/agents/orchestrator.md` FIRST and follow its pipeline — tier assignment, expert routing, synthesis, and writeback are defined there and only there.
- Expert roster lives in `.claude/agents/`, one per row:

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

- Isolated context is mandatory for parallel expert dispatch: experts never see each other's outputs.
- Every external-facing artifact requires human review before sending — and must pass the technical-accuracy gate first (`.claude/skills/technical-accuracy/SKILL.md`).

## Tier output contracts

| Tier | Output |
|---|---|
| LOW | Lite: 2–3 findings + next steps. No dispatch, no writeback. |
| MEDIUM | Standard: Core Claim + Evidence + Key Assumption. Dispatch + wiki writeback + Active Task Context (when execution intent exists — see orchestrator STEP 5b). |
| HIGH | Deep: adds per-expert scenario analysis. |
| VERY HIGH | Collaboration: convergent findings + Choice Points + robust move; coherence check; Meta-Advisor audit. |

## Wiki (persistent memory)

```
wiki/
├── index.md    ← catalog of analyses — read before answering
├── log.md      ← operation log — read last 5 entries each session
├── notes/  entities/  concepts/  sources/  meta/
```

- `entities/` and `meta/` are created on first real need — absence means "nothing learned yet," not an error.
- `wiki/meta/` holds learned routing and framing lessons as prose (calibration.md, persona-fit.md, framing-patterns.md, user-prefs.md).
- Writeback after every MEDIUM+ response is non-negotiable.

## Dynamic Workflows handoff

MEDIUM+ analysis ends with an `## Active Task Context` block written to `.claude/active-task.md` (format defined in orchestrator.md). Review it, resolve any Open Choice Points, then trigger:

```
Execute the Active Task Context in .claude/active-task.md using ultracode.
Read .claude/active-task.md first — the task list, constraints, and verification criteria are there.
Use the role-based agents defined in .claude/agents/.
```

DW execution layer: `implementer` · `researcher` · `verifier` · `integrator` (definitions in `.claude/agents/`). Each task carries an `[expert: <name>]` tag — the implementer reads that expert's definition before implementing, so analysis-phase frameworks carry into execution.
Quality agents: `meta-advisor` (reasoning audit, VERY HIGH), `completeness-critic` (coverage audit, VERY HIGH), `wiki-synchronizer` (wiki/memory/primer drift audit) — definitions in `.claude/agents/`.

## Grounding

- Contract-level claims cite `.sol` file:line from a fresh clone (see `knowledge/sources.md`). Doc memory is never a substitute.
- Verifier done-criteria for code tasks must be executable (`forge test`, `node --check`, a runnable script) — prose criteria are rejected in Contract Critique.
- Never copy content from agent-mesh's `eez-agent/knowledge/` into this repo (internal/partner material).
