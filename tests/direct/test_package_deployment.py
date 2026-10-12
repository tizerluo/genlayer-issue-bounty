"""Exact-artifact deployment and read-only on-chain hash guards; every network call is mocked."""
import base64
import hashlib
import json
import sys
from types import SimpleNamespace

import pytest

from scripts import deploy_bradbury as deploy
from scripts import verify_onchain_code as verify
from scripts.network_common import CONSTRUCTOR_ARGS


@pytest.fixture
def deployment(monkeypatch):
    package, digest = verify.checked_package()
    manifest = {'deploy_tx': 'legacy-tx', 'contract': '0x'+'a'*40, 'address': '0x'+'a'*40}
    saved=[]
    sent=[]
    client=SimpleNamespace(
        deploy_contract=lambda **kwargs: sent.append(kwargs) or '0xnew',
        get_transaction=lambda tx: {'tx_data_decoded': {'type': 'deploy', 'code': '0x'+package.hex()}},
    )
    monkeypatch.setattr(sys, 'argv', ['deploy_bradbury.py', '--fees-file', 'unused.json'])
    monkeypatch.setattr(deploy, 'preflight', lambda: ('0x'+'1'*40, 100))
    monkeypatch.setattr(deploy, 'load_manifest', lambda: manifest)
    monkeypatch.setattr(deploy, 'save_manifest', lambda data: saved.append(json.loads(json.dumps(data))))
    monkeypatch.setattr(deploy, 'fee_options', lambda path, method: {'measured': True})
    monkeypatch.setattr(deploy, 'client_with_signer', lambda: client)
    monkeypatch.setattr(deploy, 'client_read_only', lambda: client)
    monkeypatch.setattr(deploy, 'confirmed', lambda client, tx: {'recipient': '0x'+'2'*40})
    monkeypatch.setattr(verify, 'rpc', lambda method, params: '0x107d' if method == 'eth_chainId'
                        else base64.b64encode(package).decode())
    return SimpleNamespace(package=package, digest=digest, manifest=manifest,
                           saved=saved, sent=sent, client=client)


def test_legacy_transaction_is_not_resumed_and_exact_artifact_is_sent(deployment):
    assert deploy.main() == 0
    assert deployment.sent == [{'code': deployment.package, 'args': CONSTRUCTOR_ARGS, 'fees': {'measured': True}}]
    pending=deployment.saved[0]
    assert pending['package_deploy_tx'] == '0xnew' and pending['package_contract'] is None
    assert pending['package_sha256'] == deployment.digest and pending['status'] == 'pending'
    final=deployment.saved[-1]
    assert final['package_contract'] == '0x'+'2'*40
    assert final['onchain_code_verified'] is True and final['status'] == 'deployed'


def test_resume_different_transaction_code_refused_before_signing(deployment, monkeypatch):
    deployment.manifest.update(package_deploy_tx='legacy-tx', package_sha256=deployment.digest)
    deployment.client.get_transaction=lambda tx: {'tx_data_decoded': {'type': 'deploy', 'code': '0x00'}}
    monkeypatch.setattr(deploy, 'client_with_signer', lambda: pytest.fail('Must not decrypt/sign'))
    monkeypatch.setattr(deploy, 'confirmed', lambda *args: pytest.fail('Must reject before waiting'))
    with pytest.raises(RuntimeError, match='SHA-256 differs'):
        deploy.main()
    assert deployment.sent == [] and deployment.saved == []


def test_resume_artifact_change_refused_before_rpc(deployment, monkeypatch):
    deployment.manifest.update(package_deploy_tx='tx', package_sha256='0'*64)
    monkeypatch.setattr(deploy, 'client_read_only', lambda: pytest.fail('Must reject before RPC'))
    with pytest.raises(RuntimeError, match='Refusing resume'):
        deploy.main()


def test_matching_resume_uses_no_signer_or_fees(deployment, monkeypatch):
    deployment.manifest.update(package_deploy_tx='tx', package_sha256=deployment.digest)
    monkeypatch.setattr(sys, 'argv', ['deploy_bradbury.py'])
    monkeypatch.setattr(deploy, 'preflight', lambda: pytest.fail('Resume does not inspect keystore'))
    monkeypatch.setattr(deploy, 'client_with_signer', lambda: pytest.fail('Must not decrypt/sign'))
    assert deploy.main() == 0
    assert deployment.sent == []
    assert deployment.manifest['package_contract'] == '0x'+'2'*40


def test_wrong_onchain_code_never_recorded_as_deployed(deployment, monkeypatch):
    monkeypatch.setattr(verify, 'rpc', lambda method, params: '0x107d' if method == 'eth_chainId'
                        else base64.b64encode(b'legacy source').decode())
    with pytest.raises(RuntimeError, match='SHA-256 differs'):
        deploy.main()
    assert len(deployment.saved) == 1
    assert deployment.saved[0]['package_contract'] is None
    assert deployment.saved[0]['status'] == 'pending'


def test_existing_contract_is_reverified(deployment, monkeypatch):
    deployment.manifest.update(package_deploy_tx='tx', package_sha256=deployment.digest,
                               package_contract='0x'+'2'*40)
    monkeypatch.setattr(deploy, 'client_with_signer', lambda: pytest.fail('Must not decrypt/sign'))
    assert deploy.main() == 0
    assert deployment.sent == [] and deployment.saved == []


def test_read_only_binary_code_verification(monkeypatch):
    code=b'PK\x03\x04\xff\x00\x80'
    digest=hashlib.sha256(code).hexdigest()
    calls=[]
    def rpc(method, params):
        calls.append((method, params))
        assert method in {'eth_chainId', 'gen_getContractCode'}
        return '0x107d' if method == 'eth_chainId' else base64.b64encode(code).decode()
    monkeypatch.setattr(verify, 'rpc', rpc)
    assert verify.verify_onchain_code('0x'+'2'*40, digest) == digest
    assert calls[-1] == ('gen_getContractCode', [{'address': '0x'+'2'*40}])
    with pytest.raises(RuntimeError, match='SHA-256 differs'):
        verify.verify_onchain_code('0x'+'2'*40, '0'*64)


def test_read_only_verifier_rejects_wrong_chain_before_code_fetch(monkeypatch):
    def rpc(method, params):
        assert method == 'eth_chainId'
        return '0x1'
    monkeypatch.setattr(verify, 'rpc', rpc)
    with pytest.raises(RuntimeError, match='non-Bradbury'):
        verify.verify_onchain_code('0x'+'2'*40, '0'*64)


@pytest.mark.parametrize('transaction', [{}, {'tx_data_decoded': {'type': 'call'}},
                                        {'tx_data_decoded': {'type': 'deploy', 'code': None}}])
def test_resume_requires_verifiable_code(transaction):
    with pytest.raises(RuntimeError, match='no verifiable deployment code'):
        verify.verify_deploy_transaction(SimpleNamespace(get_transaction=lambda tx: transaction), 'tx', '0'*64)


def test_resume_hashes_raw_binary_rlp_code():
    import rlp
    code=b'PK\xff\x80\x00'
    payload='0x'+rlp.encode([code, b'constructor calldata', b'']).hex()
    client=SimpleNamespace(get_transaction=lambda tx: {'tx_data': payload, 'tx_data_decoded': None})
    verify.verify_deploy_transaction(client, 'tx', hashlib.sha256(code).hexdigest())
    with pytest.raises(RuntimeError, match='SHA-256 differs'):
        verify.verify_deploy_transaction(client, 'tx', '0'*64)


def test_resume_rejects_raw_method_transaction():
    import rlp
    client=SimpleNamespace(get_transaction=lambda tx: {'tx_data': '0x'+rlp.encode([b'call', b'']).hex()})
    with pytest.raises(RuntimeError, match='no verifiable deployment code'):
        verify.verify_deploy_transaction(client, 'tx', '0'*64)


def test_exact_package_manifest_rejects_byte_change(monkeypatch, tmp_path):
    package, _ = verify.checked_package()
    altered=tmp_path/'altered.zip'
    altered.write_bytes(package+b'\x00')
    monkeypatch.setattr(verify, 'OUTPUT', altered)
    with pytest.raises(RuntimeError, match='does not match package manifest'):
        verify.checked_package()


def test_verifier_has_no_legacy_address_fallback(monkeypatch, tmp_path):
    _, digest=verify.checked_package()
    manifest=tmp_path/'deployment.json'
    manifest.write_text(json.dumps({'address': '0x'+'a'*40, 'deploy_tx': 'legacy', 'package_sha256': digest}))
    monkeypatch.setattr(sys, 'argv', ['verify_onchain_code.py', '--manifest', str(manifest)])
    monkeypatch.setattr(verify, 'rpc', lambda *args: pytest.fail('No ZIP deployment to query'))
    with pytest.raises(RuntimeError, match='has not been deployed'):
        verify.main()
