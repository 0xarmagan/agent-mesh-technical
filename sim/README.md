# sim/ — EEZ mechanism simulation (M1 cost, M2 security, M3 posting game)

INTERNAL. Model, not measurement. Spec: `docs/superpowers/specs/2026-11-14-eez-mechanism-simulation-design.md`.

```
python3 sim/test_sim.py     # 20 tests: calibration (in-sample + leave-one-out ±5%), model + game invariants
python3 sim/report.py       # writes sim/out/report.md; refuses if calibration is off
```

- `params.toml` — every value tagged `code@sha`, `measured@sha` or `assumed`.
- `calibration/empty_batch_RxP.json` — tx-level gas of steady empty batches, R,P ∈ {1,2,4}.
- `probes/SimProbe.t.sol` — the Foundry probe that produced it. Re-run after an upstream change:
  copy the clone (`rsync -a --exclude .git clones/eez-core-protocol/ <tmp>/`), drop the probe into
  `<tmp>/test/`, run `forge test --match-path test/SimProbe.t.sol --isolate -vv`
  (forge lives in `~/.foundry/bin`), then update the JSON and `source_commit`.
- Per-unit gas comes from upstream `GasBreakdown`/`GasExecPaths` (`forge test --isolate --json`).

- `calibration/deferred_entry_calldata.json` + `probes/SimCalldataProbe.t.sol` — calldata bytes and
  tx-level gas per deferred entry with one L1→L2 record (832 B; 53,821 gas/entry).

Known gaps: calldata measured for one entry shape only (no L2→L1 calls, no return data); off-chain proving cost excluded; M2 costs illustrative;
M2 does not enumerate unions of distinct minimal attack sets. M3: illustrative ETH values, entrants
capped at 3, private-channel cost assumed, replay/supersede griefing and endogenous V not modelled. M4 not built.
