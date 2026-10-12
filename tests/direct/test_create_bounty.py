"""T-C：创建输入边界、快照和附带金额。"""
import pytest
from tests.helpers import create, web, ISSUE_URL, REPO, NOW

@pytest.mark.parametrize('value', [0,123])
def test_create(escrow, direct_vm, value):
    assert create(direct_vm,escrow,value=value) == 0
    b = escrow.get_bounty(0)
    assert b['reward'] == value and b['status'] == 'OPEN'
    assert escrow.get_accounting()['total_escrowed'] == value
    assert escrow.get_bounties(0,1) == [b]

@pytest.mark.parametrize('field,value,code', [
    ('criteria',[],'INVALID_CRITERIA'),('criteria',['x']*6,'INVALID_CRITERIA'),
    ('criteria',[' x','x '],'INVALID_CRITERIA'),('criteria',['x'*201],'INVALID_CRITERIA'),
    ('deadline',NOW+3599,'INVALID_DEADLINE'),('deadline',NOW+180*86400+1,'INVALID_DEADLINE'),
    ('min_score',0,'INVALID_MIN_SCORE'),('min_score',11,'INVALID_MIN_SCORE'),
    ('repo','bad/../../x','INVALID_REPO'),('issue_number',0,'INVALID_ISSUE_NUMBER'),
    ('repo','owner/.','INVALID_REPO'),('repo','owner/..','INVALID_REPO'),
    ('repo','owner/project.GIT','INVALID_REPO'),
    ('issue_number',2**64,'INVALID_ISSUE_NUMBER')])
def test_invalid_inputs(escrow, direct_vm, field, value, code):
    args = dict(repo=REPO,issue_number=12,criteria=['x'],deadline=NOW+7200,min_score=7)
    args[field] = value
    with direct_vm.expect_revert(code):
        escrow.create_bounty(**args)

@pytest.mark.parametrize('issue,status,code', [({'state':'closed'},200,'ISSUE_NOT_OPEN'),({'state':'open','pull_request':{}},200,'ISSUE_IS_PULL_REQUEST'),({},404,'ISSUE_NOT_FOUND')])
def test_issue_gate(escrow, direct_vm, issue, status, code):
    web(direct_vm,ISSUE_URL,issue,status)
    with direct_vm.expect_revert(code):
        escrow.create_bounty(REPO,12,['x'],NOW+7200,7)

def test_snapshot(escrow,direct_vm):
    web(direct_vm,ISSUE_URL,{'state':'open','title':'x'*250,'body':' \r\n'+'y'*2500+' '})
    escrow.create_bounty('Owner/PROJECT',12,[' x '],NOW+3600,1)
    b=escrow.get_bounty(0)
    assert len(b['issue_title']) == 200 and len(b['issue_snapshot']) == 2000
    assert b['criteria'] == ['x'] and b['repo'] == REPO


@pytest.mark.parametrize('trusted', [[0], [-1], [True], ['99'], [2**64], [99, 99], '99'])
def test_invalid_trusted_mergers(escrow, direct_vm, trusted):
    with direct_vm.expect_revert('INVALID_TRUSTED_MERGERS'):
        escrow.create_bounty(REPO, 12, ['x'], NOW+7200, 7, trusted)


@pytest.mark.parametrize('trusted', [None, [], [99, 100]])
def test_trusted_mergers_snapshot(escrow, direct_vm, trusted):
    create(direct_vm, escrow, trusted_merger_ids=trusted)
    assert escrow.get_bounty(0)['trusted_merger_ids'] == (trusted or [])
