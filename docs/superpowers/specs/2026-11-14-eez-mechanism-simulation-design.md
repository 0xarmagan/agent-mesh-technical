---
source-commit: 143d87e
status: design (no code, no data yet)
visibility: internal
---

# EEZ mechanism simulation — design

> **Internal. Model, not measurement.** No output of this framework may appear in external
> copy as a number about EEZ cost, revenue or security. Run claim-lint on anything derived.

## 0. Ground truth the model must respect (@143d87e)

| Fact | Evidence | Consequence for the model |
|---|---|---|
| No fee or revenue logic in the core contracts | `grep -rli fee src/EEZ.sol src/L2 src/base src/rollupContract src/proofSystems` → none (periphery mocks / `Bridge.sol:28` only); only ETH delta accounting `EEZ.sol:1032` | Every fee, auction or revenue share is a **variant**, never a baseline |
| Posting is permissionless; gated only by proofs | `postAndVerifyBatch` `EEZ.sol:371`; `registerRollup` `EEZ.sol:344-355` | "Composer" is an off-chain role; anyone can post |
| Sync is binary per L1 block | `_requireVerifiedThisBlock` `EEZ.sol:1578-1580` | Time step = one L1 block; inclusion is the critical event |
| The L1 binding is chosen per batch: none (0), exact current block (`uint64.max`), or a past block ≤256 old (reference Rollup) | `Rollup.sol:178-195`; `EEZ.sol:748` | Binding mode is a parameter; in exact-block mode a missed block means a lost proof |
| One failing PS reverts the whole batch | `EEZ.sol:787-788` | Liveness is coupled across rollups |
| Same-block re-verify resets the queue | `EEZ.sol:802-811` | Supersede is a griefing/liveness vector |
| `immediateEntryCount` not covered by the proof; sender binding optional | `EEZ.sol:642-650`, `:760` | Copier / front-runner actor is real |
| Poster can starve a target call → skipped | `EEZ.sol:252-255`, `:429` | Censorship-by-gas actor |
| Threshold any value; 0 behaves like 1 in the reference Rollup | `Rollup.sol:249-251`; ≥1 PS index `EEZ.sol:553`; nonzero vkey `Rollup.sol:162` | Threshold is not the security floor (see §3) |
| Owner `setRoot` bypasses all proofs (not in a verified block, not during execution) | `Rollup.sol:258-268`; `EEZ.sol:1544-1552` | Owner key is the cheapest attack path |
| Threshold, PS membership, vkeys, setRoot gating and timelocks are **rollup-contract policy**; EEZ only checks the returned vkey array length | `EEZ.sol:684-689`; reference `Rollup.sol:151,162,265` | M2 rows hold per rollup-contract implementation; for a non-reference contract CtC_r ≤ C_code_r |
| Only proof system = ECDSA single-signer | `ECDSAProofSystem.sol:51,67-69` | ZK cost/latency inputs model a system that does not exist yet |
| EEZ runtime 23,942 / 24,576 B | `src/TODO.md` "Bytecode" | On-chain fee logic needs a periphery contract or upgrade |
| Flow will change | `EEZ.sol:30-32` | Every code behaviour above is a **parameter**, pinned to a commit |

## 1. Architecture

```
params/  (YAML, each value tagged: source=code@sha | measured@date | assumed)
   │
   ▼
M1 Cost model (analytic) ─────┐
M2 Security model (analytic) ─┼─► M4 Block simulator (Monte Carlo + agents) ─► reports/
M3 Posting game (equilibrium)─┘         ▲
                                  scenario variants (V0–V4)
```

Python, stdlib + numpy/pandas. Deterministic seeds. Each run writes its param file, commit pin
and seed next to the output. `check_wiki_drift.py`-style guard: if `source-commit` ≠ upstream
main, the run prints which code-derived params may be stale.

## 2. M1 — Cost model (analytic, build first)

Per batch with R rollups, P distinct proof systems, E entries:

```
gas = base + Σ_r (c_cd + c_mark + |I_r|·c_vk) + P·(c_call + c_verify)
      + Σ_E (hash + exec_gas) + queued_SSTORE(E_queued) + calldata/blob
off-chain = Σ_{ps} prove_cost(ps, R, E)         # one proof per PS, shared by all R
marginal cost per atomic call =
      (cost(batch) − cost(batch without cross-chain entries)) / N_xcalls
```

- Vkey reads scale with Σ|I_r| (`Rollup.sol:158-165`); the per-PS fold is P×R (`EEZ.sol:770-783`);
  every listed PS is verified, used or not (`EEZ.sol:767-769`).
- Key structural fact: verification cost is shared across R; **P dominates only when
  c_verify ≫ |I_r|·c_vk** (ZK, not ECDSA). Cost does not scale with Σ thresholds.
- Full allocation (whole batch ÷ N_xcalls) is an upper bound only — it charges the rollup's own
  settlement to sync.
- Calibrate coefficients from `test/Gas{Breakdown,ExecPaths,L2,Cost}.t.sol` (Foundry gas reports).
- `c_verify` is a parameter sweep: ECDSA ~6–8k incl. cold call (measure from GasBreakdown),
  Groth16 ~250k, STARK 1M+ (assumed, label as such).
- **Output:** marginal cost per atomic call vs (R, P, E, gas price, p_sync), where
  p_sync = share of L1 blocks with any sync activity. No forecasts.

## 3. M2 — Security model (analytic table)

```
CtC_r = min( C_owner_r,            # setRoot, setThreshold, add/remove PS, rotate vkey — no timelock
                                   #   in the reference contract (Rollup.sol:225-268); deployment-dependent
             C_proxyAdmin_r,
             C_code_r,             # non-reference IRollupContract: its own policy (EEZ.sol:684-689)
             C_EEZ_upgradeOwner,   # EEZProxy.sol:9-14
             Σ_{cheapest max(t_r,1)} min(C_PS_i, C_PSowner_i) )   # t_r=0 still needs ≥1 PS (EEZ.sol:553)
per rollup:  CtC_r ≥ VaR_r         # VaR = value in rollup + value reachable via atomic calls
shared:      for each shared component c (PS key, PS owner, EEZ/EEZL2 upgradeOwner):
             safe ⇔ C_c ≥ Σ_{r : c ∈ cut_r} VaR_r
coupled: CtC_{A∧B} = min(CtC_A, CtC_B)   if A's circuit trusts B's returnData (flag; not on-chain)
```

- Per-rollup CtC_r ≥ VaR_r is **necessary, not sufficient**: one proof per PS covers every rollup
  that selects it (`EEZ.sol:770-787`), so shared components must cover the summed VaR.
- Report per rollup-contract implementation and config, with sensitivity on each C term. Independence of ECDSA signers is an
  explicit boolean (same operator ⇒ k signers count as 1).
- **Guardrail:** the optimiser may never minimise cost without this constraint, otherwise it
  recommends threshold 0/ECDSA every time.

## 4. M3 — Posting game (who posts in block N, who captures value)

Actors (all code-permitted): poster/composer, copier (no `bindMsgSender`), griefer (supersede,
gas-starve), L1 builder (include/drop; private order flow), rollup owner (setRoot, threshold),
arbitrageur, zone sequencer.

Variants (all off-protocol):

| ID | Mechanism |
|---|---|
| V0 | Open race, no sender binding (today's default risk) |
| V1 | Open race + `bindMsgSender` |
| V2 | Composer slot auction / exclusivity |
| V3 | Each rollup self-posts: L1↔own-rollup sync only. A↔B atomic calls still need one joint batch (`EEZ.sol:581`; a later same-block batch replaces the queue, `:804-811`), so a joint composer and one shared proof per PS are required |
| V4 | Based: L1 builder is composer |

Method: solve small equilibria analytically (2–3 composers, 1–2 builders) for "is honest posting
a best response?" and "who captures atomic arb?"; feed the rules into M4. Supersede griefing
needs a valid proof, which a copier obtains from an unbound (V0) batch.

## 5. M4 — Block simulator (Monte Carlo + agent-based)

Step = L1 block. Per block: sample gas/blob price, sync demand, arb gaps, proof latency per PS,
builder inclusion; agents act per variant; apply code rules (atomic revert, supersede, starvation
skip, L1 binding mode incl. exact-block loss, one-block entry lifetime).

**Outputs:** revenue split (composer / builder / zone / user), P(batch revert), proofs invalidated
by missed inclusion, censorship probability, griefing cost ÷ victim loss, posting/building HHI,
share of batches lost to supersede, cost per atomic call distribution.

## 6. Partner model (only where it decides something)

- **Rollup partners (e.g. Linea):**
  `ΔU = B·p_sync·[N_x·(fee_x + MEV_x) − ΔC_L1 − ΔC_proof] − C_int/T − λ·lost_local_ordering − σ·sovereignty`
  per period T, where B = L1 blocks per T, ΔC = cost above the rollup's own settlement, and
  fee_x = 0 outside V2+. Decision it serves: does sync-lane value exceed proof + L1 cost at the chosen security level?
- **App/infra partners (Soda, Colibri, ETHGas, Tenderly):** not joiners. Model as demand terms
  driven by M4 traffic (preconf demand, RPC root checks, sync calls, traces per entry). No ΔU.
- **Not simulated (qualitative suffices):** permissionless registration, sovereignty knobs,
  revenue-share negotiation without an on-chain hook.

## 7. Data plan

| Phase | Data | Runs |
|---|---|---|
| P0 now | Foundry gas tests, public gas/blob series, assumed proof costs | M1 + M2 tables; marginal cost-per-call curves |
| P1 testnet | Chiado traces: composer fill rate, rollback rate, bundle drops (**internal-only**) | Calibrate M4 inclusion + revert |
| P2 mainnet | N_xcalls distribution, real arb gaps, builder shares, fee elasticity, Linea counterfactual | Full M3/M4; partner ΔU |

## 8. Validation

1. M1 reproduces Foundry gas within ±5% on the test fixtures before any sweep.
2. Back-test M4 against P1 traces (revert + inclusion rates) before trusting P2 runs.
3. Each variant ships a "what would make this wrong" note; adversarial review by security-auditor.
4. Re-run M1/M2 whenever `check_wiki_drift.py` reports CHANGED on cited lines.

## 9. Known ways this misleads

1. **Threshold as security parameter** — owner/admin keys sit below it; overstates security.
2. **ZK inputs on an ECDSA system** — models a prover set that does not exist.
3. **Arb volume fitted from async bridges** — atomic composability makes it endogenous; understates.
4. **Missing private order flow / builder–composer integration** — open race looks competitive, centralises in reality.
5. **Fee variants read as protocol revenue** — none exists in code.
6. **Numbers leaking externally** — gated; header on every output.

## 10. Recommended first build

M1 + M2 only (P0): one script, one param file, two tables, calibrated against the Foundry gas
tests. It answers the decisions available today — recommended default security config (per
rollup-contract implementation, with the shared-component check) and marginal cost per atomic
call vs (R, P, E, gas price); break-even only against an explicit, labelled willingness-to-pay
parameter — without inventing a fee market.
