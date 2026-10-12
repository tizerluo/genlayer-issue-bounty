"""可恢复的小额测试 GEN 演示；只允许 Bradbury，所有交易均先记录哈希。"""
import argparse
import sys
from datetime import datetime,timezone
if __package__:
    from .network_common import *
    from .verify_onchain_code import verify_onchain_code
else:
    from network_common import *
    from verify_onchain_code import verify_onchain_code

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--network',choices=['testnet-bradbury'],default='testnet-bradbury')
    parser.add_argument('--fees-file',required=True)
    parser.add_argument('--reward-wei',type=int,default=10**14)
    parser.add_argument('--login',default='tizerluo')
    args=parser.parse_args()
    if not 0 < args.reward_wei <= 10**15:
        raise RuntimeError('Demo reward must be positive and at most 0.001 test GEN')
    address,balance=preflight()
    manifest=load_manifest()
    contract=manifest.get('package_contract')
    if not contract or balance==0:
        print('BLOCKER: funded dedicated deployer and verified Bradbury deployment required')
        return 2
    sandbox=json.loads((ROOT/'deployments/sandbox.json').read_text())
    verify_onchain_code(contract,manifest['package_sha256'])
    client=client_with_signer()
    if int(client.read_contract(contract,'get_config')['claim_grace_seconds'])!=259200:
        raise RuntimeError('Unexpected contract configuration')
    manifest.setdefault('demo_txs',[])
    def step(name,method,values,value=0):
        entry=next((t for t in manifest['demo_txs'] if t['step']==name),None)
        if entry is None:
            tx=hex_hash(client.write_contract(contract,method,args=values,value=value,fees=fee_options(args.fees_file,method)))
            entry={'step':name,'tx_hash':tx,'status':'pending','explorer_url':EXPLORER+'/tx/'+tx}
            manifest['demo_txs'].append(entry)
            save_manifest(manifest)
        receipt=confirmed(client,entry['tx_hash'])
        entry['status']='finalized_success'
        save_manifest(manifest)
        print(name,entry['tx_hash'])
        return receipt
    step('bind','bind_github',[args.login])
    if 'demo_deadline' not in manifest:
        manifest['demo_deadline']=int(datetime.now(timezone.utc).timestamp())+7200
        save_manifest(manifest)
    creation=step('create','create_bounty',[sandbox['repo'],sandbox['issue_number'],
         ['Implement integer addition','Document addition with an example'],manifest['demo_deadline'],7],args.reward_wei)
    # 始终从同一交易回执重建，修复旧版在并发创建前猜测 id 的记录。
    bounty_id=created_bounty_id(creation)
    manifest['demo_bounty_id']=bounty_id
    save_manifest(manifest)
    bounty=client.read_contract(contract,'get_bounty',[bounty_id])
    if bounty['creator'].lower()!=address.lower() or bounty['reward']!=args.reward_wei:
        raise RuntimeError('Concurrent bounty creation or unexpected stored reward')
    if sandbox.get('claim_evidence_status') != 'ready_after_creation':
        print('BLOCKER: bounty created; prepare a fresh PR merged after creation by another GitHub id into the default branch, with Fixes #issue in its merge commit, then update sandbox selectors')
        return 2
    step('claim','submit_claim',[bounty_id,sandbox['complete_pr']])
    bounty=client.read_contract(contract,'get_bounty',[bounty_id])
    if bounty['status']!='AWARDED' or bounty['winner'].lower()!=address.lower():
        raise RuntimeError('Claim was not awarded to deployer')
    unlock=int(client.read_contract(contract,'get_credit_unlock_at',[address]))
    if int(datetime.now(timezone.utc).timestamp()) < unlock:
        print('BLOCKER: award credit locked until Unix timestamp',unlock,'; rerun after the finality delay')
        return 2
    before=int(rpc('eth_getBalance',[address,'latest']),16)
    step('withdraw','withdraw',[])
    accounting=client.read_contract(contract,'get_accounting')
    if client.read_contract(contract,'get_credit',[address])!=0:
        raise RuntimeError('Credit remains after withdrawal')
    manifest['demo_accounting']=accounting
    manifest['withdraw_balance_observation']={'before_wei':before,'after_wei':int(rpc('eth_getBalance',[address,'latest']),16),
         'note':'Balance difference includes transaction fees; verify external transfer receipt separately'}
    save_manifest(manifest)
    print('Demo bounty:',bounty_id,'withdraw finalized; inspect external transfer delivery in explorer')
    return 0

if __name__=='__main__':
    sys.exit(safe_main(main))
