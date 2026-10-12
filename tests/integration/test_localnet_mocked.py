"""I-1 至 I-4：真实 Studio RPC、五个 mock 验证者和支付状态。"""
import json
import pytest
from gltest import get_contract_factory, get_validator_factory, get_default_account
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from tests.helpers import NOW, REPO, USER_URL, GISTS_URL, ISSUE_URL, PR_URL, DIFF_URL, DIFF

pytestmark = pytest.mark.integration

def succeeded(receipt):
    # 同时检查状态和执行结果，不能只看 ACCEPTED。
    assert str(receipt.get('status','')).upper() in ('ACCEPTED','FINALIZED')
    leaders=receipt.get('consensus_data',{}).get('leader_receipt',[])
    results=[r.get('execution_result') for r in leaders]
    assert 'FINISHED_WITH_RETURN' in results or tx_execution_succeeded(receipt)

def context(account, merged=True, met=(True,True), count=5):
    data={USER_URL:{'id':42,'login':'alice'},
          GISTS_URL:[{'description':'genlayer-bounty-bind:'+account.address.lower()}],
          ISSUE_URL:{'state':'open','title':'Addition','body':'Implement and document addition.'},
          PR_URL:{'merged':merged,'merged_at':'2026-10-12T01:00:00Z','user':{'id':42},
                  'base':{'repo':{'full_name':REPO}},'title':'Add','body':'Fixes #12'},
          DIFF_URL:DIFF}
    web={u:{'method':'GET','response':{'status':200,'headers':{},'body':v if isinstance(v,str) else json.dumps(v)}} for u,v in data.items()}
    answer={'criteria':[{'id':i+1,'met':m} for i,m in enumerate(met)],'score':9,'summary':'Mock judge'}
    validators=get_validator_factory().batch_create_mock_validators(count=count,
        mock_llm_response={'nondet_exec_prompt':{'BOUNTY_JUDGE_V1':answer}},
        mock_web_response={'nondet_web_request':web})
    return {'validators':[v.to_dict() for v in validators],'genvm_datetime':'2026-10-12T00:00:00Z'}

def deploy(ctx):
    return get_contract_factory(contract_file_path='contracts/issue_bounty_escrow.py').deploy(args=[259200,3],transaction_context=ctx)

def setup_bounty(c,ctx):
    succeeded(c.bind_github('alice').transact(transaction_context=ctx))
    succeeded(c.create_bounty(REPO,12,['Implement addition','Document addition'],NOW+7200,7).transact(value=123,transaction_context=ctx))

def test_I1_payment_flow():
    ctx=context(get_default_account())
    c=deploy(ctx)
    setup_bounty(c,ctx)
    succeeded(c.submit_claim(0,34).transact(transaction_context=ctx))
    assert c.get_bounty(0).call()['status'] == 'AWARDED'
    assert c.get_credit(get_default_account().address).call() == 123
    succeeded(c.withdraw().transact(transaction_context=ctx,wait_transaction_status=TransactionStatus.FINALIZED))
    a=c.get_accounting().call()
    assert a['total_credits'] == 0 and a['total_withdrawn'] == 123
    assert a['total_escrowed']+a['total_credits']+a['total_withdrawn'] == 123

def test_I2_unmerged():
    ctx=context(get_default_account(),merged=False)
    c=deploy(ctx)
    setup_bounty(c,ctx)
    succeeded(c.submit_claim(0,34).transact(transaction_context=ctx))
    assert c.get_claim(0).call()['reason'] == 'NOT_MERGED'
    assert c.get_bounty(0).call()['status'] == 'OPEN'

def test_I3_refund():
    ctx=context(get_default_account())
    c=deploy(ctx)
    setup_bounty(c,ctx)
    ctx['genvm_datetime']='2026-10-15T02:00:01Z'
    succeeded(c.refund(0).transact(transaction_context=ctx))
    assert c.get_bounty(0).call()['status'] == 'REFUNDED'
    assert c.get_credit(get_default_account().address).call() == 123

def test_I4_consensus_split():
    # 三对三；必须观察真实未成功的回执，超时不能当作验证成功。
    account=get_default_account()
    ctx=context(account)
    c=deploy(ctx)
    setup_bounty(c,ctx)
    yes=context(account,met=(True,True),count=3)
    no=context(account,met=(False,False),count=3)
    split={**yes,'validators':yes['validators']+no['validators']}
    receipt=c.submit_claim(0,34).transact(transaction_context=split,consensus_max_rotations=0)
    assert str(receipt.get('status','')).upper() not in ('ACCEPTED','FINALIZED')
    assert c.get_bounty(0).call()['status'] == 'OPEN'
