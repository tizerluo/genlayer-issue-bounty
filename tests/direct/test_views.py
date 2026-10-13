"""T-V1：分页和不存在的编号。"""
import pytest
from tests.helpers import NOW, pr, verdict


@pytest.mark.parametrize('as_string', [False, True], ids=['address', 'str'])
@pytest.mark.parametrize('accepted', [False, True], ids=['empty-credit', 'awarded-credit'])
def test_wallet_views_accept_address_or_string(ready, direct_vm, as_string, accepted):
    pr(direct_vm, merged=accepted)
    if accepted:
        verdict(direct_vm)
    ready.submit_claim(0, 34)
    wallet = direct_vm.sender.as_hex if as_string else direct_vm.sender
    assert ready.get_credit(wallet) == (123 if accepted else 0)
    assert ready.get_credit_unlock_at(wallet) == (NOW + 604800 if accepted else 0)
    assert ready.get_github_binding(wallet) == {'github_id': 42, 'login': 'alice'}
    assert ready.get_claim_count(0, wallet) == 1


@pytest.mark.parametrize('as_string', [False, True], ids=['address', 'str'])
def test_unbound_wallet_views_accept_address_or_string(ready, as_string):
    from genlayer import Address
    wallet = Address('0x' + '9' * 40)
    if as_string:
        wallet = wallet.as_hex
    assert ready.get_credit(wallet) == 0
    assert ready.get_credit_unlock_at(wallet) == 0
    assert ready.get_github_binding(wallet) == {'github_id': 0, 'login': ''}
    assert ready.get_claim_count(0, wallet) == 0

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
