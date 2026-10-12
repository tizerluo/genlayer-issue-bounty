"""T-P：清零后发消息、退款边界和资金守恒。"""
import pytest
from gltest.direct import create_address
from tests.helpers import create, pr, verdict

def conserved(c, inflow):
    a=c.get_accounting()
    assert a['total_escrowed']+a['total_credits']+a['total_withdrawn'] == inflow

def test_withdraw(ready,direct_vm,monkeypatch):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    conserved(ready,123)
    sender=direct_vm.sender
    requests=[]
    def hook(vm,request):
        requests.append(request)
        if 'EthSend' in request:
            assert ready.get_credit(sender.as_hex) == 0
            assert ready.get_accounting()['total_withdrawn'] == 123
            assert request['EthSend']['address'] == sender
            assert request['EthSend']['value'] == 123
            assert request['EthSend']['calldata'] == b''
        return {'ok':None}
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
    ready.withdraw()
    conserved(ready,579)

def test_events(escrow,direct_vm):
    requests=[]
    direct_vm._gl_call_hook=lambda vm,req: (requests.append(req) or {'ok':None})
    create(direct_vm,escrow,value=1)
    events=[r['EmitEvent'] for r in requests if 'EmitEvent' in r]
    assert len(events) == 1
