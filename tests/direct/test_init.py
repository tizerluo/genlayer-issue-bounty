"""T-I：构造参数边界。"""
import pytest
from conftest import CONTRACT, TREASURY

def test_config(escrow):
    assert escrow.get_config() == {'claim_grace_seconds': 259200, 'max_claims_per_claimant': 3,
                                  'treasury': TREASURY,
                                  'prompt_version': 'BOUNTY_JUDGE_V2', 'score_tolerance': 2, 'max_criteria': 5,
                                  'finality_delay_seconds': 604800}
    assert escrow.get_bounty_count() == 0

@pytest.mark.parametrize('grace,claims', [(0,3), (2592001,3), (1,0), (1,11)])
def test_invalid_config(direct_vm, direct_deploy, grace, claims):
    with direct_vm.expect_revert('INVALID_'):
        direct_deploy(CONTRACT, grace, claims, TREASURY)


@pytest.mark.parametrize('treasury', ['bad', '0x123', '0x'+'0'*40])
def test_invalid_treasury(direct_vm, direct_deploy, treasury):
    with direct_vm.expect_revert('INVALID_TREASURY'):
        direct_deploy(CONTRACT, 259200, 3, treasury)


def test_escrow_cannot_be_treasury(escrow, direct_vm):
    from importlib import import_module
    module = import_module('_contract_issue_bounty_escrow')
    with direct_vm.expect_revert('INVALID_TREASURY'):
        module.IssueBountyEscrow.__init__(escrow, 259200, 3, '0x'+direct_vm._contract_address.hex())
