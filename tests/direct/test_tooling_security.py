"""Review #13：密码换行、私有缓存、回执 id 及本地网络守卫的负向测试。"""
import base64
import importlib
import json
from types import SimpleNamespace

import pytest
import rlp
from genlayer_py.abi import calldata

from scripts.cache_paths import private_cache
from tests.integration.network_guard import require_localnet


def test_signer_trims_only_trailing_newlines(monkeypatch,tmp_path):
    module=importlib.import_module('scripts.network_common')
    keyfile=tmp_path/'synthetic-keystore.json'
    keyfile.write_text(json.dumps({'synthetic':True}))
    password=tmp_path/'test-password.txt'
    password.write_text('synthetic passphrase \n\n')
    password.chmod(0o600)
    monkeypatch.setattr(module,'KEYSTORE',keyfile)
    monkeypatch.setattr(module,'PASSWORD',password)
    from eth_account import Account
    import genlayer_py
    def decrypt(data,phrase):
        assert data == {'synthetic':True}
        assert phrase == 'synthetic passphrase '
        return b'synthetic-test-material'
    monkeypatch.setattr(Account,'decrypt',decrypt)
    monkeypatch.setattr(genlayer_py,'create_account',lambda value:'synthetic-account')
    assert module.signer() == 'synthetic-account'


def test_password_permissions_rejected_before_decryption(monkeypatch,tmp_path):
    module=importlib.import_module('scripts.network_common')
    password=tmp_path/'test-password.txt'
    password.write_text('synthetic')
    password.chmod(0o644)
    monkeypatch.setattr(module,'PASSWORD',password)
    from eth_account import Account
    monkeypatch.setattr(Account,'decrypt',lambda *args:pytest.fail('Must not decrypt'))
    with pytest.raises(RuntimeError,match='mode 0600'):
        module.signer()


@pytest.mark.parametrize('kind',['world-writable','symlink','wrong-owner'])
def test_cache_rejects_untrusted_directory(monkeypatch,tmp_path,kind):
    root=tmp_path/'cache'
    root.mkdir(mode=0o700)
    if kind=='world-writable':
        root.chmod(0o777)
    elif kind=='symlink':
        link=tmp_path/'link'
        link.symlink_to(root,target_is_directory=True)
        root=link
    else:
        import scripts.cache_paths as cache_paths
        uid=cache_paths.os.getuid()
        monkeypatch.setattr(cache_paths.os,'getuid',lambda:uid+1)
    monkeypatch.setenv('ISSUE_BOUNTY_CACHE_DIR',str(root))
    with pytest.raises(RuntimeError,match='mode 0700'):
        private_cache('gltest-direct')


def test_cache_rejects_preplanted_sdk_subdirectory(monkeypatch,tmp_path):
    root=tmp_path/'cache'
    root.mkdir(mode=0o700)
    (root/'gltest-direct').symlink_to(tmp_path,target_is_directory=True)
    monkeypatch.setenv('ISSUE_BOUNTY_CACHE_DIR',str(root))
    with pytest.raises(RuntimeError,match='mode 0700'):
        private_cache('gltest-direct')


@pytest.mark.parametrize('network,url',[
    ('testnet_bradbury','https://rpc-bradbury.genlayer.com'),
    ('localnet','https://rpc-bradbury.genlayer.com'),
    ('localnet','http://127.0.0.1.attacker.example:4000'),
    ('localnet','http://127.0.0.1@attacker.example:4000'),
])
def test_live_smoke_guard_refuses_network_before_deploy(monkeypatch,network,url):
    module=importlib.import_module('tests.integration.test_live_smoke')
    config=SimpleNamespace(get_network_name=lambda:network,get_rpc_url=lambda:url,get_chain_type=lambda:network)
    from gltest_cli.config import general
    monkeypatch.setattr(general,'get_general_config',lambda:config)
    monkeypatch.setattr(module,'get_contract_factory',lambda **kwargs:pytest.fail('Must not deploy'))
    with pytest.raises(RuntimeError,match='loopback localnet'):
        module.test_real_judge('complete',1)


def receipt_for_bounty(bounty_id):
    # 官方 SDK 的旧版 RLP 执行回执格式；v0.6 缺失字节时明确停止。
    raw=rlp.encode([[[b'\x00',calldata.encode(bounty_id)],[],[],b''],[]])
    return {'tx_receipt':'0x'+raw.hex()}


@pytest.mark.parametrize('receipt',[{}, {'tx_receipt':'0x'}, receipt_for_bounty('7'), receipt_for_bounty(True)])
def test_missing_or_non_integer_creation_id_is_not_guessed(receipt):
    from scripts.network_common import created_bounty_id
    with pytest.raises(RuntimeError,match='no verifiable bounty id'):
        created_bounty_id(receipt)


def test_concurrent_demo_uses_creation_receipt_and_repairs_stale_id(monkeypatch,tmp_path):
    # 旧版错误记录 4；实际创建返回 7，期间其他人创建 5/6；禁止查询计数器。
    module=importlib.import_module('scripts.demo_flow')
    sandbox=tmp_path/'deployments'
    sandbox.mkdir()
    (sandbox/'sandbox.json').write_text(json.dumps({'repo':'owner/project','issue_number':12,'complete_pr':34}))
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module.sys,'argv',['demo_flow.py','--fees-file','unused.json'])
    address='0x'+'1'*40
    monkeypatch.setattr(module,'preflight',lambda:(address,10**15))
    manifest={'address':'0x'+'2'*40,'demo_bounty_id':4,'demo_deadline':123,
              'demo_txs':[{'step':'bind','tx_hash':'bind-tx'},{'step':'create','tx_hash':'create-tx'}]}
    monkeypatch.setattr(module,'load_manifest',lambda:manifest)
    monkeypatch.setattr(module,'save_manifest',lambda data:None)
    monkeypatch.setattr(module,'confirmed',lambda client,tx:receipt_for_bounty(7) if tx=='create-tx' else {})
    reads=[]
    def read(contract,method,args=None):
        reads.append((method,args))
        if method=='get_config':
            return {'claim_grace_seconds':259200}
        assert method=='get_bounty' and args==[7]
        return {'creator':address,'reward':10**14}
    client=SimpleNamespace(read_contract=read,
                           write_contract=lambda *a,**kw:pytest.fail('Must not resubmit recorded transactions'))
    monkeypatch.setattr(module,'client_with_signer',lambda:client)
    assert module.main()==2  # 等待新 PR；已完成创建必须持久保留准确 id。
    assert manifest['demo_bounty_id']==7
    assert ('get_bounty',[7]) in reads


def test_localnet_creation_result_decodes_actual_integer():
    from scripts.network_common import created_bounty_id
    result=base64.b64encode(b'\x00'+calldata.encode(9)).decode()
    assert created_bounty_id({'consensus_data':{'leader_receipt':[{'result':{'raw':result}}]}})==9
