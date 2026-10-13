"""公开 GitHub 样本的最小字段和完整 URL mock。"""
import json
import re
from pathlib import Path

FIXTURES=Path(__file__).resolve().parent/'fixtures'

def fixture(name):
    return json.loads((FIXTURES/name).read_text())

NOW = 1791763200
REPO = 'owner/project'
USER_URL = 'https://api.github.com/users/alice'
GISTS_URL = USER_URL + '/gists?per_page=100'
ISSUE_URL = f'https://api.github.com/repos/{REPO}/issues/12'
PR_URL = f'https://api.github.com/repos/{REPO}/pulls/34'
DIFF_URL = f'https://patch-diff.githubusercontent.com/raw/{REPO}/pull/34.diff'
MERGE_SHA = 'a' * 40
COMMIT_URL = f'https://api.github.com/repos/{REPO}/commits/{MERGE_SHA}'
EVENTS_URL = f'https://api.github.com/repos/{REPO}/issues/12/events?per_page=100&page=1'
DIFF = (FIXTURES/'pr_merged.diff').read_text()

def web(vm, url, obj, status=200):
    body = obj if isinstance(obj, str) else json.dumps(obj)
    pattern = '^'+re.escape(url)+'$'
    # 同一 URL 的覆盖必须替换旧 mock，否则 runner 仍匹配第一份响应。
    for i, (registered, _) in enumerate(vm._web_mocks):
        if registered.pattern == pattern:
            vm._web_mocks[i] = (registered, {'status': status, 'body': body})
            vm._web_mocks_hit.discard(i)
            return
    vm.mock_web(pattern, {'status': status, 'body': body})

def bind_marker(vm, c, github_id=42):
    from genlayer import Address
    contract = Address(vm._contract_address).as_hex.lower()
    return f'genlayer-bounty-bind:{contract}:{vm.sender.as_hex.lower()}:{c.get_bind_nonce(github_id)}'

def bind(vm, c, github_id=42, login='alice', proof=None, owner_id=None):
    url = f'https://api.github.com/users/{login.lower()}'
    web(vm, url, {**fixture('user_alice.json'),'id': github_id, 'login': login})
    web(vm, url+'/gists?per_page=100', [{'description': proof if proof is not None else bind_marker(vm,c,github_id),
                                    'owner': {'id': github_id if owner_id is None else owner_id}}])
    c.bind_github(login)

def create(vm, c, value=0, **changes):
    vm.value = value
    web(vm, ISSUE_URL, fixture('issue_open.json'))
    args = {'repo': REPO, 'issue_number': 12, 'criteria': ['Implement addition', 'Document addition'], 'deadline': NOW+7200, 'min_score': 7}
    args.update(changes)
    try:
        result = c.create_bounty(**args)
        # direct runner 不处理原生存款；仅按输入 value 建立独立测试余额模型。
        vm.deal(vm._contract_address, vm._balances.get(vm._contract_address, 0) + value)
        return result
    finally:
        vm.value = 0

def pr(vm, commit_message='Add addition\n\nFixes #12', diff_text=DIFF, events=None, **changes):
    obj = fixture('pr_merged.json')
    obj.update(changes)
    web(vm, PR_URL, obj)
    if obj.get('merged'):
        sha = obj.get('merge_commit_sha', MERGE_SHA)
        web(vm, f'https://api.github.com/repos/{REPO}/commits/{sha}', {'sha': sha, 'commit': {'message': commit_message}})
        # Only register events for the fallback path; strict mocks require each URL be used.
        from importlib import import_module
        module = import_module('_contract_issue_bounty_escrow')
        if not any(module._references_issue(text, REPO, 12)
                   for text in (commit_message, obj.get('title') or '', obj.get('body') or '')):
            web(vm, EVENTS_URL, [] if events is None else events)
        if diff_text is not None:
            web(vm, DIFF_URL, diff_text)

def verdict(vm, met=(True, True), score=9, summary='Implemented'):
    vm.mock_llm('BOUNTY_JUDGE_V2', json.dumps({'criteria': [{'id': i+1, 'met': m} for i,m in enumerate(met)], 'score': score, 'summary': summary}))
