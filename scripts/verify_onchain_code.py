"""Read-only verification of exact ZIP bytes against Bradbury contract code."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path

if __package__:
    from .build_contract_package import OUTPUT, ROOT, verify_package
    from .network_common import MANIFEST, rpc
else:
    from build_contract_package import OUTPUT, ROOT, verify_package
    from network_common import MANIFEST, rpc

PACKAGE_MANIFEST = ROOT / 'artifacts/issue_bounty_escrow.package.json'


def checked_package() -> tuple[bytes, str]:
    """Use the recorded artifact verbatim, checking its hash and source semantics."""
    package = OUTPUT.read_bytes()
    recorded = json.loads(PACKAGE_MANIFEST.read_text())
    digest = hashlib.sha256(package).hexdigest()
    if digest != recorded['package_sha256'] or len(package) != recorded['package_bytes']:
        raise RuntimeError('Artifact does not match package manifest')
    verify_package(package)
    return package, digest


def assert_code_hash(code: bytes, expected: str) -> str:
    digest = hashlib.sha256(code).hexdigest()
    if digest != expected:
        raise RuntimeError('Code SHA-256 differs from package_sha256')
    return digest


def verify_onchain_code(contract: str, expected: str) -> str:
    """Fetch binary code directly; SDK text decoding would corrupt ZIP bytes."""
    if not re.fullmatch(r'0x[0-9a-fA-F]{40}', contract) or int(contract, 16) == 0:
        raise RuntimeError('A nonzero package contract address is required')
    if int(rpc('eth_chainId', []), 16) != 4221:
        raise RuntimeError('Refusing a non-Bradbury chain')
    encoded = rpc('gen_getContractCode', [{'address': contract}])
    code = base64.b64decode(encoded, validate=True)
    return assert_code_hash(code, expected)


def verify_deploy_transaction(client, tx: str, expected: str) -> None:
    """Fail closed if a resumed SDK deployment contains different or missing code."""
    transaction = client.get_transaction(tx)
    # Some SDK releases expose raw RLP even when their text-oriented decode fails
    # for binary packages. Hash the raw code field without a UTF-8 conversion.
    raw = transaction.get('tx_data')
    if raw:
        import rlp
        payload = bytes.fromhex(raw.removeprefix('0x')) if isinstance(raw, str) else bytes(raw)
        fields = rlp.decode(payload)
        if not isinstance(fields, list) or len(fields) != 3 or not isinstance(fields[0], bytes):
            raise RuntimeError('Existing transaction has no verifiable deployment code')
        assert_code_hash(fields[0], expected)
        return
    deployment = transaction.get('tx_data_decoded')
    if not isinstance(deployment, dict) or deployment.get('type') != 'deploy':
        raise RuntimeError('Existing transaction has no verifiable deployment code')
    encoded = deployment.get('code')
    if not isinstance(encoded, str) or not encoded.startswith('0x'):
        raise RuntimeError('Existing transaction has no verifiable deployment code')
    assert_code_hash(bytes.fromhex(encoded[2:]), expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--contract', help='Explicit package contract, before manifest confirmation')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    _, digest = checked_package()
    if manifest.get('package_sha256') != digest:
        raise RuntimeError('Deployment manifest does not identify this package')
    contract = args.contract or manifest.get('package_contract')
    if not contract:
        raise RuntimeError('ZIP package has not been deployed; no package_contract recorded')
    verify_onchain_code(contract, digest)
    print(json.dumps({'package_contract': contract, 'package_sha256': digest,
                      'verified': True, 'transactions_sent': 0}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
