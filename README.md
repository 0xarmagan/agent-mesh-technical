# agent-mesh-technical

Multi-expert orchestrator for EEZ technical work. An orchestrator routes protocol, contract, and Ethereum-core questions to specialized technical agents with isolated context, synthesizes their findings, and remembers everything in a wiki.

Unlike agent-mesh's strategy roster, every expert here grounds claims in the actual `eez-core-protocol` source rather than doc memory — contract-level facts cite `.sol` file:line from a fresh clone, and implementation-ready tasks hand off to Dynamic Workflows with executable (not prose) done-criteria.

## The roster

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

## How it works

**Stage 1 — Analysis.** You ask a technical question. The orchestrator judges its complexity tier, picks experts by domain relevance, and dispatches them in parallel with isolated context (experts never see each other's outputs). It synthesizes convergent findings, contradictions (Choice Points for you to resolve), and gaps. Findings go to the wiki; implementation-ready tasks go to `.claude/active-task.md`.

**Stage 2 — Execution.** Dynamic Workflows reads `.claude/active-task.md` and spawns role agents: implementer (writes code), researcher (read-only), verifier (checks done-criteria are executable — `forge test`, `node --check`, a runnable script), integrator (loops or completes). Each task is tagged `[expert: <name>]` so the implementer reads that expert's definition first.

## Get started

Ask a technical question in Claude Code — e.g. "does `postAndVerifyBatch` allow a zero proof threshold?" No setup beyond cloning this repo and a fresh clone of the source protocol:

```bash
gh repo clone eez-association/eez-core-protocol clones/eez-core-protocol
```

See `knowledge/sources.md` for the full source map and clone-freshness rules. When an analysis produces an Active Task Context, review it, resolve any Open Choice Points, then trigger execution:

```
Execute the Active Task Context in .claude/active-task.md using ultracode.
Read .claude/active-task.md first — the task list, constraints, and verification criteria are there.
Use the role-based agents defined in .claude/agents/.
```

## Documentation

- Constitution: `CLAUDE.md`
- Full pipeline protocol: `.claude/agents/orchestrator.md`
- Design spec: `.superpowers/sdd/2026-09-16-agent-mesh-technical/`
