"""T-N：独立重跑验证者；不以格式检查代替证据判断。"""
import hashlib
import importlib
import pytest
from tests.helpers import pr, verdict, web, DIFF_URL, DIFF

@pytest.mark.parametrize('leader_met,leader_score,mine_met,mine_score,agree',[
    ((True,True),9,(True,True),9,True),
    ((True,True),9,(True,True),8,True),
    ((True,True),9,(True,True),7,True),
    ((True,True),7,(True,True),6,False),
    ((True,True),9,(True,True),6,False),
    ((True,True),9,(True,False),9,False),
    ((False,False),5,(False,True),5,True),
    ((False,True),5,(True,False),5,False),
    ((False,False),3,(False,False),6,False),
])
def test_decision_tolerances(ready,direct_vm,replay_validator,leader_met,leader_score,mine_met,mine_score,agree):
    pr(direct_vm)
    verdict(direct_vm,leader_met,leader_score)
    ready.submit_claim(0,34)
    direct_vm.clear_mocks()
    web(direct_vm,DIFF_URL,DIFF)
    verdict(direct_vm,mine_met,mine_score)
    assert replay_validator() is agree

def test_changed_diff(ready,direct_vm,replay_validator):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.clear_mocks()
    web(direct_vm,DIFF_URL,DIFF+'changed')
    assert replay_validator() is False

@pytest.mark.parametrize('leader_error,status,agree',[
    ('[TRANSIENT] GITHUB_HTTP_503',503,True),
    ('[LLM_ERROR] BAD_SCHEMA',None,False),
    ('[TRANSIENT] GITHUB_HTTP_503',200,False),
    ('[EXTERNAL] DIFF_NOT_FOUND',404,True),
    ('unknown',None,False),
])
def test_error_votes(ready,direct_vm,replay_validator,leader_error,status,agree):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.clear_mocks()
    if status is not None:
        web(direct_vm,DIFF_URL,DIFF,status)
        if status == 200:
            verdict(direct_vm)
    assert replay_validator(leader_error=Exception(leader_error)) is agree

def test_malformed_leader(ready,direct_vm,replay_validator):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.clear_mocks()
    assert replay_validator(leader_result={'criteria_met':[True]}) is False

def test_forged_accept(ready,direct_vm,replay_validator):
    pr(direct_vm)
    verdict(direct_vm,(False,False),4)
    ready.submit_claim(0,34)
    forged={'criteria_met':[True,True],'score':10,'summary':'forged','diff_sha256':hashlib.sha256(DIFF.encode()).hexdigest()}
    assert replay_validator(leader_result=forged) is False

def test_strict_facts_disagree(ready,direct_vm,replay_validator):
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    direct_vm.clear_mocks()
    pr(direct_vm,merged=False)
    assert replay_validator(index=-2) is False

def test_validator_vm_error_cannot_approve(ready,direct_vm,replay_validator,monkeypatch):
    # 负向控制仅证明回调拒绝异常；真实 GenVM 错误转换/隔离仍须 I-4 验证。
    pr(direct_vm)
    verdict(direct_vm)
    ready.submit_claim(0,34)
    module=importlib.import_module('_contract_issue_bounty_escrow')
    def fail(url):
        raise RuntimeError('simulated validator VM failure')
    monkeypatch.setattr(module,'_diff',fail)
    assert replay_validator() is False
