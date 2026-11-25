# Stage 2: Dynamic Workflows Handoff (Optional)

Load and follow this workflow **only** when the user explicitly wants a Dynamic Workflows / `ultracode` execution handoff via `.claude/active-task.md`. Skip it entirely for pure analysis, reviews, critiques, or direct implementation.

## STEP 5b: Active Task Context writeback

Overwrite the `## Active Task Context` section of `.claude/active-task.md` with:

```markdown
## Active Task Context

**Decision:** <binding logic from synthesis — one sentence>

**Tasks:**
- [ ] Task N [expert: <agent-filename-stem>]: <implementation-ready description>

**Constraints:**
- Global: <rule all subagents must follow>
- Task N: <constraint from that expert's findings>

**Verification:**
- Task N done when: <observable criterion>

**Retry Policy:** max 3 attempts · on fail: verifier writes delta → integrator injects constraints → re-trigger DW

**Restart Policy:** after 2 consecutive fails on the same task, integrator reverts that task's commits and re-dispatches the implementer fresh — contract and verification criteria carry forward, the failed approach does not

**Open Choice Points:** <none | list of unresolved decisions>

**Source:** agent-mesh-technical synthesis · <YYYY-MM-DD>
```

Rules:
- Tasks must be truly independent.
- Tag each task with the exact agent filename stem from `.claude/agents/` (the implementer reads that definition before implementing).
- Per-task constraints come from that expert's findings, never invented.
- If Open Choice Points exist, write NO tasks — surface the choices and wait for human resolution.

## STEP 5c: Contract negotiation

Runs after 5b, before presenting for DW triggering (skip when Open Choice Points block tasks).

Invoke `verifier` (`.claude/agents/verifier.md`) in **Contract Critique mode**, giving it only each task's `**Verification:**` line. Verifier returns `ACCEPT` or `REVISE` per task.
- On `REVISE`: apply the proposed fix and re-run once (2 rounds max).
- Still `REVISE` after 2 rounds → move that task to **Open Choice Points** (needs a human call).
- When all remaining tasks `ACCEPT`, append: `**Contract:** negotiated · verifier-accepted <YYYY-MM-DD>`.
- Qualitative check — testable, specific, not rubber-stampable. For code tasks, `REVISE` any criterion that is not executable (`forge test`, `node --check`, runnable script).

## Execution trigger & roles

DW execution roles live in `.claude/agents/`: `implementer`, `researcher`, `verifier`, `integrator`.

After human review of `.claude/active-task.md` and resolution of any Open Choice Points, trigger execution with:

```
Execute the Active Task Context in .claude/active-task.md using ultracode.
Read .claude/active-task.md first — the task list, constraints, and verification criteria are there.
Use the role-based agents defined in .claude/agents/.
```
