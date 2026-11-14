#!/usr/bin/env python3
"""M2 — EEZ security model (analytic table). INTERNAL: model, not measurement.

Spec §3. Costs are illustrative units; only the binding component and the ratios mean anything.

Per rollup r, minimal attack sets:
  {owner_r}, {proxy_admin_r}, {eez_upgrade_owner}, {code_r} (custom contract only),
  and every choice of k_r = max(threshold, 1) listed proof systems, each attacked via its
  key OR its owner (ECDSAProofSystem.setSigner).
  CtC_r = min cost over those sets.           per rollup:  CtC_r ≥ VaR_r  (necessary)
Shared check: for every attack set S made only of shared components, the attacker breaks
  every rollup that has some attack set ⊆ S, so require cost(S) ≥ Σ VaR(broken by S).
Limitation: unions of distinct minimal sets are not enumerated.
"""
from itertools import combinations, product

from m1_cost import load_params


def _components(params):
    return {c["id"]: c for c in params["m2"]["component"]}


def attack_sets(rollup, comps):
    """Yield (frozenset of component ids, cost, label). Per-rollup keys are pseudo-components."""
    rid = rollup["id"]
    yield frozenset({f"{rid}:owner"}), rollup["owner_cost"], "owner (setRoot/threshold/vkeys)"
    yield frozenset({f"{rid}:proxy_admin"}), rollup["proxy_admin_cost"], "rollup proxy admin"
    eez = comps["eez_upgrade_owner"]
    yield frozenset({"eez_upgrade_owner"}), eez["cost"], "EEZ upgrade owner"
    if rollup.get("contract") == "custom":
        yield frozenset({f"{rid}:code"}), rollup["code_cost"], "custom rollup-contract policy"
    k = max(rollup["threshold"], 1)
    pss = rollup["proof_systems"]
    if k > len(pss):
        return  # rollup locked: threshold unreachable
    for combo in combinations(pss, k):
        options = [[ps] + ([comps[ps]["owner"]] if comps[ps].get("owner") else []) for ps in combo]
        for pick in product(*options):
            s = frozenset(pick)
            yield s, sum(comps[c]["cost"] for c in s), f"{k} proof system(s) via " + "+".join(sorted(s))


def per_rollup(params):
    comps = _components(params)
    rows = []
    for r in params["m2"]["rollup"]:
        sets = list(attack_sets(r, comps))
        s, cost, label = min(sets, key=lambda t: t[1])
        rows.append({"rollup": r["id"], "contract": r.get("contract", "reference"),
                     "threshold": r["threshold"], "effective_k": max(r["threshold"], 1),
                     "ctc": cost, "binding": label, "var": r["var"],
                     "margin": cost / r["var"], "safe_alone": cost >= r["var"]})
    return rows


def shared_check(params):
    comps = _components(params)
    rollups = params["m2"]["rollup"]
    sets_by_rollup = {r["id"]: [s for s, _, _ in attack_sets(r, comps)] for r in rollups}
    shared_ids = {cid for cid, c in comps.items() if c.get("shared")}
    candidates = {s for sets in sets_by_rollup.values() for s in sets if s <= shared_ids}
    var = {r["id"]: r["var"] for r in rollups}
    rows = []
    for s in sorted(candidates, key=lambda x: sorted(x)):
        broken = sorted(rid for rid, sets in sets_by_rollup.items() if any(a <= s for a in sets))
        cost = sum(comps[c]["cost"] for c in s)
        total = sum(var[b] for b in broken)
        rows.append({"attack_set": "+".join(sorted(s)), "cost": cost, "breaks": broken,
                     "var_sum": total, "margin": cost / total if total else float("inf"),
                     "safe": cost >= total})
    return rows


if __name__ == "__main__":
    p = load_params()
    for r in per_rollup(p):
        print(r)
    for r in shared_check(p):
        print(r)
