// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {console} from "forge-std/Test.sol";
import {GasFixture} from "./GasFixture.t.sol";
import {EEZ, ProofSystemBatchPerVerificationEntries} from "../src/EEZ.sol";
import {ExecutionEntry} from "../src/interfaces/IEEZ.sol";

/// @notice Scratch probe for mechanism-sim M1 (not upstream). Per deferred entry carrying one
///         L1→L2 record (same shape as bench.post.deferred + extra_l1_to_l2_record):
///         calldata bytes (zero / non-zero) and tx-level steady-state gas. Run with --isolate.
contract SimCalldataProbe is GasFixture {
    function _entries(uint256 n) internal view returns (ExecutionEntry[] memory entries) {
        entries = _savedFor(rA.id, n, 0, 1);
        for (uint256 i; i < n; i++) {
            entries[i].rollingHash = keccak256("benchmark rolling hash");
        }
    }

    function _report(uint256 n) internal {
        ProofSystemBatchPerVerificationEntries memory b = _stdBatch(rA.id, _entries(n), _emptyStaticEntries(), 0, 0);
        bytes memory cd = abi.encodeCall(EEZ.postAndVerifyBatch, (b));
        uint256 z;
        for (uint256 i; i < cd.length; i++) {
            if (cd[i] == 0) z++;
        }
        rollups.postAndVerifyBatch(b);
        vm.roll(block.number + 1);
        rollups.postAndVerifyBatch(b);
        uint256 g = vm.lastCallGas().gasTotalUsed;
        string memory k = string.concat("sim.deferred_l1l2.n", vm.toString(n));
        console.log(string.concat(k, ".calldata_bytes"), cd.length);
        console.log(string.concat(k, ".zero_bytes"), z);
        console.log(string.concat(k, ".tx_gas"), g);
    }

    function test_N1() public { _report(1); }
    function test_N2() public { _report(2); }
    function test_N8() public { _report(8); }
}
