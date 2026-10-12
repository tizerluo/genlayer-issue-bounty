"""T-P：清零后发消息、退款边界和资金守恒。"""
import pytest
from gltest.direct import create_address
from tests.helpers import create, pr, verdict, NOW

@pytest.fixture(autouse=True)
def native_transfer_model(direct_vm):
    """独立模拟请求的余额效果，不读取合约账本；不代表真实子交易执行。"""
    def emit(vm, request):
        if 'EthSend' in request:
            transfer = request['EthSend']
            balance = vm._balances.get(vm._contract_address, 0)
            assert balance >= transfer['value']
            vm.deal(vm._contract_address, balance - transfer['value'])
        return {'ok':None}
    direct_vm._gl_call_hook = emit

def conserved(c, inflow):
    a=c.get_accounting()
    assert a['total_escrowed']+a['total_credits']+a['total_withdrawn'] == inflow
    assert a['contract_balance'] == a['total_escrowed'] + a['total_credits']
    assert a['contract_balance'] == inflow - a['total_withdrawn']

def test_withdraw(ready,direct_vm,monkeypatch):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    conserved(ready,123)
    assert ready.get_bounty(0)['awarded_at'] == NOW
    direct_vm.warp('2026-10-19T00:00:00Z')
    sender=direct_vm.sender
    requests=[]
    transfer_model=direct_vm._gl_call_hook
    def hook(vm,request):
        requests.append(request)
        if 'EthSend' in request:
            assert ready.get_credit(sender.as_hex) == 0
            assert ready.get_accounting()['total_withdrawn'] == 123
            assert request['EthSend']['address'] == sender
            assert request['EthSend']['value'] == 123
            assert request['EthSend']['calldata'] == b''
        return transfer_model(vm,request)
    direct_vm._gl_call_hook=hook
    ready.withdraw()
    assert any('EthSend' in r for r in requests)
    assert ready.get_credit(sender.as_hex) == 0
    conserved(ready,123)
    with direct_vm.expect_revert('NOTHING_TO_WITHDRAW'):
        ready.withdraw()

def test_empty(escrow,direct_vm):
    with direct_vm.expect_revert('NOTHING_TO_WITHDRAW'):
        escrow.withdraw()

def test_refund(ready,direct_vm):
    direct_vm.warp('2026-10-15T02:00:00Z')
    with direct_vm.expect_revert('REFUND_TOO_EARLY'):
        ready.refund(0)
    direct_vm.warp('2026-10-15T02:00:01Z')
    ready.refund(0)
    assert ready.get_bounty(0)['status'] == 'REFUNDED'
    assert ready.get_credit(direct_vm.sender.as_hex) == 123
    conserved(ready,123)
    with direct_vm.expect_revert('BOUNTY_NOT_OPEN'):
        ready.refund(0)

def test_refund_permissions(ready,direct_vm):
    creator=direct_vm.sender
    direct_vm.sender=create_address('bob')
    with direct_vm.expect_revert('NOT_CREATOR'):
        ready.refund(0)
    direct_vm.sender=creator
    with direct_vm.expect_revert('REFUND_TOO_EARLY'):
        ready.refund(0)
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    with direct_vm.expect_revert('BOUNTY_NOT_OPEN'):
        ready.refund(0)

def test_sequence_accounting(ready,direct_vm):
    conserved(ready,123)
    create(direct_vm,ready,value=456)
    conserved(ready,579)
    direct_vm.clear_mocks()
    pr(direct_vm,merged=False)
    ready.submit_claim(0,34)
    conserved(ready,579)
    direct_vm.clear_mocks()
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    conserved(ready,579)
    direct_vm.warp('2026-10-15T02:00:01Z')
    ready.refund(1)
    conserved(ready,579)
    direct_vm.warp('2026-10-19T00:00:00Z')
    ready.withdraw()
    conserved(ready,579)

def test_events(escrow,direct_vm):
    requests=[]
    direct_vm._gl_call_hook=lambda vm,req: (requests.append(req) or {'ok':None})
    create(direct_vm,escrow,value=1)
    events=[r['EmitEvent'] for r in requests if 'EmitEvent' in r]
    assert len(events) == 1

@pytest.mark.parametrize('method,args', [('withdraw',[]),('withdraw_to',['0x'+'2'*40])])
def test_award_cannot_withdraw_before_finality(ready,direct_vm,method,args):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.warp('2026-10-18T23:59:59Z')
    with direct_vm.expect_revert('WITHDRAW_NOT_FINAL'):
        getattr(ready,method)(*args)
    assert ready.get_credit(direct_vm.sender.as_hex) == 123
    conserved(ready,123)

def test_withdraw_to_uses_callers_credit(ready,direct_vm):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    sender=direct_vm.sender
    recipient=create_address('recipient-eoa')
    direct_vm.warp('2026-10-19T00:00:00Z')
    requests=[]
    transfer_model=direct_vm._gl_call_hook
    def capture(vm,request):
        requests.append(request)
        return transfer_model(vm,request)
    direct_vm._gl_call_hook=capture
    direct_vm.sender=create_address('credit-thief')
    with direct_vm.expect_revert('NOTHING_TO_WITHDRAW'):
        ready.withdraw_to(recipient.as_hex)
    direct_vm.sender=sender
    ready.withdraw_to(recipient.as_hex)
    sends=[r['EthSend'] for r in requests if 'EthSend' in r]
    assert len(sends)==1 and sends[0]['address']==recipient and sends[0]['value']==123
    assert ready.get_credit_unlock_at(sender.as_hex)==0
    conserved(ready,123)

@pytest.mark.parametrize('recipient',['0x'+'0'*40,'bad','0x123'])
def test_invalid_recipient_leaves_credit(ready,direct_vm,recipient):
    with direct_vm.expect_revert('INVALID_RECIPIENT'):
        ready.withdraw_to(recipient)
    conserved(ready,123)

def test_contract_recipient_rejected(ready,direct_vm):
    from genlayer import Address
    with direct_vm.expect_revert('INVALID_RECIPIENT'):
        ready.withdraw_to(Address(direct_vm._contract_address).as_hex)

def test_new_award_cannot_shorten_existing_credit_hold(ready,direct_vm):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.warp('2026-10-13T00:00:00Z')
    create(direct_vm,ready,value=456,deadline=NOW+2*86400)
    pr(direct_vm,merged_at='2026-10-13T01:00:00Z')
    ready.submit_claim(1,34)
    assert ready.get_credit_unlock_at(direct_vm.sender.as_hex)==NOW+8*86400
    direct_vm.warp('2026-10-19T00:00:00Z')
    with direct_vm.expect_revert('WITHDRAW_NOT_FINAL'):
        ready.withdraw()
    conserved(ready,579)

def test_synchronous_emit_error_propagates(ready,direct_vm):
    from genlayer import gl
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.warp('2026-10-19T00:00:00Z')
    requests=[]
    def fail(vm,request):
        requests.append(request)
        if 'EthSend' in request:
            raise gl.vm.UserError('EMIT_FAILED')
        return {'ok':None}
    direct_vm._gl_call_hook=fail
    with direct_vm.expect_revert('EMIT_FAILED'):
        ready.withdraw()
    # Direct mode does not roll back storage on exceptions. Verify propagation and
    # absence of a success event; actual transaction rollback belongs to the host.
    assert not any('EmitEvent' in request for request in requests)

def test_accounting_detects_simulated_stranded_transfer(ready,direct_vm):
    # 异步子转账失败不执行合约恢复分支；独立余额断言必须暴露账本差异。
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.warp('2026-10-19T00:00:00Z')
    ready.withdraw()
    direct_vm.deal(direct_vm._contract_address,123)
    assert ready.get_accounting()['contract_balance']==123
    assert ready.get_credit(direct_vm.sender.as_hex)==0
    with pytest.raises(AssertionError):
        conserved(ready,123)


def test_sweep_preserves_open_escrow_and_refund_credit(ready, direct_vm):
    from genlayer import Address
    from conftest import TREASURY
    create(direct_vm, ready, value=456)
    direct_vm.warp('2026-10-15T02:00:01Z')
    ready.refund(1)
    direct_vm.deal(direct_vm._contract_address, 579 + 77)
    direct_vm.sender = Address(TREASURY)
    requests=[]
    transfer_model=direct_vm._gl_call_hook
    def capture(vm, request):
        requests.append(request)
        return transfer_model(vm, request)
    direct_vm._gl_call_hook=capture
    assert ready.sweep_surplus() == 77
    sends=[request['EthSend'] for request in requests if 'EthSend' in request]
    assert len(sends) == 1 and sends[0]['address'] == Address(TREASURY)
    assert sends[0]['value'] == 77
    accounting=ready.get_accounting()
    assert accounting['contract_balance'] == 579
    assert accounting['total_escrowed'] == 123 and accounting['total_credits'] == 456
    assert accounting['total_swept'] == 77 and accounting['total_withdrawn'] == 0
    with direct_vm.expect_revert('NO_SURPLUS'):
        ready.sweep_surplus()


def test_sweep_only_fixed_treasury(ready, direct_vm):
    direct_vm.deal(direct_vm._contract_address, 124)
    with direct_vm.expect_revert('NOT_TREASURY'):
        ready.sweep_surplus()
    assert ready.get_accounting()['contract_balance'] == 124


def test_failed_child_surplus_can_be_swept_without_recreating_credit(ready, direct_vm):
    from genlayer import Address
    from conftest import TREASURY
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0, 34)
    direct_vm.warp('2026-10-19T00:00:00Z')
    claimant=direct_vm.sender
    ready.withdraw()
    # Simulate failed deferred delivery leaving the original native funds behind.
    direct_vm.deal(direct_vm._contract_address, 123)
    create(direct_vm, ready, value=456, deadline=NOW+8*86400)
    direct_vm.sender=Address(TREASURY)
    assert ready.sweep_surplus() == 123
    assert ready.get_credit(claimant.as_hex) == 0
    accounting=ready.get_accounting()
    assert accounting['contract_balance'] == accounting['total_escrowed'] == 456
    assert accounting['total_swept'] == 123


def test_sweep_refuses_balance_below_liabilities(ready, direct_vm):
    from genlayer import Address
    from conftest import TREASURY
    direct_vm.sender=Address(TREASURY)
    direct_vm.deal(direct_vm._contract_address, 122)
    with direct_vm.expect_revert('NO_SURPLUS'):
        ready.sweep_surplus()
    assert ready.get_accounting()['total_escrowed'] == 123
