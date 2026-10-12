"""T-I：构造参数边界。"""
import pytest
from conftest import CONTRACT

def test_config(escrow):
    assert escrow.get_config() == {'claim_grace_seconds': 259200, 'max_claims_per_claimant': 3,
                                  'prompt_version': 'BOUNTY_JUDGE_V1', 'score_tolerance': 2, 'max_criteria': 5,
                                  'finality_delay_seconds': 604800}
    assert escrow.get_bounty_count() == 0

@pytest.mark.parametrize('grace,claims', [(0,3), (2592001,3), (1,0), (1,11)])
def test_invalid_config(direct_vm, direct_deploy, grace, claims):
    with direct_vm.expect_revert('INVALID_'):
        direct_deploy(CONTRACT, grace, claims)
