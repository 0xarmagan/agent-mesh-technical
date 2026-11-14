#!/usr/bin/env python3
"""M1 — EEZ batch cost model (analytic, calibrated). INTERNAL: model, not measurement.

Spec: docs/superpowers/specs/2026-11-14-eez-mechanism-simulation-design.md §2.

batch_gas(R, P, verifier) = a + b·R + c·P + d·R·P + P·(verify[verifier] − verify[mock])
  fitted on tx-level steady-state empty batches where every rollup lists all P proof
  systems (so d·R·P is the Σ|I_r|·c_vk term). Entries add measured per-unit body gas
  plus calldata (assumed bytes × 16).

Marginal cost per atomic L1→L2 call = post-side unit gas + calldata + execute-side gas.
Full allocation (whole batch ÷ N) is reported only as an upper bound.
Off-chain proving cost is NOT included.
"""
import json
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOLERANCE = 0.05


def load_params(path=HERE / "params.toml"):
    with open(path, "rb") as f:
        return tomllib.load(f)


def _solve(A, y):
    """Least squares via normal equations + Gaussian elimination (stdlib only)."""
    n = len(A[0])
    M = [[sum(r[i] * r[j] for r in A) for j in range(n)] for i in range(n)]
    v = [sum(r[i] * yy for r, yy in zip(A, y)) for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv], v[col], v[piv] = M[piv], M[col], v[piv], v[col]
        for r in range(n):
            if r != col and M[r][col]:
                f = M[r][col] / M[col][col]
                M[r] = [a - f * b for a, b in zip(M[r], M[col])]
                v[r] -= f * v[col]
    return [v[i] / M[i][i] for i in range(n)]


def fit(points):
    """Return (coeffs a,b,c,d) and per-point relative residuals."""
    A = [[1, p["R"], p["P"], p["R"] * p["P"]] for p in points]
    y = [p["gas"] for p in points]
    coef = _solve(A, y)
    resid = []
    for row, p in zip(A, points):
        pred = sum(c * x for c, x in zip(coef, row))
        resid.append({"R": p["R"], "P": p["P"], "gas": p["gas"], "pred": round(pred), "rel": (pred - p["gas"]) / p["gas"]})
    return coef, resid


class CostModel:
    def __init__(self, params):
        self.p = params
        cal = json.loads((HERE / params["m1"]["calibration"]["file"]).read_text())
        self.coef, self.residuals = fit(cal["points"])
        self.verify = {k: v["gas"] for k, v in params["m1"]["verify"].items()}
        self.unit = {k: v["gas"] for k, v in params["m1"]["unit_gas"].items()}
        cd = params["m1"]["calldata"]
        self.entry_calldata = (cd["zero_bytes_per_entry"]["value"] * cd["gas_per_zero_byte"]["value"]
                               + cd["nonzero_bytes_per_entry"]["value"] * cd["gas_per_nonzero_byte"]["value"])
        self.entry_points = json.loads((HERE / cd["file"]).read_text())["points"]

    def entry_check(self):
        """Measured tx-level gas per extra entry vs model (body units + calldata)."""
        a, b = self.entry_points[0], self.entry_points[-1]
        measured = (b["tx_gas"] - a["tx_gas"]) / (b["n"] - a["n"])
        return measured, self.marginal_post_gas()

    def calibrated(self):
        return all(abs(r["rel"]) <= TOLERANCE for r in self.residuals)

    def batch_base_gas(self, R, P, verifier="ecdsa"):
        a, b, c, d = self.coef
        return a + b * R + c * P + d * R * P + P * (self.verify[verifier] - self.verify["mock"])

    def marginal_post_gas(self, callback=False):
        """Post-side gas of one more deferred entry carrying one L1→L2 record."""
        return self.unit["deferred_entry"] + self.unit["l1_to_l2_record"] + self.entry_calldata

    def execute_gas(self, callback=False):
        return self.unit["execute_l1_to_l2"] + (self.unit["first_callback"] if callback else 0)

    def marginal_call_gas(self, callback=False):
        return self.marginal_post_gas(callback) + self.execute_gas(callback)

    def full_alloc_call_gas(self, R, P, n_calls, verifier="ecdsa", callback=False):
        """Upper bound: charges the whole batch (incl. the rollups' own settlement) to sync calls."""
        return self.batch_base_gas(R, P, verifier) / n_calls + self.marginal_call_gas(callback)


def sweep(model):
    s = model.p["m1"]["sweep"]
    rows = []
    for ver in s["verifier"]:
        for R in s["rollups"]:
            for P in s["proof_systems"]:
                rows.append({
                    "verifier": ver, "R": R, "P": P,
                    "batch_base_gas": round(model.batch_base_gas(R, P, ver)),
                    "base_per_rollup": round(model.batch_base_gas(R, P, ver) / R),
                    "full_alloc_1call": round(model.full_alloc_call_gas(R, P, 1, ver)),
                    "full_alloc_10calls": round(model.full_alloc_call_gas(R, P, 10, ver)),
                })
    return rows


def to_eth(gas, gwei):
    return gas * gwei * 1e-9


if __name__ == "__main__":
    m = CostModel(load_params())
    print("coef a,b,c,d =", [round(x) for x in m.coef], "calibrated:", m.calibrated())
    print("marginal atomic call gas:", round(m.marginal_call_gas()), "with callback:", round(m.marginal_call_gas(True)))
