# VERY HIGH Tier & Reframe Audit (Optional)

Load and follow this workflow **only** when a request is genuinely irreversible / protocol-wide (standard/spec change, security posture, irreversible deployment decision) or when the user explicitly requests Collaboration Mode, a deep coverage audit, or a reframe audit.

## Tier inheritance for reframes

A reframe/re-lens request ("explain this through OODA," "audit this differently") judged on its own surface reads as low-effort formatting and can under-score. If the material being reframed was originally analyzed at VERY HIGH, the reframe inherits VERY HIGH regardless of how simple the follow-up request sounds in isolation, so the reframe audit below fires.

## STEP 4g: Completeness pass

Dispatch `completeness-critic` (`.claude/agents/completeness-critic.md`) with:
- the raw situation, and
- a short "already covered" list distilled from `4a–4d` (include the Blind Spot cross-check so `4d` gaps and `4g` gaps don't duplicate).

Never pass the full synthesis or the experts' framing. Fold surviving gaps into **Unresolved Gaps** in the final output.

## STEP 4h: Reframe audit

Runs whenever a turn re-applies a different framework to material already synthesized in this session or a prior one (can trigger standalone without dispatching new experts).

Invoke `meta-advisor` (`.claude/agents/meta-advisor.md`) in **reframe-audit mode** before presenting the new pass. Report its verdict plainly if the new pass is mostly restatement — do not present relabeled findings as new insight.

## Reasoning audit (standard VERY HIGH)

After all experts return and synthesis (`4a–4e`) completes, invoke `meta-advisor` (`.claude/agents/meta-advisor.md`) to audit the synthesis reasoning before final output.

## Collaboration Mode output contract

Output sections:
- **CONVERGENT FINDINGS**
- **LOAD-BEARING TENSIONS (Choice Points)**
- **UNRESOLVED GAPS**
- **BINDING LOGIC**
- **ROBUST MOVE**
