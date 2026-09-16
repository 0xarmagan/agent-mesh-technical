# agent-mesh-technical — Design Spec

**Date:** 2026-09-16
**Status:** Approved design, pre-implementation
**Location:** New sibling repo `~/Documents/agent-mesh-technical`

## Purpose

A technical counterpart to agent-mesh: a multi-expert orchestration system whose experts master the technical topics of EEZ (synchronous rollups, execution entries, batch/proof flows, cross-chain proxies, based sequencing) and work together on analysis **and** code execution. agent-mesh stays the strategy/business mesh; agent-mesh-technical owns protocol, contract, and Ethereum-core work.

## Scope decisions (user-confirmed)

- New sibling repo, not a subdirectory of agent-mesh.
- Analysis + code execution: experts analyze technical questions AND the Dynamic Workflows pipeline implements/reviews code (contracts, protocol demos, spec drafts).
- Full expert roster: the four named roles plus ZK/proving specialist, security auditor, MEV/sequencing economist, and rollup-integration engineer.

## Architecture

Mirror of agent-mesh's proven skeleton, with a technical grounding layer added.

```
agent-mesh-technical/
├── CLAUDE.md                  ← constitution: tiering, grounding rules, source of truth
├── README.md
├── .claude/
│   ├── rules/core-rules.md    ← EEZ source-of-truth rule (inherited verbatim from agent-mesh)
│   ├── agents/                ← orchestrator + 8 experts + 3 quality + 4 DW execution
│   └── skills/                ← technical-accuracy gate, eez grounding conventions
├── knowledge/                 ← POINTERS to live repos + thin cached primer (not a copied corpus)
│   ├── sources.md             ← repo URLs, local clone paths, key-file map
│   └── primer/                ← short EEZ concept primers, marked with source-commit hash
└── wiki/                      ← same structure as agent-mesh (index, log, notes, meta, …)
```

### Analysis experts (8)

| Agent file | Domain | Notes |
|---|---|---|
| `eez-protocol-dev` | Execution entries, rolling hashes, batch/proof flows, `postAndVerifyBatch`, `CrossChainProxy`, EEZ core code | Seeded from the existing `eez-protocol-dev` skill content |
| `smart-contract-engineer` | Solidity, proxy patterns, gas, contract-level design and review | |
| `protocol-designer` | Spec/architecture level: composability model, trust assumptions, standard & GIP design | |
| `ethereum-core-dev` | L1 consensus, EIPs, based sequencing, DA/blobs, client behavior | |
| `zk-proving-specialist` | Proof systems, multi-prover verification, validity proofs | |
| `security-auditor` | Adversarial review: threat models, reentrancy, cross-chain attack surfaces | |
| `mev-sequencing-economist` | Composer fee market, based-sequencing incentives, MEV profiles | Bridges technical and incentive design |
| `rollup-integration-engineer` | How an L2 joins EEZ: node changes, sequencer integration, deposits | Alliance-onboarding-facing |

Each expert keeps agent-mesh's persona format (analytical core, frameworks, blind spots, return contract: Core Claim + Evidence + Key Assumption + Blind Spot) **plus** a mandatory grounding preamble: read `knowledge/sources.md`, ground contract-level claims in the actual `.sol` source, cite `file:line`.

### Kept from agent-mesh (adapted)

- **orchestrator** — same pipeline (tiering → pre-analysis challenge → dispatch → synthesis → Active Task Context → wiki writeback). Retuned: technical tier heuristics; new dependency pairs (security-auditor after smart-contract-engineer; mev-sequencing-economist after protocol-designer; zk-proving-specialist feeds ethereum-core-dev on proof-related L1 questions).
- **Quality agents** — meta-advisor, completeness-critic, wiki-synchronizer. Wiki-synchronizer gains a drift audit: primer source-commit hashes vs upstream `main`.
- **DW execution four** — implementer, researcher, verifier, integrator, with `[expert:]` tagging. Verifier's Contract Critique mode rejects prose criteria for code tasks: done-criteria must be executable (`forge test`, `node --check`, a runnable demo).

### Grounding layer (new)

- **Source of truth:** `https://github.com/eez-association/eez-core-protocol` (`main`) for every contract-level fact — inherited verbatim from agent-mesh core-rules. `main` moves: pull/re-clone before technical work.
- `knowledge/sources.md` lists repos, local clone paths, and the key-file map. Experts get Read/Bash/Grep and read live source, not cached explainers.
- `knowledge/primer/` files carry a `source-commit:` frontmatter field; wiki-synchronizer flags primers whose commit lags upstream.

## Data flow

Question → orchestrator tiers it → dispatches experts (isolated context, grounded in live source) → synthesis (agreement / tensions / gaps) → wiki writeback → Active Task Context (when execution intent exists) → verifier contract critique → DW execution → verifier runs executable criteria → integrator completes.

## Error handling / known risks (addressed in design)

1. **Corpus staleness** — pointers-not-copies + commit-hash drift audit; no large cached corpus.
2. **Over-dispatch across 8 adjacent domains** — sharp frontmatter boundaries; orchestrator's "when in doubt, drop" rule retained; LOW/Lite path stays aggressive (technical questions one expert can answer skip the ceremony).
3. **Verifier rubber-stamping** — executable-only done-criteria for code tasks, enforced in Contract Critique mode.
4. **Local clone availability** — `knowledge/sources.md` is the single place holding clone paths; a missing clone is a setup error surfaced to the user, never silently substituted with KB explainers.

## Testing / validation

- Adversarial validation pass after build (per skill-authoring practice): dispatch a fresh subagent on a hard EEZ technical question divergent from the design examples; require it to self-report where guidance was incomplete.
- Second pass targeting integration plumbing: does every consumer (orchestrator dispatch table, dependency pairs, CLAUDE.md roster, README) read the new roster and grounding rules?

## Out of scope

- Migrating agent-mesh's business experts or wiki content.
- Public distribution; repo starts private/local.
- Marketing/content workflows (stay in eez-agent).
