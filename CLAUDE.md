# agent-mesh-technical

Multi-expert orchestrator and source-grounded wiki for EEZ technical work.

@.claude/rules/core-rules.md

## Routing

- **LOW** (single-domain, clear, reversible): answer directly (2–3 findings + next steps). No dispatch, no writeback.
- **MEDIUM / HIGH** (multi-domain, ambiguous, or high-stakes): read `.claude/agents/orchestrator.md` first and follow its pipeline.
- **Expert roster:** `.claude/agents/` (select by frontmatter `description`; prefer 2–3 focused experts).
- **Isolated context** is mandatory for parallel expert dispatch: experts never see each other's outputs.
- **External-facing artifacts** require human review and must pass `.claude/skills/technical-accuracy/SKILL.md` (paired with source checks for protocol mechanics).

## Optional workflows (read only when triggered)

- **VERY HIGH / Collaboration Mode & reframe audits:** read `.claude/workflows/very-high.md` only for irreversible protocol/spec/deployment decisions or when explicitly requested.
- **Stage 2 Dynamic Workflows handoff (`.claude/active-task.md`):** read `.claude/workflows/stage2-dw.md` only when explicitly asked to prepare a DW/ultracode task handoff.

## Wiki (persistent memory)

```
wiki/
├── index.md    ← catalog of analyses — read before answering
├── log.md      ← operation log — read last 5 entries each session
├── notes/  entities/  concepts/  sources/  meta/
```

- `wiki/meta/` holds learned lessons (`calibration.md`, `user-prefs.md`, etc.); created on first need.
- Writeback after every MEDIUM+ response is mandatory (speculative/hypothetical questions need only a `wiki/log.md` entry).
- Periodic drift check: `wiki-synchronizer` (`.claude/agents/wiki-synchronizer.md`) + `python3 scripts/check_wiki_drift.py`.

## Grounding

- Contract-level claims cite `.sol` file:line from a fresh clone (`knowledge/sources.md`). Doc memory never substitutes for source.
- Never state a numeric latency or finality figure from memory — verify against `knowledge/sources.md` and `.claude/skills/eez-protocol-dev/references/positioning.md`, or use qualitative framing.
- Never copy content from agent-mesh's `eez-agent/knowledge/` into this repo (internal/partner material).
