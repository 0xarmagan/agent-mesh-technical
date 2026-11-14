#!/usr/bin/env python3
"""Tests for the mechanism sim: python3 sim/test_sim.py"""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m1_cost
import m2_security

P = m1_cost.load_params()


class M1(unittest.TestCase):
    def setUp(self):
        self.m = m1_cost.CostModel(P)

    def test_in_sample_within_tolerance(self):
        self.assertTrue(self.m.calibrated(), self.m.residuals)

    def test_leave_one_out_within_tolerance(self):
        pts = json.loads((HERE / P["m1"]["calibration"]["file"]).read_text())["points"]
        for i, held in enumerate(pts):
            coef, _ = m1_cost.fit(pts[:i] + pts[i + 1:])
            a, b, c, d = coef
            pred = a + b * held["R"] + c * held["P"] + d * held["R"] * held["P"]
            self.assertLess(abs(pred - held["gas"]) / held["gas"], m1_cost.TOLERANCE, held)

    def test_verifier_substitution_scales_with_P(self):
        d1 = self.m.batch_base_gas(2, 1, "ecdsa") - self.m.batch_base_gas(2, 1, "mock")
        d3 = self.m.batch_base_gas(2, 3, "ecdsa") - self.m.batch_base_gas(2, 3, "mock")
        self.assertAlmostEqual(d1, 6191 - 2535)
        self.assertAlmostEqual(d3, 3 * (6191 - 2535))

    def test_sharing_a_PS_amortises(self):
        per_rollup = [self.m.batch_base_gas(R, 1) / R for R in (1, 2, 4, 8)]
        self.assertEqual(per_rollup, sorted(per_rollup, reverse=True))

    def test_entry_post_side_matches_tx_level_measurement(self):
        measured, model = self.m.entry_check()
        self.assertLess(abs(model - measured) / measured, 0.01, (measured, model))

    def test_entry_calldata_bytes_are_linear(self):
        pts = self.m.entry_points
        per = [(b["calldata_bytes"] - a["calldata_bytes"]) / (b["n"] - a["n"]) for a, b in zip(pts, pts[1:])]
        self.assertEqual(per, [832, 832])

    def test_full_allocation_is_upper_bound(self):
        self.assertGreater(self.m.full_alloc_call_gas(1, 1, 1), self.m.marginal_call_gas())
        self.assertGreater(self.m.full_alloc_call_gas(1, 1, 1), self.m.full_alloc_call_gas(1, 1, 10))


def _params_with(rollups, components=None):
    p = copy.deepcopy(P)
    p["m2"]["rollup"] = rollups
    if components is not None:
        p["m2"]["component"] = components
    return p


BASE_COMPS = [
    {"id": "eez_upgrade_owner", "cost": 10_000, "shared": True},
    {"id": "psA", "cost": 100, "owner": "ownA", "shared": True},
    {"id": "ownA", "cost": 1_000, "shared": True},
]


def _rollup(**kw):
    r = {"id": "z", "contract": "reference", "threshold": 1, "proof_systems": ["psA"],
         "owner_cost": 5_000, "proxy_admin_cost": 5_000, "var": 50}
    r.update(kw)
    return r


class M2(unittest.TestCase):
    def test_threshold_zero_behaves_as_one(self):
        row = m2_security.per_rollup(_params_with([_rollup(threshold=0)], BASE_COMPS))[0]
        self.assertEqual(row["effective_k"], 1)
        self.assertEqual(row["ctc"], 100)

    def test_owner_key_below_threshold_binds(self):
        row = m2_security.per_rollup(_params_with([_rollup(owner_cost=20)], BASE_COMPS))[0]
        self.assertEqual(row["ctc"], 20)
        self.assertIn("owner", row["binding"])

    def test_ps_owner_cheaper_than_key_binds(self):
        comps = [dict(c) for c in BASE_COMPS]
        comps[1]["cost"] = 9_000
        row = m2_security.per_rollup(_params_with([_rollup()], comps))[0]
        self.assertEqual(row["ctc"], 1_000)

    def test_custom_contract_policy_counts(self):
        row = m2_security.per_rollup(_params_with([_rollup(contract="custom", code_cost=7)], BASE_COMPS))[0]
        self.assertEqual(row["ctc"], 7)

    def test_locked_rollup_has_no_ps_path(self):
        row = m2_security.per_rollup(_params_with([_rollup(threshold=3)], BASE_COMPS))[0]
        self.assertNotIn("proof system", row["binding"])

    def test_shared_ps_sums_var(self):
        rs = [_rollup(id="z1", var=80), _rollup(id="z2", var=80)]
        p = _params_with(rs, BASE_COMPS)
        alone = m2_security.per_rollup(p)
        self.assertTrue(all(r["safe_alone"] for r in alone))           # 100 ≥ 80 each
        shared = {r["attack_set"]: r for r in m2_security.shared_check(p)}
        self.assertEqual(shared["psA"]["breaks"], ["z1", "z2"])
        self.assertFalse(shared["psA"]["safe"])                         # 100 < 160


if __name__ == "__main__":
    unittest.main(verbosity=1)
