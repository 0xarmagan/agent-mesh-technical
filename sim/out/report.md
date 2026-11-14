# EEZ mechanism sim — M1 cost + M2 security

> **INTERNAL — model, not measurement.** Do not quote any number from this file in external
> copy. M2 costs are illustrative units; only the binding component and ratios mean anything.
> Off-chain proving cost is not included. Source pin: `143d87e`


## M1 — batch cost (gas, tx-level, steady state)

Fit: `gas = 37347 + 27422·R + 8360·P + 5818·R·P` + P·(verify − mock); worst residual 0.12% over 9 measured shapes (R,P ∈ {1,2,4}). R=8 rows are extrapolated.

- Marginal atomic L1→L2 call: **109114 gas** (53808 post-side incl. 5080 calldata gas for 832 bytes + 55306 execute); with one callback 133894.
- Basis: batch base is tx-level gas (incl. 21k intrinsic + calldata); per-entry and execute figures are contract-body gas (GasBreakdown) — the execute side excludes the caller's own 21k intrinsic, which the user pays for any L1 call. Post side cross-checked: measured tx-level gas per extra entry 53821 vs model 53808.
- Full allocation (batch ÷ calls) below is an upper bound: it charges each rollup's own settlement to sync.

| verifier | R | P | batch_base_gas | base_per_rollup | full_alloc_1call | full_alloc_10calls |
|---|---|---|---|---|---|---|
| ecdsa | 1 | 1 | 82605 | 82605 | 191719 | 117374 |
| ecdsa | 1 | 2 | 100439 | 100439 | 209553 | 119158 |
| ecdsa | 1 | 4 | 136108 | 136108 | 245222 | 122725 |
| ecdsa | 2 | 1 | 115845 | 57923 | 224959 | 120699 |
| ecdsa | 2 | 2 | 139498 | 69749 | 248612 | 123064 |
| ecdsa | 2 | 4 | 186804 | 93402 | 295918 | 127794 |
| ecdsa | 4 | 1 | 182327 | 45582 | 291441 | 127347 |
| ecdsa | 4 | 2 | 217616 | 54404 | 326730 | 130876 |
| ecdsa | 4 | 4 | 288195 | 72049 | 397309 | 137934 |
| ecdsa | 8 | 1 | 315290 | 39411 | 424404 | 140643 |
| ecdsa | 8 | 2 | 373852 | 46732 | 482966 | 146499 |
| ecdsa | 8 | 4 | 490978 | 61372 | 600092 | 158212 |
| groth16 | 1 | 1 | 326414 | 326414 | 435528 | 141755 |
| groth16 | 1 | 2 | 588057 | 588057 | 697171 | 167920 |
| groth16 | 1 | 4 | 1111344 | 1111344 | 1220458 | 220248 |
| groth16 | 2 | 1 | 359654 | 179827 | 468768 | 145079 |
| groth16 | 2 | 2 | 627116 | 313558 | 736230 | 171826 |
| groth16 | 2 | 4 | 1162040 | 581020 | 1271154 | 225318 |
| groth16 | 4 | 1 | 426136 | 106534 | 535250 | 151728 |
| groth16 | 4 | 2 | 705234 | 176309 | 814348 | 179637 |
| groth16 | 4 | 4 | 1263431 | 315858 | 1372545 | 235457 |
| groth16 | 8 | 1 | 559099 | 69887 | 668213 | 165024 |
| groth16 | 8 | 2 | 861470 | 107684 | 970584 | 195261 |
| groth16 | 8 | 4 | 1466214 | 183277 | 1575328 | 255735 |

## M2 — security per rollup (illustrative units)

| rollup | contract | threshold | effective_k | ctc | binding | var | margin | safe_alone |
|---|---|---|---|---|---|---|---|---|
| zone_ref_1of1 | reference | 1 | 1 | 100 | 1 proof system(s) via ps_ecdsa_A | 400 | 0.25 | False |
| zone_ref_2of2 | reference | 2 | 2 | 200 | 2 proof system(s) via ps_ecdsa_A+ps_ecdsa_B | 400 | 0.50 | False |
| zone_ref_t0 | reference | 0 | 1 | 100 | 1 proof system(s) via ps_ecdsa_B | 100 | 1.00 | True |
| zone_zk_owner_timelocked | reference | 1 | 1 | 800 | 1 proof system(s) via ps_owner_C | 600 | 1.33 | True |
| zone_custom | custom | 1 | 1 | 50 | custom rollup-contract policy | 200 | 0.25 | False |

## M2 — shared-component check

Per-rollup safety is necessary, not sufficient: a shared key breaks every rollup that depends on it.

| attack_set | cost | breaks | var_sum | margin | safe |
|---|---|---|---|---|---|
| eez_upgrade_owner | 1000 | zone_custom, zone_ref_1of1, zone_ref_2of2, zone_ref_t0, zone_zk_owner_timelocked | 1700 | 0.59 | False |
| ps_ecdsa_A | 100 | zone_custom, zone_ref_1of1 | 600 | 0.17 | False |
| ps_ecdsa_A+ps_ecdsa_B | 200 | zone_custom, zone_ref_1of1, zone_ref_2of2, zone_ref_t0 | 1100 | 0.18 | False |
| ps_ecdsa_A+ps_owner_B | 250 | zone_custom, zone_ref_1of1, zone_ref_2of2, zone_ref_t0 | 1100 | 0.23 | False |
| ps_ecdsa_B | 100 | zone_ref_t0 | 100 | 1.00 | True |
| ps_ecdsa_B+ps_owner_A | 250 | zone_custom, zone_ref_1of1, zone_ref_2of2, zone_ref_t0 | 1100 | 0.23 | False |
| ps_owner_A | 150 | zone_custom, zone_ref_1of1 | 600 | 0.25 | False |
| ps_owner_A+ps_owner_B | 300 | zone_custom, zone_ref_1of1, zone_ref_2of2, zone_ref_t0 | 1100 | 0.27 | False |
| ps_owner_B | 150 | zone_ref_t0 | 100 | 1.50 | True |
| ps_owner_C | 800 | zone_zk_owner_timelocked | 600 | 1.33 | True |
| ps_zk_C | 5000 | zone_zk_owner_timelocked | 600 | 8.33 | True |

## M3 — posting game (one block, one sync opportunity; shares of V)

Illustrative ETH values (params `[m3]`). Race variants: pure Nash equilibria over OUT | (public/private, bind, bid grid); others closed form. Rules encoded: the proof binds every entry, so a copier executes the composer's entries and can only take a poster reward R paid to msg.sender (EEZ.sol:728-760); `gated` = today's single-signer ECDSA proving, `open` = assumed ZK.

- Open races cap entrants at 3 — duplicate-proving loss is a lower bound.
- Not modelled: same-block replay/supersede griefing, builder private order flow, endogenous V (M4).

| variant | proving | R/V | eq | entrants | composers | prover_operator | builder | zone | copier | gas | lost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V0_race_unbound | gated | 0.0 | 1 | [1] | 0.0 | 0.986 | 0.0 | 0.0 | 0.0 | 0.014 | 0.0 |
| V1_race_bound | gated | 0.0 | 2 | [1] | 0.0 | 0.986 | 0.0 | 0.0 | 0.0 | 0.014 | 0.0 |
| V2_auction | gated | 0.0 | closed form |  | 0.0 | 0.986 | 0.0 | -0.0 | 0.0 | 0.014 | 0.0 |
| V3_self_post | gated | 0.0 | closed form |  | 0.0 | 0.0 | 0.0 | 0.493 | 0.0 | 0.007 | 0.5 |
| V4_based | gated | 0.0 | closed form |  | 0.0 | 0.493 | 0.493 | -0.0 | 0.0 | 0.014 | 0.0 |
| V0_race_unbound | gated | 0.2 | 1 | [1] | 0.0 | 1.146 | 0.04 | -0.2 | 0.0 | 0.014 | 0.0 |
| V1_race_bound | gated | 0.2 | 1 | [1] | 0.0 | 1.186 | 0.0 | -0.2 | 0.0 | 0.014 | 0.0 |
| V2_auction | gated | 0.2 | closed form |  | 0.0 | 1.186 | 0.0 | -0.2 | 0.0 | 0.014 | 0.0 |
| V3_self_post | gated | 0.2 | closed form |  | 0.0 | 0.0 | 0.0 | 0.493 | 0.0 | 0.007 | 0.5 |
| V4_based | gated | 0.2 | closed form |  | 0.0 | 0.593 | 0.593 | -0.2 | 0.0 | 0.014 | 0.0 |
| V0_race_unbound | open | 0.0 | 1 | [3] | 0.02 | 0.0 | 0.701 | 0.0 | 0.0 | 0.038 | 0.24 |
| V1_race_bound | open | 0.0 | 8 | [3] | 0.02 | 0.0 | 0.701 | 0.0 | 0.0 | 0.038 | 0.24 |
| V2_auction | open | 0.0 | closed form |  | 0.0 | 0.0 | 0.0 | 0.882 | 0.0 | 0.038 | 0.08 |
| V3_self_post | open | 0.0 | closed form |  | 0.0 | 0.0 | 0.0 | 0.441 | 0.0 | 0.019 | 0.54 |
| V4_based | open | 0.0 | closed form |  | 0.0 | 0.0 | 0.882 | -0.0 | 0.0 | 0.038 | 0.08 |
| V0_race_unbound | open | 0.2 | 1 | [3] | 0.07 | 0.0 | 0.851 | -0.2 | 0.0 | 0.038 | 0.24 |
| V1_race_bound | open | 0.2 | 8 | [3] | 0.07 | 0.0 | 0.851 | -0.2 | 0.0 | 0.038 | 0.24 |
| V2_auction | open | 0.2 | closed form |  | 0.0 | 0.0 | 0.0 | 0.882 | 0.0 | 0.038 | 0.08 |
| V3_self_post | open | 0.2 | closed form |  | 0.0 | 0.0 | 0.0 | 0.441 | 0.0 | 0.019 | 0.54 |
| V4_based | open | 0.2 | closed form |  | 0.0 | 0.0 | 1.082 | -0.2 | 0.0 | 0.038 | 0.08 |
