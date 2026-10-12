"""Deploy the reviewed ZIP verbatim; never resume a transaction for other code."""
import argparse
import sys
from datetime import datetime, timezone

if __package__:
    from .network_common import *
    from .verify_onchain_code import checked_package, verify_deploy_transaction, verify_onchain_code
else:
    from network_common import *
    from verify_onchain_code import checked_package, verify_deploy_transaction, verify_onchain_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--fees-file', help='Measured deployment SDK fee estimate JSON')
    args = parser.parse_args()
    package, digest = checked_package()
    manifest = load_manifest()
    tx = manifest.get('package_deploy_tx')
    contract = manifest.get('package_contract')
    if tx or contract:
        if manifest.get('package_sha256') != digest:
            raise RuntimeError('Refusing resume: recorded package differs from artifact')
        reader = client_read_only()
        if not tx:
            raise RuntimeError('Package contract has no recorded deployment transaction')
        # A legacy deploy_tx must never be reused. Check the submitted code before
        # waiting, recording an address or accessing the signer.
        verify_deploy_transaction(reader, tx, digest)
        if contract:
            verify_onchain_code(contract, digest)
            print('Already verified:', contract)
            return 0
        if args.preflight:
            print('Package deployment pending; transaction code hash verified:', tx)
            return 0
        client = reader  # Resumption and verification need no private key or fees.
    else:
        address, balance = preflight()
        manifest.update({
            'chain_id': 4221, 'rpc': RPC, 'deployer': address,
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'package_deploy_tx': None, 'package_contract': None, 'package_sha256': digest,
            'constructor_args': CONSTRUCTOR_ARGS, 'address': None, 'explorer_url': None,
            'demo_txs': manifest.get('demo_txs', []),
        })
        print('Bradbury deployer:', address, 'balance wei:', balance)
        if balance == 0:
            manifest.update({'status': 'blocked', 'blockers': ['Deployer balance is zero; faucet funding required']})
            save_manifest(manifest)
            print('BLOCKER: obtain test GEN; no deployment transaction sent')
            return 2
        if args.preflight:
            manifest.update({'status': 'package_not_deployed', 'blockers': []})
            save_manifest(manifest)
            print('Funded. Provide measured --fees-file before deployment.')
            return 0
        if not args.fees_file:
            print('BLOCKER: provide measured --fees-file')
            return 2
        fees = fee_options(args.fees_file, 'deploy')
        client = client_with_signer()
        # Exact bytes from artifacts/issue_bounty_escrow.zip; never rebuild here.
        tx = hex_hash(client.deploy_contract(code=package, args=CONSTRUCTOR_ARGS, fees=fees))
        manifest.update({'package_deploy_tx': tx, 'status': 'pending'})
        save_manifest(manifest)
        verify_deploy_transaction(client, tx, digest)

    receipt = confirmed(client, tx)
    deployed = receipt.get('data', {}).get('contract_address') or receipt.get('recipient') or receipt.get('to_address')
    if not deployed or str(deployed).lower() == '0x' + '0' * 40:
        raise RuntimeError('Missing contract address in verified deployment receipt')
    # Success requires RPC code bytes to match, not merely a successful receipt.
    verify_onchain_code(str(deployed), digest)
    manifest.update({
        'package_contract': str(deployed), 'address': str(deployed),
        'explorer_url': EXPLORER + '/address/' + str(deployed),
        'deployed_at': datetime.now(timezone.utc).isoformat(),
        'status': 'deployed', 'blockers': [], 'onchain_code_verified': True,
    })
    save_manifest(manifest)
    print('Deployed and code verified:', manifest['explorer_url'])
    return 0


if __name__ == '__main__':
    sys.exit(safe_main(main))
