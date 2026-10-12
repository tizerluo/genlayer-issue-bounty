"""真实 OpenRouter 冒烟；未提供密钥时按业主要求跳过。"""
import os
import pytest
from gltest import get_contract_factory
from .test_localnet_mocked import succeeded
from .network_guard import require_localnet

pytestmark=pytest.mark.live

@pytest.mark.parametrize('case', ['complete','partial'])
@pytest.mark.parametrize('run', [1,2,3])
def test_real_judge(case,run):
    from gltest_cli.config.general import get_general_config
    require_localnet(get_general_config())
    if not os.environ.get('OPENROUTER_API_KEY'):
        pytest.skip('BLOCKER: OPENROUTER_API_KEY absent')
    if os.environ.get('ISSUE_BOUNTY_LIVE_SMOKE') != '1':
        pytest.skip('Set ISSUE_BOUNTY_LIVE_SMOKE=1 after configuring OpenRouter in Studio')
    # 六个赏金须先于 PR 合并创建；禁止回溯 created_at 来迁就历史 PR。
    contract=os.environ.get('BOUNTY_LIVE_CONTRACT')
    ids=os.environ.get(f'BOUNTY_{case.upper()}_BOUNTY_IDS','').split(',')
    if not contract or len(ids)!=3 or not all(i.strip().isdigit() for i in ids):
        pytest.skip('Prepare a local contract and three distinct bounty ids per case BEFORE merging fresh PRs')
    ids=[int(i.strip()) for i in ids]
    if len(set(ids))!=3:
        pytest.fail('Each smoke run requires a distinct bounty id; rejected diffs cannot be rejudged')
    bounty_id=ids[run-1]
    pr=int(os.environ['BOUNTY_COMPLETE_PR' if case == 'complete' else 'BOUNTY_PARTIAL_PR'])
    c=get_contract_factory(contract_file_path='contracts/issue_bounty_escrow.py').build_contract(contract)
    assert c.get_bounty(bounty_id).call()['status']=='OPEN'
    assert c.get_claims_for_bounty(bounty_id).call()==[]
    succeeded(c.submit_claim(bounty_id,pr).transact())
    claim=c.get_claims_for_bounty(bounty_id).call()[0]
    assert claim['status'] == ('ACCEPTED' if case == 'complete' else 'REJECTED')
    if case == 'partial':
        assert claim['reason'] == 'CRITERIA_NOT_MET'
    print({'case':case,'run':run,'score':claim['score'],'status':claim['status'],'diff_sha256':claim['diff_sha256']})
