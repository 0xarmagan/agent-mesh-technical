# Validation run 2 — integration plumbing audit (2026-09-16)

## Scope
A second adversarial pass checking whether decisions/mechanisms introduced elsewhere in the repo are actually wired into every consumer (contracts, counts, lists, layouts, gates, quick-ref tables), not just whether the pipeline produces a working answer.

## Checks run
Numbered checks 1–8 against the repo's agent/skill/CLAUDE.md wiring.

- **Checks 2, 3, 5, 6, 8 — PASS.** No wiring defects found in these areas.

## Defects found and fixed
- **CLAUDE.md missing quality-agent mention** — the DW execution layer sentence named `implementer`/`researcher`/`verifier`/`integrator` but the quality layer (`meta-advisor`, `completeness-critic`, `wiki-synchronizer`) was defined in `.claude/agents/` yet never referenced from CLAUDE.md, so a reader relying on CLAUDE.md as the map would miss them entirely. → **FIX 5** (see `validation-run-1.md`).
- **`wiki-synchronizer.md` section-name drift** — it instructed reading CLAUDE.md's "Wiki structure" section, but the actual heading in CLAUDE.md is "Wiki (persistent memory)" — the agent would fail to find its own prerequisite reading. → **FIX 6**: corrected the reference.

Checks 1, 4, 7 outcomes: 1 = defect fixed (CLAUDE.md quality-agents mention); 4 = defect fixed (wiki-synchronizer section name); 7 = parked with ruling (missing `memory:` key, by design).

## Parked with ruling
- **Missing `memory:` frontmatter key on `implementer`/`researcher`/`verifier`/`integrator`/`wiki-synchronizer`.** Flagged as a possible gap, but this matches the agent-mesh source pattern and is by design: these are stateless execution/audit roles that shouldn't carry persistent per-agent memory across invocations. No fix applied — ruled correct as-is.
