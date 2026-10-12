"""真实 OpenRouter 冒烟；未提供密钥时按业主要求跳过。"""
import os
import pytest
from gltest import get_contract_factory
from .test_localnet_mocked import succeeded

pytestmark=pytest.mark.live

@pytest.mark.parametrize('case', ['complete','partial'])
@pytest.mark.parametrize('run', [1,2,3])
def test_real_judge(case,run):
    if not os.environ.get('OPENROUTER_API_KEY'):
        pytest.skip('BLOCKER: OPENROUTER_API_KEY absent')
    if os.environ.get('ISSUE_BOUNTY_LIVE_SMOKE') != '1':
        pytest.skip('Set ISSUE_BOUNTY_LIVE_SMOKE=1 after configuring OpenRouter in Studio')
    # 每次使用新实例，避免前次 AWARDED 状态影响重复测量。
    repo=os.environ.get('BOUNTY_SANDBOX_REPO','tizerluo/bounty-sandbox')
    login=os.environ.get('BOUNTY_GITHUB_LOGIN','tizerluo')
    issue=int(os.environ.get('BOUNTY_ISSUE_NUMBER','2'))
    pr=int(os.environ['BOUNTY_COMPLETE_PR' if case == 'complete' else 'BOUNTY_PARTIAL_PR'])
    from datetime import datetime,timezone
    deadline=int(datetime.now(timezone.utc).timestamp())+7200
    c=get_contract_factory(contract_file_path='contracts/issue_bounty_escrow.py').deploy(args=[259200,3])
    succeeded(c.bind_github(login).transact())
    succeeded(c.create_bounty(repo,issue,['Implement integer addition','Document addition with an example'],deadline,7).transact())
    succeeded(c.submit_claim(0,pr).transact())
    claim=c.get_claim(0).call()
    assert claim['status'] == ('ACCEPTED' if case == 'complete' else 'REJECTED')
    if case == 'partial':
        assert claim['reason'] == 'CRITERIA_NOT_MET'
    print({'case':case,'run':run,'score':claim['score'],'status':claim['status'],'diff_sha256':claim['diff_sha256']})
