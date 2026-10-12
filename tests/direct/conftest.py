"""严格 mock 和固定交易时间贯穿全部直接模式测试。"""
import pytest

NOW = 1791763200
CONTRACT = 'contracts/issue_bounty_escrow.py'
TREASURY = '0x' + '8' * 40

@pytest.fixture(autouse=True)
def strict_vm(direct_vm):
    direct_vm.check_pickling = True
    direct_vm.strict_mocks = True
    direct_vm.warp('2026-10-12T00:00:00Z')

@pytest.fixture
def escrow(direct_deploy, direct_vm):
    contract = direct_deploy(CONTRACT, 259200, 3, TREASURY)
    from genlayer import Address
    direct_vm.sender = Address(direct_vm.sender)
    return contract

@pytest.fixture
def ready(escrow, direct_vm):
    from tests.helpers import bind, create
    bind(direct_vm, escrow)
    create(direct_vm, escrow, value=123)
    direct_vm.clear_mocks()
    return escrow
