"""T-V1：分页和不存在的编号。"""
import pytest

def test_empty_views(escrow):
    assert escrow.get_bounties(0,50) == []
    assert escrow.get_wallet_for_github_id(42).lower() == '0x'+'0'*40
    assert escrow.get_accounting()['total_escrowed'] == 0

@pytest.mark.parametrize('offset,limit', [(-1,1),(0,0),(0,51)])
def test_bad_pages(escrow, direct_vm, offset, limit):
    with direct_vm.expect_revert('INVALID_PAGE'):
        escrow.get_bounties(offset,limit)

@pytest.mark.parametrize('method,identifier,code', [('get_bounty',0,'BOUNTY_NOT_FOUND'),('get_bounty',-1,'BOUNTY_NOT_FOUND'),('get_claim',0,'CLAIM_NOT_FOUND')])
def test_missing(escrow, direct_vm, method, identifier, code):
    with direct_vm.expect_revert(code):
        getattr(escrow,method)(identifier)
