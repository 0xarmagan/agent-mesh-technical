#!/usr/bin/env python3
"""Write sim/out/report.md from M1 + M2. INTERNAL: model, not measurement.

  python3 sim/report.py            # refuses to write if M1 calibration is off tolerance
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m1_cost
import m2_security

HEADER = """> **INTERNAL — model, not measurement.** Do not quote any number from this file in external
> copy. M2 costs are illustrative units; only the binding component and ratios mean anything.
> Off-chain proving cost is not included. Source pin: `{pin}`{stale}
"""


def _stale(pin):
    clone = HERE.parent / "clones" / "eez-core-protocol"
    try:
        head = subprocess.run(["git", "-C", str(clone), "rev-parse", "--short", "origin/main"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return " (clone unavailable: pin unchecked)"
    return "" if head.startswith(pin) or pin.startswith(head) else f" — **STALE: upstream main is `{head}`; re-run the probe**"


def table(rows, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def main():
    p = m1_cost.load_params()
    m = m1_cost.CostModel(p)
    if not m.calibrated():
        sys.exit("M1 calibration outside ±5% — refusing to write report")
    pin = p["source_commit"]
    a, b, c, d = (round(x) for x in m.coef)
    worst = max(abs(r["rel"]) for r in m.residuals)

    md = ["# EEZ mechanism sim — M1 cost + M2 security", "", HEADER.format(pin=pin, stale=_stale(pin)), ""]
    md += ["## M1 — batch cost (gas, tx-level, steady state)", "",
           f"Fit: `gas = {a} + {b}·R + {c}·P + {d}·R·P` + P·(verify − mock); worst residual "
           f"{worst:.2%} over 9 measured shapes (R,P ∈ {{1,2,4}}). R=8 rows are extrapolated.", "",
           f"- Marginal atomic L1→L2 call: **{round(m.marginal_call_gas())} gas** "
           f"({round(m.marginal_post_gas())} post-side incl. {round(m.entry_calldata)} calldata gas for 832 bytes + "
           f"{round(m.execute_gas())} execute); with one callback {round(m.marginal_call_gas(True))}.",
           "- Basis: batch base is tx-level gas (incl. 21k intrinsic + calldata); per-entry and execute figures are "
           "contract-body gas (GasBreakdown) — the execute side excludes the caller's own 21k intrinsic, which the "
           "user pays for any L1 call. Post side cross-checked: measured tx-level gas per extra entry "
           f"{round(m.entry_check()[0])} vs model {round(m.entry_check()[1])}.",
           "- Full allocation (batch ÷ calls) below is an upper bound: it charges each rollup's own settlement to sync.",
           ""]
    md.append(table(m1_cost.sweep(m), ["verifier", "R", "P", "batch_base_gas", "base_per_rollup",
                                       "full_alloc_1call", "full_alloc_10calls"]))
    md += ["", "## M2 — security per rollup (illustrative units)", ""]
    rows = m2_security.per_rollup(p)
    for r in rows:
        r["margin"] = f"{r['margin']:.2f}"
    md.append(table(rows, ["rollup", "contract", "threshold", "effective_k", "ctc", "binding", "var", "margin", "safe_alone"]))
    md += ["", "## M2 — shared-component check", "",
           "Per-rollup safety is necessary, not sufficient: a shared key breaks every rollup that depends on it.", ""]
    srows = m2_security.shared_check(p)
    for r in srows:
        r["margin"] = f"{r['margin']:.2f}"
        r["breaks"] = ", ".join(r["breaks"])
    md.append(table(srows, ["attack_set", "cost", "breaks", "var_sum", "margin", "safe"]))
    out = HERE / "out" / "report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(md) + "\n")
    print(f"wrote {out.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
