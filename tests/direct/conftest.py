"""严格 mock 和固定交易时间贯穿全部直接模式测试。"""
import pytest

NOW = 1791763200
CONTRACT = 'contracts/issue_bounty_escrow.py'

@pytest.fixture(autouse=True)
def strict_vm(direct_vm):
    direct_vm.check_pickling = True
    direct_vm.strict_mocks = True
    direct_vm.warp('2026-10-12T00:00:00Z')

@pytest.fixture
def escrow(direct_deploy):
    return direct_deploy(CONTRACT, 259200, 3)
