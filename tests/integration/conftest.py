"""集成测试显式选择本地 Studio，禁止把 mock 配置发到测试网。"""
import os
import socket
import pytest
from .network_guard import require_localnet

@pytest.fixture(autouse=True)
def studio_required():
    if os.environ.get('ISSUE_BOUNTY_STUDIO_TESTS') != '1':
        pytest.skip('Set ISSUE_BOUNTY_STUDIO_TESTS=1 with a running local Studio')
    from gltest_cli.config.general import get_general_config
    config = get_general_config()
    require_localnet(config)
    try:
        with socket.create_connection(('127.0.0.1',4000),timeout=2):
            pass
    except OSError:
        pytest.skip('BLOCKER: Studio RPC not running on port 4000; Docker unavailable in build environment')
