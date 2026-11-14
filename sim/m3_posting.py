#!/usr/bin/env python3
"""M3 — posting game: who posts in block N and who captures the value. INTERNAL: model, not measurement.

Spec §4. One L1 block, one sync opportunity worth V to the party whose entries execute.

Source rules encoded (eez-core-protocol @143d87e):
  - The proof binds every entry (beneficiaries, currentRoot pins) — EEZ.sol:728-760. A copier who
    re-posts a batch executes the ORIGINAL composer's entries: V still goes to the composer.
  - msg.sender is bound only if bindMsgSenderInPublicInput (EEZ.sol:760). So a copier can only take
    a poster reward R that an off-protocol design pays to msg.sender.
  - Only one IProofSystem exists, single-signer ECDSA (ECDSAProofSystem.sol:67-69): "gated"
    proving means the signer's operator is the only possible composer. "open" assumes ZK.

Race variants (V0, V1) are solved by enumerating pure-strategy Nash equilibria over
  strategy = OUT | (channel ∈ {public, private}, bind ∈ {0,1}, bid ∈ grid)
Other variants (V2–V4) use closed forms. Payoff shares are reported per party.
"""
from itertools import product

from m1_cost import CostModel, load_params

PARTIES = ["composers", "prover_operator", "builder", "zone", "copier", "gas", "lost"]
OUT = ("out",)


def setting(params, proving, reward):
    m3, model = params["m3"], CostModel(params)
    ver = m3["verifier"][proving]
    gas = model.batch_base_gas(m3["rollups_in_batch"], m3["proof_systems"], ver) + model.marginal_post_gas()
    g = gas * m3["gas_price_gwei"] * 1e-9
    return {"V": m3["value"], "R": reward, "g": g, "prove": m3["prove_cost"][proving],
            "g_copy": g * m3["copier_gas_multiplier"], "public_losers_pay": m3["public_losers_pay_gas"],
            "private_cost": m3["private_channel_cost"]}


def max_surplus(s):
    return s["V"] + s["R"] - s["g"] - s["prove"]


def race_payoffs(profile, s, grid, bind_allowed):
    """Return (per-composer payoffs, party split dict) for one strategy profile."""
    n = len(profile)
    pay = [0.0] * n
    split = dict.fromkeys(PARTIES, 0.0)
    S = max_surplus(s)
    entrants = [i for i, st in enumerate(profile) if st != OUT]
    if not entrants:
        split["lost"] += s["V"]
        return pay, split
    bids = {i: grid[profile[i][2]] * max(S, 0.0) for i in entrants}
    top = max(bids.values())
    winners = [i for i in entrants if bids[i] == top]
    w = 1.0 / len(winners)                       # ties: equal-probability lottery
    for i in entrants:
        channel, bind, _ = profile[i]
        bind = bind if bind_allowed else 0
        pay[i] -= s["prove"]
        split["lost"] += s["prove"]              # proving resources burned
        win_p = w if i in winners else 0.0
        lose_p = 1.0 - win_p
        if lose_p and channel == "public" and s["public_losers_pay"]:
            pay[i] -= lose_p * s["g"]
            split["gas"] += lose_p * s["g"]      # reverted public tx still pays gas
        if not win_p:
            continue
        # Copier: front-runs a public, unbound winner if R covers its gas + outbidding the composer.
        copier_bid = bids[i] + 1e-12
        copied = (channel == "public" and not bind and s["R"] > 0 and s["R"] - s["g_copy"] - copier_bid > 0)
        if copied:
            pay[i] += win_p * s["V"]                       # entries still pay V to the composer
            split["composers"] += win_p * s["V"]
            split["copier"] += win_p * (s["R"] - s["g_copy"] - copier_bid)
            split["builder"] += win_p * copier_bid
            split["gas"] += win_p * s["g_copy"]
            split["zone"] -= win_p * s["R"]
        else:
            priv = s["private_cost"] if channel == "private" else 0.0
            gain = s["V"] + s["R"] - s["g"] - bids[i] - priv
            pay[i] += win_p * gain
            split["composers"] += win_p * gain
            split["builder"] += win_p * (bids[i] + priv)
            split["gas"] += win_p * s["g"]
            split["zone"] -= win_p * s["R"]
    split["composers"] -= s["prove"] * len(entrants)  # composers bear proving; the work itself is lost
    return pay, split


def strategies(grid, bind_allowed):
    binds = (0, 1) if bind_allowed else (0,)
    return [OUT] + [(c, b, k) for c in ("public", "private") for b in binds for k in range(len(grid))]


def pure_nash(n, s, grid, bind_allowed):
    strats = strategies(grid, bind_allowed)
    eq = []
    for prof in product(strats, repeat=n):
        pay, split = race_payoffs(prof, s, grid, bind_allowed)
        stable = True
        for i in range(n):
            for alt in strats:
                if alt == prof[i]:
                    continue
                dev = list(prof)
                dev[i] = alt
                if race_payoffs(tuple(dev), s, grid, bind_allowed)[0][i] > pay[i] + 1e-12:
                    stable = False
                    break
            if not stable:
                break
        if stable:
            eq.append((prof, pay, split))
    return eq


def _honest(eq, s):
    """True if no equilibrium leaves a public, unbound winner exposed to a profitable copy."""
    if s["R"] <= 0:
        return True
    for prof, _, _ in eq:
        for st in prof:
            if st != OUT and st[0] == "public" and st[1] == 0:
                return False
    return True


def _norm(split, V):
    return {k: round(v / V, 3) for k, v in split.items()}


def race(params, proving, reward, bind_allowed):
    s = setting(params, proving, reward)
    grid = params["m3"]["bid_grid"]
    n = 1 if proving == "gated" else params["m3"]["max_composers"]
    eq = pure_nash(n, s, grid, bind_allowed)
    if not eq:
        return {"equilibria": 0}
    # report the equilibrium most favourable to composers and the least (range)
    splits = [e[2] for e in eq]
    best = max(splits, key=lambda d: d["composers"])
    worst = min(splits, key=lambda d: d["composers"])
    out = {"equilibria": len(eq), "honest_br": _honest(eq, s),
           "split_best": _norm(best, s["V"]), "split_worst": _norm(worst, s["V"]),
           "entrants": sorted({sum(st != OUT for st in e[0]) for e in eq})}
    if proving == "gated":  # the only composer is the signer's operator
        for d in (out["split_best"], out["split_worst"]):
            d["prover_operator"], d["composers"] = d["composers"], 0.0
    return out


def closed_forms(params, proving, reward):
    """V2 auction, V3 self-post, V4 based. Shares of V."""
    m3 = params["m3"]
    s = setting(params, proving, reward)
    V, S = s["V"], max_surplus(s)
    z = lambda **kw: {p: round(kw.get(p, 0.0) / V, 3) for p in PARTIES}
    holder = "prover_operator" if proving == "gated" else "composers"
    # V2: exclusive slot sold before the block; competitive common-value bids → price ≈ S.
    v2 = z(zone=S - reward, gas=s["g"], lost=s["prove"]) if proving == "open" else \
        z(**{holder: S, "gas": s["g"], "zone": -reward, "lost": s["prove"]})  # gated: one bidder, price 0
    # V3: each rollup self-posts; cross-rollup opportunities cannot be captured (EEZ.sol:581).
    x = m3["cross_rollup_share"]
    # the zone is its own poster, so any poster reward R is an internal transfer
    v3 = z(zone=(1 - x) * (V - s["g"] - s["prove"]), gas=(1 - x) * s["g"], lost=x * V + (1 - x) * s["prove"])
    # V4: L1 builder is the composer. Open proving: builder keeps everything. Gated: buys the signature.
    if proving == "open":
        v4 = z(builder=V + reward - s["prove"] - s["g"], gas=s["g"], zone=-reward, lost=s["prove"])
    else:
        b = m3["based_bargain_share"]
        net = V + reward - s["prove"] - s["g"]
        v4 = z(builder=b * net, prover_operator=(1 - b) * net, gas=s["g"], zone=-reward, lost=s["prove"])
    return {"V2_auction": v2, "V3_self_post": v3, "V4_based": v4}


def run(params):
    rows = []
    for proving in ("gated", "open"):
        for reward in params["m3"]["poster_reward"]:
            for name, bind_allowed in (("V0_race_unbound", False), ("V1_race_bound", True)):
                r = race(params, proving, reward, bind_allowed)
                rows.append({"variant": name, "proving": proving, "R": reward, **r})
            for name, split in closed_forms(params, proving, reward).items():
                rows.append({"variant": name, "proving": proving, "R": reward, "equilibria": "closed form",
                             "honest_br": None, "split_best": split, "split_worst": split, "entrants": None})
    return rows


if __name__ == "__main__":
    for r in run(load_params()):
        print(r["variant"], r["proving"], r["R"], r["equilibria"], r.get("honest_br"), r.get("entrants"))
        print("   best ", r.get("split_best"))
        print("   worst", r.get("split_worst"))
