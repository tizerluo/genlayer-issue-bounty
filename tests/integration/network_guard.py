"""真实 LLM 和 mock 测试共享本地网络边界，先于部署/签名。"""
from urllib.parse import urlparse


def require_localnet(config):
    network = config.get_network_name()
    url = config.get_rpc_url()
    parsed = urlparse(url)
    if (network != 'localnet' or config.get_chain_type() != 'localnet'
            or parsed.scheme not in ('http', 'https')
            or parsed.hostname not in ('127.0.0.1', 'localhost', '::1')):
        raise RuntimeError('Integration and live smoke tests require a loopback localnet RPC')
