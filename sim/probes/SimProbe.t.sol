// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {console} from "forge-std/Test.sol";
import {Base} from "./Base.t.sol";
import {MockProofSystem} from "./mocks/MockProofSystem.sol";
import {ECDSAProofSystem} from "../src/proofSystems/ECDSAProofSystem.sol";
import {ProofSystemBatchPerVerificationEntries, RollupIdWithProofSystems} from "../src/EEZ.sol";

/// @notice Scratch probe for the mechanism-sim M1 cost model (not part of upstream).
///         Steady-state empty-batch gas vs (R rollups, P proof systems, every rollup lists all P),
///         and cold ECDSAProofSystem.verify gas. Run with --isolate.
contract SimProbe is Base {
    function setUp() public {
        setUpBase();
    }

    function _sortedMocks(uint256 p) internal returns (address[] memory a) {
        a = new address[](p);
        for (uint256 i; i < p; i++) a[i] = address(new MockProofSystem());
        for (uint256 i; i < p; i++) {
            for (uint256 j = i + 1; j < p; j++) {
                if (uint160(a[j]) < uint160(a[i])) (a[i], a[j]) = (a[j], a[i]);
            }
        }
    }

    function _batch(uint256[] memory rids, address[] memory psList)
        internal
        pure
        returns (ProofSystemBatchPerVerificationEntries memory b)
    {
        uint256 p = psList.length;
        uint64[] memory idx = new uint64[](p);
        for (uint256 i; i < p; i++) idx[i] = uint64(i);
        RollupIdWithProofSystems[] memory rps = new RollupIdWithProofSystems[](rids.length);
        for (uint256 r; r < rids.length; r++) {
            rps[r] = RollupIdWithProofSystems({rollupId: uint64(rids[r]), proofSystemIndexes: idx});
        }
        bytes[] memory proofs = new bytes[](p);
        for (uint256 i; i < p; i++) proofs[i] = "proof";
        b = _raw(_emptyEntries(), _emptyStaticEntries(), psList, proofs, rps, 0, 0);
    }

    function _measure(uint256 nR, uint256 nP) internal returns (uint256) {
        address[] memory psList = _sortedMocks(nP);
        bytes32[] memory vks = new bytes32[](nP);
        for (uint256 i; i < nP; i++) vks[i] = keccak256(abi.encode(i + 1));
        uint256[] memory rids = new uint256[](nR);
        for (uint256 r; r < nR; r++) {
            rids[r] = _makeRollupCustom(keccak256(abi.encode("root", r)), psList, vks, 1, defaultOwner).id;
        }
        ProofSystemBatchPerVerificationEntries memory b = _batch(rids, psList);
        rollups.postAndVerifyBatch(b); // warm-up: first write of verification records
        vm.roll(block.number + 1);
        rollups.postAndVerifyBatch(b);
        return vm.lastCallGas().gasTotalUsed;
    }

    function test_Empty_R1_P1() public {
        console.log("sim.empty.R1.P1", _measure(1, 1));
    }

    function test_Empty_R1_P2() public {
        console.log("sim.empty.R1.P2", _measure(1, 2));
    }

    function test_Empty_R1_P4() public {
        console.log("sim.empty.R1.P4", _measure(1, 4));
    }

    function test_Empty_R2_P1() public {
        console.log("sim.empty.R2.P1", _measure(2, 1));
    }

    function test_Empty_R2_P2() public {
        console.log("sim.empty.R2.P2", _measure(2, 2));
    }

    function test_Empty_R2_P4() public {
        console.log("sim.empty.R2.P4", _measure(2, 4));
    }

    function test_Empty_R4_P1() public {
        console.log("sim.empty.R4.P1", _measure(4, 1));
    }

    function test_Empty_R4_P2() public {
        console.log("sim.empty.R4.P2", _measure(4, 2));
    }

    function test_Empty_R4_P4() public {
        console.log("sim.empty.R4.P4", _measure(4, 4));
    }

    function test_EcdsaVerifyCold() public {
        uint256 pk = 0xA11CE;
        ECDSAProofSystem v = new ECDSAProofSystem(address(0xBEEF), vm.addr(pk));
        bytes32 h = keccak256("x");
        (uint8 vv, bytes32 r, bytes32 s) = vm.sign(pk, h);
        bytes memory proof = abi.encodePacked(r, s, vv);
        assertTrue(v.verify(proof, h));
        console.log("sim.ecdsa.verify_call", vm.lastCallGas().gasTotalUsed);
        MockProofSystem m = new MockProofSystem();
        m.verify(proof, h);
        console.log("sim.mock.verify_call", vm.lastCallGas().gasTotalUsed);
    }
}
