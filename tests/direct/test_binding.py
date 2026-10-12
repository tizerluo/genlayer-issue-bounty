"""T-B：gist 证明及数字 id 双向迁移。"""
import pytest
from gltest.direct import create_address
from tests.helpers import bind, bind_marker, web, USER_URL

def test_binding(escrow, direct_vm):
    bind(direct_vm, escrow, login='ALICE')
    assert escrow.get_github_binding(direct_vm.sender.as_hex) == {'github_id':42,'login':'alice'}
    assert escrow.get_wallet_for_github_id(42).lower() == direct_vm.sender.as_hex.lower()

def test_wrong_proof(escrow, direct_vm):
    with direct_vm.expect_revert('BIND_PROOF_NOT_FOUND'):
        bind(direct_vm, escrow, proof='genlayer-bounty-bind:0x'+'0'*40)

def test_bad_login(escrow, direct_vm):
    with direct_vm.expect_revert('INVALID_LOGIN'):
        escrow.bind_github('bad/../x')

def test_move_identity(escrow, direct_vm):
    alice = direct_vm.sender
    bind(direct_vm, escrow)
    direct_vm.clear_mocks()
    bob = create_address('bob')
    direct_vm.sender = bob
    bind(direct_vm, escrow)
    assert escrow.get_github_binding(alice.as_hex)['github_id'] == 0
    assert escrow.get_wallet_for_github_id(42) == bob.as_hex
    direct_vm.clear_mocks()
    bind(direct_vm, escrow, github_id=43, login='charlie')
    assert escrow.get_wallet_for_github_id(42).lower() == '0x'+'0'*40

def test_old_gist_cannot_reclaim_migrated_identity(escrow,direct_vm):
    alice = direct_vm.sender
    old_proof = bind_marker(direct_vm,escrow)
    bind(direct_vm,escrow,proof=old_proof)
    direct_vm.clear_mocks()
    bob = create_address('new-owner-wallet')
    direct_vm.sender = bob
    bind(direct_vm,escrow)
    assert escrow.get_bind_nonce(42) == 2
    direct_vm.clear_mocks()
    direct_vm.sender = alice
    with direct_vm.expect_revert('BIND_PROOF_NOT_FOUND'):
        bind(direct_vm,escrow,proof=old_proof)
    assert escrow.get_wallet_for_github_id(42) == bob.as_hex
    assert escrow.get_bind_nonce(42) == 2

def test_proof_is_bound_to_contract(escrow,direct_vm):
    proof = bind_marker(direct_vm,escrow)
    parts = proof.split(':')
    parts[1] = '0x'+'f'*40
    with direct_vm.expect_revert('BIND_PROOF_NOT_FOUND'):
        bind(direct_vm,escrow,proof=':'.join(parts))
    assert escrow.get_bind_nonce(42) == 0

@pytest.mark.parametrize('owner_id',[43,True,'42'])
def test_gist_owner_must_match_user(escrow,direct_vm,owner_id):
    with direct_vm.expect_revert('BIND_PROOF_NOT_FOUND'):
        bind(direct_vm,escrow,owner_id=owner_id)
    assert escrow.get_github_binding(direct_vm.sender.as_hex)['github_id'] == 0
    assert escrow.get_bind_nonce(42) == 0

@pytest.mark.parametrize('status,code', [(404,'GITHUB_USER_NOT_FOUND'),(403,'GITHUB_HTTP_403'),(503,'GITHUB_HTTP_503')])
def test_http(escrow, direct_vm, status, code):
    web(direct_vm, USER_URL, {}, status)
    with direct_vm.expect_revert(code):
        escrow.bind_github('alice')
