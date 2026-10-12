"""预检和部署；没有测试币时保存明确的 blocker，不导出私钥。"""
import argparse
import sys
from datetime import datetime,timezone
from network_common import *

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--fees-file',help='Measured network estimate JSON, separate deploy/method entries supported')
    args=parser.parse_args()
    address,balance=preflight()
    manifest=load_manifest()
    if manifest.get('address'):
        print('Already recorded:',manifest['address'])
        return 0
    manifest.update({'chain_id':4221,'rpc':RPC,'deployer':address,'checked_at':datetime.now(timezone.utc).isoformat(),
                     'address':None,'explorer_url':None,'demo_txs':manifest.get('demo_txs',[])})
    print('Bradbury deployer:',address,'balance wei:',balance)
    if balance == 0:
        manifest.update({'status':'blocked','blockers':['Official faucet requires GitHub sign-in and Turnstile; deployer balance is zero',
                                                      'FeeManager quoteGasPrice reverted with RC tooling; current fee profile unverified']})
        save_manifest(manifest)
        print('BLOCKER: obtain test GEN via the official faucet; no deployment transaction sent')
        return 2
    if args.preflight:
        print('Funded. Verify live fee policy and provide --fees-file before deployment.')
        return 0
    if not args.fees_file:
        print('BLOCKER: provide measured --fees-file after resolving network/tooling compatibility')
        return 2
    client=client_with_signer()
    # 已发送的部署交易始终先查回执，防止重跑脚本造成重复部署。
    tx=manifest.get('deploy_tx')
    if not tx:
        tx=hex_hash(client.deploy_contract(code=(ROOT/'contracts/issue_bounty_escrow.py').read_text(),
                      args=[259200,3],fees=fee_options(args.fees_file,'deploy')))
        manifest.update({'deploy_tx':tx,'status':'pending'})
        save_manifest(manifest)
    receipt=confirmed(client,tx)
    deployed=receipt.get('data',{}).get('contract_address') or receipt.get('recipient') or receipt.get('to_address')
    if not deployed or str(deployed).lower()=='0x'+'0'*40:
        raise RuntimeError('Missing contract address in verified deployment receipt')
    manifest.update({'address':str(deployed),'explorer_url':EXPLORER+'/address/'+str(deployed),
                     'deployed_at':datetime.now(timezone.utc).isoformat(),'status':'deployed','blockers':[]})
    save_manifest(manifest)
    print('Deployed:',manifest['explorer_url'])
    return 0

if __name__=='__main__':
    sys.exit(safe_main(main))
